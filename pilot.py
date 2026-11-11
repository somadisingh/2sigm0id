"""Pilot users: a labeled pool of spoken answers for grounding and checking method D.

The 10 pilot users (mirofish/personas_pilot.json) are never scored in the experiment. Each one
answers every belief-engine question in its spoken wording, with no injected noise. Labels
come from the pilot user's TRUE profile, never from an LLM:
  fact questions          the true fact value, and the option that contains it
  willingness / behavior  the true dimension score, and the option nearest to it

  python pilot.py build         ask the questions (simulated-user calls only, about $0.05)
  python pilot.py forms         the same questions as a form, with form noise (about $0.04)
  python pilot.py calibrate     DP: GLM's option probabilities for each answer; fits the
                                temperature on the fact answers, where the right option is
                                known exactly (about $0.15)
  python pilot.py extract-eval  D vs DR vs DP on the same labeled answers (about $0.60)
  python pilot.py fit           fits the engine's evidence settings (pilot/fitted.json) and
                                chooses the fixed-form questions (pilot/short_forms.json);
                                checks both by leaving one pilot user out (no API calls)

Outputs in pilot/: pool.jsonl, calibration.json, option_probs.jsonl, extract_eval.md.
"""

import argparse
import json
import math
import random
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import belief as BE
import config as C
import methods as M
import prompts as P
import retrieval
import run_bakeoff as R
from capacity import INCOME_SCORE
from llm import strip_think

HERE = Path(__file__).resolve().parent
OUT = HERE / "pilot"
PILOTS = HERE / "mirofish" / "personas_pilot.json"
ITEMS = {i["id"]: i for i in M.load_bank()["items"]}


def gold_for(p, item):
    """The correct reading of a pilot user's answer, from their true profile."""
    truth = p["ground_truth"]
    if item["dimension"] == "capacity":
        v = p["finances"][item["fact"]]
        if item["fact"] == "income_stability":
            s = INCOME_SCORE[v]
            opt = next(n for n, o in enumerate(item["options"]) if abs(o["score"] - s) < 0.01)
        else:
            opt = next(n for n, o in enumerate(item["options"])
                       if o["range"][0] <= v < (o["range"][1] if o["range"][1] is not None else math.inf))
        return {"value": v}, opt
    score = truth[item["dimension"]]
    kind = BE.evidence_kind(item)
    if item["id"] == "BEH02" and p["experience"]["past_loss_reaction"] == "none":
        opt = next(n for n, o in enumerate(item["options"]) if o["score"] is None)
    else:
        opt = min((n for n, o in enumerate(item["options"]) if o["score"] is not None),
                  key=lambda n: abs(item["options"][n]["score"] - score))
    return {"score": score, "kind": "past" if kind == "past" else "hypothetical"}, opt


def build(args):
    llm = R.make_llm(args.mock)
    pilots = json.loads(PILOTS.read_text())
    pool = M.engine_pool(M.load_bank())

    def one(p):
        msgs = [{"role": "system", "content": P.build_user_system(p)}]
        rows = []
        for item in pool:
            msgs.append({"role": "user", "content": item["spoken"]})
            r = llm.chat(C.EXPERIMENT_USER, msgs, C.EXPERIMENT_USER_REASONING, C.USER_MAX_TOKENS,
                         C.USER_TEMPERATURE)
            a = strip_think(r["text"]) or "(no answer)"
            msgs.append({"role": "assistant", "content": a})
            gold, opt = gold_for(p, item)
            rows.append({"persona_id": p["id"], "item": item["id"], "dimension": item["dimension"],
                         "topic": retrieval.topic(item), "question": item["spoken"], "answer": a,
                         "gold": gold, "gold_option": opt, "usage": r["usage"]})
        print(f"{p['id']}: {len(rows)} answers")
        return rows

    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        rows = [r for rs in ex.map(one, pilots) for r in rs]
    OUT.mkdir(exist_ok=True)
    path = OUT / ("pool_mock.jsonl" if args.mock else "pool.jsonl")
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"Saved {len(rows)} labeled answers to {path.relative_to(HERE)}")


