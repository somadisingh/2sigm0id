"""Pilot users: a labeled pool of spoken answers for grounding and checking method D.

The 10 pilot users (mirofish/personas_pilot.json) are never scored in the experiment. Each one
answers every belief-engine question in its spoken wording, with no injected noise. Labels
come from the pilot user's TRUE profile, never from an LLM:
  fact questions          the true fact value, and the option that contains it
  willingness / behavior  the true dimension score, and the option nearest to it

  python pilot.py build         ask the questions (simulated-user calls only, about $0.05)
  python pilot.py calibrate     DP: GLM's option probabilities for each answer; fits the
                                temperature on the fact answers, where the right option is
                                known exactly (about $0.15)
  python pilot.py extract-eval  D vs DR vs DP on the same labeled answers (about $0.60)

Outputs in pilot/: pool.jsonl, calibration.json, option_probs.jsonl, extract_eval.md.
"""

import argparse
import json
import math
import time
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

    def one(r):
        item = items[r["item"]]
        out = {"r": r}
        for name, ex in (("D", ""), ("DR", retrieval.examples_block(
                pool.similar(item, r["question"], r["answer"], exclude_persona=r["persona_id"])))):
            ev, calls = M.extract(llm, iv, C.EXPERIMENT_INTERVIEWER_REASONING, r["question"], item,
                                  r["answer"], ex)
            out[name] = (ev, calls)
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

    rows = {k: summary(k) for k in ("D", "DR", "DP")}
    cols = list(rows["D"])
    raw = [{"persona_id": o["r"]["persona_id"], "item": o["r"]["item"], "question": o["r"]["question"],
            "answer": o["r"]["answer"], "dimension": o["r"]["dimension"], "topic": o["r"]["topic"],
            "gold": o["r"]["gold"], "gold_option": o["r"]["gold_option"],
            "D": o["D"][0], "DR": o["DR"][0], "DP": o["DP"][0]} for o in res]
    if not args.mock:
        (HERE / "results").mkdir(exist_ok=True)
        (HERE / "results" / "pilot_extract_eval.jsonl").write_text("".join(json.dumps(r) + "\n" for r in raw))
    lines = [f"# Extraction check on the pilot pool ({len(res)} labeled answers, {time.strftime('%Y-%m-%d')})", "",
             "| reader | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for k, v in rows.items():
        lines.append(f"| {k} | " + " | ".join(fmt(c, v[c]) for c in cols) + " |")
    lines += ["", "fact right: share of fact answers read as a range (D, DR) or top option (DP) that "
              "contains the true value. Errors: mean absolute difference from the true score. "
              "DP's score is the expected option score. Labels come from the true profiles, so a "
              "pilot user who answered off-profile counts against every reader equally."]
    lines += ["", "Paired differences against D (negative = lower error than D), with 95% bootstrap ranges:", ""]
    for name in ("DR", "DP"):
        for dim in ("willingness", "behavioral"):
            d = [score_error(r, name) - score_error(r, "D") for r in raw
                 if r["dimension"] == dim and score_error(r, name) is not None and score_error(r, "D") is not None]
            lo, hi = paired_range(d)
            lines.append(f"- {name} {dim}: {sum(d) / len(d):+.3f} ({lo:+.3f} to {hi:+.3f}), {len(d)} answers")
    text = "\n".join(lines) + "\n"
    if not args.mock:
        (OUT / "extract_eval.md").write_text(text)
    print(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("build", build), ("calibrate", calibrate), ("extract-eval", extract_eval)):
        sp = sub.add_parser(name)
        sp.add_argument("--mock", action="store_true")
        sp.set_defaults(fn=fn)
    args = ap.parse_args()
    R.load_env()
    args.fn(args)


if __name__ == "__main__":
    main()