def forms(args):
    """Each pilot user answers every engine question as a form (an option number), with the
    same form noise as the experiment (vague and flipped answers). Needed to fit the
    engine's form settings and to choose the fixed-form questions."""
    llm = R.make_llm(args.mock)
    pilots = json.loads(PILOTS.read_text())
    pool = M.engine_pool(M.load_bank())

    def one(p):
        rng = random.Random(zlib.crc32(f"{p['id']}|forms".encode()))
        msgs = [{"role": "system", "content": P.build_user_system(p)}]
        rows = []
        for k, item in enumerate(pool):
            noise = [x for x in R.draw_noise(rng, p, k) if x in M.FORM_NOISE]
            q = M.FORM_PROMPT.format(question=item["text"], options=M.numbered(item))
            note = ("\n\n[Private note: " + " ".join(M.FORM_NOISE[x] for x in noise) + "]") if noise else ""
            msgs.append({"role": "user", "content": q + note})
            r = llm.chat(C.EXPERIMENT_USER, msgs, C.EXPERIMENT_USER_REASONING, C.USER_MAX_TOKENS,
                         C.USER_TEMPERATURE)
            msgs[-1]["content"] = q
            msgs.append({"role": "assistant", "content": strip_think(r["text"]) or "(no answer)"})
            choice = M.pick_option(r["text"], len(item["options"]))
            if choice is None:
                msgs.append({"role": "user", "content": M.FORM_RETRY.format(n=len(item["options"]))})
                r = llm.chat(C.EXPERIMENT_USER, msgs, C.EXPERIMENT_USER_REASONING, C.USER_MAX_TOKENS,
                             C.USER_TEMPERATURE)
                msgs.append({"role": "assistant", "content": strip_think(r["text"]) or "(no answer)"})
                choice = M.pick_option(r["text"], len(item["options"]))
            rows.append({"persona_id": p["id"], "item": item["id"], "dimension": item["dimension"],
                         "choice": choice, "noise": noise})
        return rows

    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        rows = [r for rs in ex.map(one, pilots) for r in rs]
    OUT.mkdir(exist_ok=True)
    path = OUT / ("form_answers_mock.jsonl" if args.mock else "form_answers.jsonl")
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"Saved {len(rows)} form answers ({sum(r['choice'] is None for r in rows)} unanswered) "
          f"to {path.relative_to(HERE)}")


def metrics(rows, t):
    """NLL, accuracy, Brier and ECE of the gold option under temperature t."""
    nll = acc = brier = 0.0
    bins = [[0, 0.0, 0.0] for _ in range(10)]   # count, sum confidence, sum correct
    for r in rows:
        q = M.sharpen(r["q"], t)
        g = r["gold_option"]
        nll -= math.log(max(q[g], 1e-12))
        top = max(range(len(q)), key=q.__getitem__)
        acc += top == g
        brier += sum((x - (i == g)) ** 2 for i, x in enumerate(q))
        b = bins[min(9, int(q[top] * 10))]
        b[0] += 1
        b[1] += q[top]
        b[2] += top == g
    n = len(rows)
    ece = sum(abs(s - c) for _, s, c in bins) / n
    return {"nll": round(nll / n, 3), "accuracy": round(acc / n, 3),
            "brier": round(brier / n, 3), "ece": round(ece, 3), "n": n}


def read_all(llm, rows, bank_items, t=1.0):
    def one(r):
        item = bank_items[r["item"]]
        q, calls = M.read_options(llm, C.EXPERIMENT_INTERVIEWER, "off", r["question"], item, r["answer"], t=t)
        return {**r, "q": q, "calls": calls}
    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        return list(ex.map(one, rows))


def calibrate(args):
    llm = R.make_llm(args.mock)
    pool = retrieval.Pool.load(OUT / ("pool_mock.jsonl" if args.mock else "pool.jsonl"))
    items = {i["id"]: i for i in M.load_bank()["items"]}
    read = read_all(llm, pool.entries, items)
    ok = [r for r in read if r["q"]]
    (OUT / ("option_probs_mock.jsonl" if args.mock else "option_probs.jsonl")).write_text("".join(
        json.dumps({k: r[k] for k in ("persona_id", "item", "gold_option", "q")}) + "\n" for r in ok))
    facts = [r for r in ok if r["dimension"] == "capacity"]
    grid = [round(0.25 * k, 2) for k in range(2, 81)]   # 0.5 to 20
    best = min(grid, key=lambda t: metrics(facts, t)["nll"])
    out = {"model": C.EXPERIMENT_INTERVIEWER, "temperature": best, "fitted_on": "fact answers",
           "readable": f"{len(ok)} of {len(read)}",
           "facts_before": metrics(facts, 1.0), "facts_after": metrics(facts, best),
           "all_before": metrics(ok, 1.0), "all_after": metrics(ok, best),
           "date": time.strftime("%Y-%m-%d")}
    if not args.mock:
        M.CALIBRATION_PATH.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


def fact_hit(rng, gold, fact):
    if rng is None:
        return None
    v = INCOME_SCORE[gold["value"]] if fact == "income_stability" else gold["value"]
    lo, hi = rng
    tol = 0.01 if fact == "income_stability" else 1e-9
    return lo - tol <= v <= hi + tol


def score_error(r, name):
    """Absolute error of a reader's willingness or behavior score on one labeled answer."""
    ev = r[name]
    if ev is None:
        return None
    if name == "DP":
        item = ITEMS[r["item"]]
        sc = [n for n, o in enumerate(item["options"]) if o["score"] is not None]
        if sum(ev[n] for n in sc) < 0.5:   # mostly "never happened": no score
            return None
        exp = sum(ev[n] * item["options"][n]["score"] for n in sc) / sum(ev[n] for n in sc)
        return abs(exp - r["gold"]["score"])
    got = ev.get(r["dimension"])
    return None if got is None else abs(got["score"] - r["gold"]["score"])


def paired_range(d, n=2000, seed=0):
    import random
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(d, k=len(d))) / len(d) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def extract_eval(args):
    """D (extractor), DR (extractor + retrieved examples) and DP (option probabilities) on the
    same labeled pilot answers. DR never sees examples from the same pilot user."""
    llm = R.make_llm(args.mock)
    pool = retrieval.Pool.load(OUT / ("pool_mock.jsonl" if args.mock else "pool.jsonl"))
    items = {i["id"]: i for i in M.load_bank()["items"]}
    iv = C.EXPERIMENT_INTERVIEWER

    readers = args.readers

    def one(r):
        item = items[r["item"]]
        out = {"r": r, "D": (dict(M.NO_EVIDENCE), []), "DR": (dict(M.NO_EVIDENCE), []), "DP": (None, [])}
        for name, ex in (("D", ""), ("DR", None)):
            if name not in readers:
                continue
            if ex is None:
                ex = retrieval.examples_block(
                    pool.similar(item, r["question"], r["answer"], exclude_persona=r["persona_id"]))
            ev, calls = M.extract(llm, iv, C.EXPERIMENT_INTERVIEWER_REASONING, r["question"], item,
                                  r["answer"], ex)
            out[name] = (ev, calls)
        if "DP" in readers:
            out["DP"] = M.read_options(llm, iv, "off", r["question"], item, r["answer"])
        return out

    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        res = list(ex.map(one, pool.entries))

    def summary(name):
        fact_hits, fact_missing, errs, missing, kinds, cost, calls = [], 0, {"willingness": [], "behavioral": []}, \
            {"willingness": 0, "behavioral": 0}, [], 0.0, 0
        for o in res:
            r, item = o["r"], items[o["r"]["item"]]
            ev, cs = o[name]
            cost += sum(cost_of(c) for c in cs)
            calls += len(cs)
            if name == "DP":
                q = ev
                if r["dimension"] == "capacity":
                    if q is None:
                        fact_missing += 1
                    else:
                        fact_hits.append(max(range(len(q)), key=q.__getitem__) == r["gold_option"])
                elif q is not None and r["gold_option"] is not None and item["options"][r["gold_option"]]["score"] is not None:
                    sc = [n for n, opt in enumerate(item["options"]) if opt["score"] is not None]
                    exp = sum(q[n] * item["options"][n]["score"] for n in sc) / sum(q[n] for n in sc)
                    errs[r["dimension"]].append(abs(exp - r["gold"]["score"]))
                elif r["dimension"] != "capacity":
                    missing[r["dimension"]] += 1
                continue
            if r["dimension"] == "capacity":
                got = ev["facts"].get(r["topic"])
                if got is None:
                    fact_missing += 1
                else:
                    fact_hits.append(fact_hit(got["range"], r["gold"], r["topic"]))
            else:
                got = ev[r["dimension"]]
                if got is None:
                    missing[r["dimension"]] += 1
                else:
                    errs[r["dimension"]].append(abs(got["score"] - r["gold"]["score"]))
                    if r["dimension"] == "behavioral":
                        kinds.append(got["kind"] == r["gold"]["kind"])
        mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
        n = len(res)
        return {"fact right": mean(fact_hits), "fact missing": fact_missing,
                "willingness error": mean(errs["willingness"]), "willingness missing": missing["willingness"],
                "behavior error": mean(errs["behavioral"]), "behavior missing": missing["behavioral"],
                "past/imagined right": mean(kinds), "calls": calls / n, "$ per answer": cost / n}

    def cost_of(c):
        m = C.MODELS[c.get("model") or iv]
        return (c["usage"]["in"] * m["price_in"] + c["usage"]["out"] * m["price_out"]) / 1e6

    def fmt(col, v):
        if v is None:
            return "-"
        if col == "$ per answer":
            return f"${v:.5f}"
        return f"{v:.3f}" if isinstance(v, float) else str(v)

    rows = {k: summary(k) for k in ("D", "DR", "DP") if k in readers}
    cols = list(rows["D"])
    raw = [{"persona_id": o["r"]["persona_id"], "item": o["r"]["item"], "question": o["r"]["question"],
            "answer": o["r"]["answer"], "dimension": o["r"]["dimension"], "topic": o["r"]["topic"],
            "gold": o["r"]["gold"], "gold_option": o["r"]["gold_option"],
            "D": o["D"][0], "DR": o["DR"][0], "DP": o["DP"][0]} for o in res]
    if not args.mock and set(readers) == {"D", "DR", "DP"}:
        (HERE / "results").mkdir(exist_ok=True)
        (HERE / "results" / "pilot_extract_eval.jsonl").write_text("".join(json.dumps(r) + "\n" for r in raw))
    if args.save and not args.mock:
        (HERE / "results" / args.save).write_text("".join(json.dumps(r) + "\n" for r in raw))
    lines = [f"# Extraction check on the pilot pool ({len(res)} labeled answers, {time.strftime('%Y-%m-%d')})", "",
             "| reader | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for k, v in rows.items():
        lines.append(f"| {k} | " + " | ".join(fmt(c, v[c]) for c in cols) + " |")
    lines += ["", "fact right: share of fact answers read as a range (D, DR) or top option (DP) that "
              "contains the true value. Errors: mean absolute difference from the true score. "
              "DP's score is the expected option score. Labels come from the true profiles, so a "
              "pilot user who answered off-profile counts against every reader equally."]
    lines += ["", "Paired differences against D (negative = lower error than D), with 95% bootstrap ranges:", ""]
    for name in [x for x in ("DR", "DP") if x in readers and "D" in readers]:
        for dim in ("willingness", "behavioral"):
            d = [score_error(r, name) - score_error(r, "D") for r in raw
                 if r["dimension"] == dim and score_error(r, name) is not None and score_error(r, "D") is not None]
            lo, hi = paired_range(d)
            lines.append(f"- {name} {dim}: {sum(d) / len(d):+.3f} ({lo:+.3f} to {hi:+.3f}), {len(d)} answers")
    text = "\n".join(lines) + "\n"
    if not args.mock and set(readers) == {"D", "DR", "DP"}:
        (OUT / "extract_eval.md").write_text(text)
    print(text)


SIGMA_GRID = [round(0.05 + 0.025 * k, 3) for k in range(23)]   # 0.05 to 0.60
LAPSE_GRID = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3]
SHORT_FORMS_PATH = OUT / "short_forms.json"


def form_loglik(rows, pilots, sigma, lapse, kind=None):
    """Log-likelihood of the pilot users' form answers under the engine's form model."""
    ll = 0.0
    for r in rows:
        item, p = ITEMS[r["item"]], pilots[r["persona_id"]]
        opt = item["options"][r["choice"] - 1] if r["choice"] else None
        if opt is None or opt["score"] is None and item["dimension"] != "capacity":
            continue
        n = len(BE.scored_options(item))
        if item["dimension"] == "capacity":
            if kind is not None:
                continue
            _, gold = gold_for(p, item)
            hit = item["options"][gold] is opt
            ll += math.log((1 - lapse) * hit + lapse / n)
            continue
        k = BE.evidence_kind(item)
        if kind is not None and k != kind:
            continue
        theta = p["ground_truth"][item["dimension"]]
        sc = [o["score"] for o in BE.scored_options(item)]
        g = [math.exp(-(x - theta) ** 2 / (2 * sigma[k] ** 2)) for x in sc]
        ll += math.log((1 - lapse) * g[sc.index(opt["score"])] / sum(g) + lapse / n)
    return ll


def fit_form(rows, pilots):
    best = None
    for lapse in LAPSE_GRID:
        sigma = {k: max(SIGMA_GRID, key=lambda s: form_loglik(rows, pilots, {k: s}, lapse, k))
                 for k in ("stated", "hypothetical", "past")}
        ll = form_loglik(rows, pilots, sigma, lapse)
        if best is None or ll > best[0]:
            best = (ll, sigma, lapse)
    return {"sigma": best[1], "lapse": best[2]}, best[0]


def fit_spoken(readings):
    """Extracted scores vs true scores: a normal spread plus a share of stray readings
    (uniform on 0-1). One shared stray share; one spread per kind of evidence."""
    def ll(kind, sg, lp):
        return sum(math.log((1 - lp) * math.exp(-(s - t) ** 2 / (2 * sg ** 2)) / (sg * math.sqrt(2 * math.pi)) + lp)
                   for k, s, t in readings if k == kind)
    kinds = sorted({k for k, _, _ in readings})
    lapse = max(LAPSE_GRID, key=lambda lp: sum(max(ll(k, sg, lp) for sg in SIGMA_GRID) for k in kinds))
    return {"spoken_sigma": {k: max(SIGMA_GRID, key=lambda sg: ll(k, sg, lapse)) for k in kinds},
            "spoken_lapse": lapse}


def dim_estimate(answers, dim):
    b = BE.Belief()
    for item, choice in answers:
        b.observe_option(item, choice)
    return b.profile()[dim]


def pick_short_forms(rows, pilots, ids):
    """Greedy, per dimension, within the contract's split: add the question that most lowers
    the error of that dimension's estimate on the training pilot users."""
    ans = {(r["persona_id"], r["item"]): r["choice"] for r in rows}
    alloc = M.load_bank()["short_form_allocation"]
    pool = M.engine_pool(M.load_bank())
    order = {}
    for dim in BE.DIMS:
        need = max(alloc[b][dim] for b in alloc)
        chosen = []
        while len(chosen) < need:
            def err(it):
                return sum(abs(dim_estimate([(ITEMS[i], ans[(pid, i)]) for i in chosen + [it["id"]]], dim)
                               - pilots[pid]["ground_truth"][dim]) for pid in ids)
            chosen.append(min((it for it in pool if it["dimension"] == dim and it["id"] not in chosen),
                              key=err)["id"])
        order[dim] = chosen
    return {b: [i for d in BE.DIMS for i in order[d][:alloc[b][d]]] for b in alloc}


def replay(pid, rows, pilots, budget, form_ids=None, spoken=None):
    """Score one pilot user offline, with no API calls. Forms use the recorded form answers:
    a fixed form (A) when form_ids is given, else the engine choosing (C). With spoken (the
    extractor's recorded readings of each spoken answer), the engine chooses and reads them
    (D without clarifying questions)."""
    ans = {r["item"]: r["choice"] for r in rows if r["persona_id"] == pid}
    pool = M.engine_pool(M.load_bank())
    b, settled = BE.Belief(), False
    for k in range(budget):
        if form_ids:
            item = ITEMS[form_ids[k]]
        else:
            item, info = b.choose([i for i in pool if i["id"] in ans and i["id"] not in b.asked],
                                  budget - k, settled, seed=k)
            settled = info["settled"]
        b.asked.add(item["id"])
        if spoken is not None:
            M.apply_evidence(b, spoken[(pid, item["id"])], k)
        else:
            b.observe_option(item, ans[item["id"]])
    est, truth = b.profile(), pilots[pid]["ground_truth"]
    err = sum(abs(est[d] - truth[d]) for d in BE.DIMS) / 3
    exact = min(BE.band(est[d]) for d in BE.DIMS) == truth["final_band"]
    return err, exact


def spoken_data(path, pilots, ids):
    """The extractor's (D) readings on the pilot pool: score readings and fact hits for
    fitting, and every reading by (pilot, item) for replay."""
    readings, fact_hits, by_key = [], [], {}
    for r in (json.loads(x) for x in path.read_text().splitlines()):
        ev = r["D"]
        by_key[(r["persona_id"], r["item"])] = ev
        if r["persona_id"] not in ids:
            continue
        truth = pilots[r["persona_id"]]["ground_truth"]
        if r["dimension"] == "capacity":
            got = ev["facts"].get(r["topic"])
            if got and got["clear"]:
                fact_hits.append(fact_hit(got["range"], r["gold"], r["topic"]))
        elif ev.get(r["dimension"]) and ev[r["dimension"]]["clear"]:
            e = ev[r["dimension"]]
            kind = "stated" if r["dimension"] == "willingness" else e["kind"]
            readings.append((kind, e["score"], truth[r["dimension"]]))
    return readings, fact_hits, by_key


def fit_all(rows, pilots, raw_path, ids):
    """Form and spoken settings fitted on the pilot users in ids."""
    form, ll = fit_form([r for r in rows if r["persona_id"] in ids], pilots)
    readings, fact_hits, _ = spoken_data(raw_path, pilots, ids)
    return {**form, **fit_spoken(readings), "fact_miss": round(1 - sum(fact_hits) / len(fact_hits), 3)}, ll, readings


def fit(args):
    pilots = {p["id"]: p for p in json.loads(PILOTS.read_text())}
    rows = [json.loads(x) for x in (OUT / "form_answers.jsonl").read_text().splitlines()]
    raw_path = HERE / "results" / "pilot_extract_eval.jsonl"
    if not raw_path.exists():
        raise SystemExit("Run `python pilot.py extract-eval` first (it saves the extractor's readings).")
    start = BE.STARTING
    default_forms = {b: [i["id"] for i in M.short_form(M.load_bank(), int(b), use_fitted=False)]
                     for b in ("5", "10", "15")}
    ids = sorted(pilots)
    _, _, spoken = spoken_data(raw_path, pilots, ids)

    # leave one pilot user out: fit and choose on 9, score the 10th
    budgets = (5, 10, 15)
    names = ("A, default form, starting settings", "A, default form, fitted settings",
             "A, chosen form, fitted settings", "C, starting settings", "C, fitted settings",
             "D, starting settings", "D, fitted settings")
    res = {n: {b: [] for b in budgets} for n in names}
    for h in ids:
        train = [i for i in ids if i != h]
        BE.use(start, "starting guesses")
        for b in budgets:
            res[names[0]][b].append(replay(h, rows, pilots, b, default_forms[str(b)]))
            res[names[3]][b].append(replay(h, rows, pilots, b))
            res[names[5]][b].append(replay(h, rows, pilots, b, spoken=spoken))
        fitted, _, _ = fit_all(rows, pilots, raw_path, train)
        BE.use(fitted, "fitted, leave one out")
        forms_h = pick_short_forms([r for r in rows if r["persona_id"] in train], pilots, train)
        for b in budgets:
            res[names[1]][b].append(replay(h, rows, pilots, b, default_forms[str(b)]))
            res[names[2]][b].append(replay(h, rows, pilots, b, forms_h[str(b)]))
            res[names[4]][b].append(replay(h, rows, pilots, b))
            res[names[6]][b].append(replay(h, rows, pilots, b, spoken=spoken))
        print(f"left out {h}")

    mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
    err = {n: mean([e for b in budgets for e, _ in res[n][b]]) for n in names}
    # adopt a fitted part only if it lowered the error on the left-out users
    use_form = err[names[1]] + err[names[4]] <= err[names[0]] + err[names[3]]
    use_spoken = err[names[6]] <= err[names[5]]
    use_forms = err[names[2]] <= err[names[1]]

    BE.use(start, "starting guesses")
    ll_start = form_loglik(rows, pilots, start["sigma"], start["lapse"])
    final, ll_fit, readings = fit_all(rows, pilots, raw_path, ids)
    adopted = {}
    if use_form:
        adopted.update({k: final[k] for k in ("sigma", "lapse")})
    if use_spoken:
        adopted.update({k: final[k] for k in ("spoken_sigma", "spoken_lapse", "fact_miss")})
    adopted["fitted_on"] = (f"{len(pilots)} pilot users: {len(rows)} form answers, "
                            f"{len(readings)} spoken readings")
    adopted["date"] = time.strftime("%Y-%m-%d")
    BE.use(final, "fitted")
    forms_all = pick_short_forms(rows, pilots, ids)
    if not args.mock:
        BE.FITTED_PATH.write_text(json.dumps(adopted, indent=1) + "\n")
        if use_forms:
            SHORT_FORMS_PATH.write_text(json.dumps(forms_all, indent=1) + "\n")

    yes = lambda x: "adopted" if x else "not adopted"  # noqa: E731
    lines = [f"# Pilot fit ({time.strftime('%Y-%m-%d')})", "",
             "Fitted on the 10 pilot users only. The 100 test users were not used. A fitted part is "
             "adopted only if it lowered the error on pilot users it was not fitted on.", "",
             "## Evidence settings", "",
             f"| setting | starting guess | fitted |", "|---|---|---|"]
    for k in ("stated", "hypothetical", "past"):
        lines.append(f"| form spread, {k} | {start['sigma'][k]} | {final['sigma'][k]} |")
    lines.append(f"| form lapse | {start['lapse']} | {final['lapse']} |")
    for k in ("stated", "hypothetical", "past"):
        n = sum(1 for kind, _, _ in readings if kind == k)
        lines.append(f"| spoken spread, {k} ({n} readings) | {start['spoken_sigma'][k]} | "
                     f"{final['spoken_sigma'].get(k, '-')} |")
    lines.append(f"| spoken lapse | {start['spoken_lapse']} | {final['spoken_lapse']} |")
    lines.append(f"| spoken fact miss rate | {start['fact_miss']} | {final['fact_miss']} |")
    lines += ["", f"A smaller spread means stronger evidence. Form answers: log-likelihood {ll_start:.1f} with "
              f"the starting guesses, {ll_fit:.1f} fitted (higher is better).", "",
              f"- Form settings: **{yes(use_form)}**.",
              f"- Spoken settings: **{yes(use_spoken)}**.",
              f"- Chosen fixed-form questions: **{yes(use_forms)}**.", "",
              "## Leave-one-out check (fit on 9 pilot users, score the 10th, 10 times)", "",
              "| method | budget 5 | budget 10 | budget 15 | mean |", "|---|---|---|---|---|"]
    for n in names:
        cells = [f"{mean([e for e, _ in res[n][b]]):.3f} ({mean([x for _, x in res[n][b]]):.0%})" for b in budgets]
        lines.append(f"| {n} | " + " | ".join(cells) + f" | {err[n]:.3f} |")
    lines += ["", "Avg error over the three scores (band exact in brackets), from recorded answers, with "
              "no new API calls. D here reads the recorded spoken answers without clarifying questions. "
              "The pilot answers have no injected contradictions. 10 users: treat differences under "
              "about 0.02 as noise.", "",
              "## Fixed-form questions (A and B)", "", "| budget | default | chosen on the pilot users |",
              "|---|---|---|"]
    for b in ("5", "10", "15"):
        lines.append(f"| {b} | {', '.join(default_forms[b])} | {', '.join(forms_all[b])} |")
    text = "\n".join(lines) + "\n"
    if not args.mock:
        (OUT / "fit.md").write_text(text)
    print(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("build", build), ("forms", forms), ("calibrate", calibrate),
                     ("extract-eval", extract_eval), ("fit", fit)):
        sp = sub.add_parser(name)
        sp.add_argument("--mock", action="store_true")
        if name == "extract-eval":
            sp.add_argument("--readers", nargs="*", default=["D", "DR", "DP"], choices=["D", "DR", "DP"],
                            help="only these readers; the saved files are written only for all three")
            sp.add_argument("--save", help="also save the raw readings to this results file")
        sp.set_defaults(fn=fn)
    args = ap.parse_args()
    R.load_env()
    args.fn(args)


if __name__ == "__main__":
    main()
