"""Persona checks 2, 3 and 5 (plan.md, task S3). Siya's checks.

Every test user answers 8 new multiple-choice questions (4 willingness, 4 behavior), in a fresh
conversation with no noise. None of the 8 is in question_bank.json. Each option has a fixed
score (0.1, 0.3, 0.5, 0.7 or 0.9, one per band), so no AI reads the answers.

  Check 2, profile:  the average score for willingness and for behavior must land in the true
                     band or one band away. "Says aggressive, would panic-sell" users are also
                     reported apart: they must answer willingness boldly and behavior with fear.
  Check 3, repeat:   the same user (DeepSeek) answers the same 8 questions in a second, separate
                     conversation. Fails if fewer than 5 of the 8 answers are the same option.
  Check 5, models:   the 8 questions are also answered by Nemotron and Muse playing the same user.
                     Fails if two models are 2 or more bands apart on willingness or behavior.
                     Muse costs about 15 times more, so it runs on --muse-users users (default 10).

A user who fails 2 or more checks is marked EXCLUDE (decided Nov 13: left out of the scoring).
If results/persona_check1_facts.jsonl exists, check 1 counts too (fail = 2 or more wrong facts).

Run from the repo folder:
  python mirofish/persona_checks.py --mock --limit 10    # free test with fake answers, saves nothing
  python mirofish/persona_checks.py --limit 10           # small real run, a few cents
  python mirofish/persona_checks.py                      # all 100 users, under $1
  python mirofish/persona_checks.py --rescore            # rebuild the tables from saved answers

Results (in mirofish/):
  persona_checks_235.md            summary and the per-user table
  persona_checks_235.csv           the per-user table, for rescoring
  persona_checks_exclude.json      ids of users that fail 2 or more checks
  persona_checks_235_answers.jsonl every answer, so the tables can be rebuilt with --rescore
"""

import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import config as C          # noqa: E402
import prompts as P         # noqa: E402
import run_bakeoff as R     # noqa: E402
from llm import strip_think  # noqa: E402

BASE = "deepseek-v4-flash-0731"            # the experiment's simulated-user model
OTHERS = ["nemotron-3.5-super", "muse-spark-open"]
MUSE = "muse-spark-open"
ANSWERS = HERE / "persona_checks_235_answers.jsonl"
CHECK1 = ROOT / "results" / "persona_check1_facts.jsonl"
PANIC = "says aggressive, would panic-sell"

# 8 new questions. Options are (text, score). Order is mixed so the bold answer is not always E.
QUESTIONS = [
    {"id": "PW1", "dim": "willingness",
     "q": "You get a $5,000 bonus that you can invest for the long run. How would you split it?",
     "opts": [("All of it in a savings account", 0.1),
              ("Mostly savings, a small part in stocks", 0.3),
              ("About half savings, half stocks", 0.5),
              ("Mostly stocks, a little in savings", 0.7),
              ("All in stocks, including a few high-growth picks", 0.9)]},
    {"id": "PB1", "dim": "behavioral",
     "q": "Your phone shows an alert: your investments just had their worst week in years. What do "
          "you actually do in the next hour?",
     "opts": [("Buy more while prices are low", 0.9),
              ("Glance at it, then get on with my day", 0.7),
              ("Keep checking, worry, but don't sell", 0.5),
              ("Sell a good part so I can stop worrying", 0.3),
              ("Sell everything right away", 0.1)]},
    {"id": "PW2", "dim": "willingness",
     "q": "Which statement sounds most like you?",
     "opts": [("I want my money to be safe, even if it grows very little", 0.1),
              ("I prefer steady, small gains to big swings", 0.3),
              ("I'm fine with some ups and downs for decent growth", 0.5),
              ("I'm happy to take real risk to grow my money faster", 0.7),
              ("I want the most growth possible and big swings don't scare me", 0.9)]},
    {"id": "PB2", "dim": "behavioral",
     "q": "You set up an automatic $200 deposit into your investments every month. Then prices fall "
          "sharply for two months. What really happens to your plan?",
     "opts": [("I stop the deposits and take my money out", 0.1),
              ("I stop the deposits until things calm down", 0.3),
              ("I lower the deposits for a while", 0.5),
              ("I keep the deposits the same", 0.7),
              ("I add extra money while prices are low", 0.9)]},
    {"id": "PW3", "dim": "willingness",
     "q": "How do you feel about the saying 'no risk, no reward' when it comes to your own money?",
     "opts": [("That's exactly how I think", 0.9),
              ("I mostly agree", 0.7),
              ("It's true sometimes, in moderation", 0.5),
              ("I'd rather not test it", 0.3),
              ("I disagree: protecting my money comes first", 0.1)]},
    {"id": "PB3", "dim": "behavioral",
     "q": "After a big market drop, a friend asks what you did with your investments. Which answer "
          "is closest to the truth?",
     "opts": [("I sold almost everything to stop the losses", 0.1),
              ("I sold a good part and felt safer", 0.3),
              ("I sold a little but kept most of it", 0.5),
              ("I kept everything and waited", 0.7),
              ("I bought more while it was cheap", 0.9)]},
    {"id": "PW4", "dim": "willingness",
     "q": "A coworker suggests putting part of your savings into a new, fast-growing fund that could "
          "also fall a lot. What is your first thought?",
     "opts": [("Sounds exciting, I'd put a big part in", 0.9),
              ("I'd try it with a meaningful amount", 0.7),
              ("Maybe a small amount, after reading about it", 0.5),
              ("Probably not, it sounds too risky", 0.3),
              ("No way, I don't want my savings to fall", 0.1)]},
    {"id": "PB4", "dim": "behavioral",
     "q": "Your investments have been down for a long slump. How do you really handle it day to day?",
     "opts": [("I see it as a chance and look for more to buy", 0.9),
              ("I mostly forget about it and don't change anything", 0.7),
              ("I feel uneasy and check often, but I hold on", 0.5),
              ("I lose sleep and move some money to safety", 0.3),
              ("I can't stand it and sell so the stress stops", 0.1)]},
]
LETTERS = "ABCDE"
DIMS = ("willingness", "behavioral")


def ask_text(q):
    lines = [q["q"]] + [f"{L}) {t}" for L, (t, _) in zip(LETTERS, q["opts"])]
    lines.append("Reply with just the letter (A, B, C, D or E) of your answer.")
    return "\n".join(lines)


def parse_letter(text, q):
    """The option the answer picked, as an index 0-4, or None if it is not clear."""
    t = text.strip()
    m = re.match(r"^\W*([A-Ea-e])\W*$", t) or re.match(r"^\W*([A-E])(?:[).:]|\s+[-\u2013\u2014])", t)
    if m:
        return LETTERS.index(m.group(1).upper())
    hits = set(re.findall(r"(?:\(|\b(?:option|answer|choice|letter|go with|pick)\s*\(?)([A-E])\b", t, re.I))
    hits |= set(re.findall(r"\b([B-E])\)", t))
    if len({h.upper() for h in hits}) == 1:
        return LETTERS.index(hits.pop().upper())
    low = t.lower()
    found = [i for i, (o, _) in enumerate(q["opts"]) if o.lower().rstrip(".") in low]
    return found[0] if len(found) == 1 else None


def interview(llm, model, p, run, mock):
    """One fresh conversation: the 8 questions in order, no noise."""
    msgs = [{"role": "system", "content": P.build_user_system(p)}]
    rows, cost = [], 0.0
    for q in QUESTIONS:
        msgs.append({"role": "user", "content": ask_text(q)})
        r = llm.chat(model, msgs, "off", C.USER_MAX_TOKENS, C.USER_TEMPERATURE)
        a = strip_think(r["text"]) or "(no answer)"
        if mock:   # fake answers near the truth, so the tables have something to show
            true_idx = [s for _, s in q["opts"]].index(
                min((s for _, s in q["opts"]), key=lambda s: abs(s - p["ground_truth"][q["dim"]])))
            a = LETTERS[max(0, min(4, true_idx + random.choice([-2, -1, 0, 0, 0, 1])))]
        m = C.MODELS[model]
        cost += (r["usage"]["in"] * m["price_in"] + r["usage"]["out"] * m["price_out"]) / 1e6
        msgs.append({"role": "assistant", "content": a})
        idx = parse_letter(a, q)
        rows.append({"persona_id": p["id"], "model": model, "run": run, "q": q["id"], "dim": q["dim"],
                     "answer": a, "option": idx,
                     "score": None if idx is None else q["opts"][idx][1]})
    return rows, cost


def collect(args, personas):
    llm = R.make_llm(args.mock)
    jobs = []
    n, k = len(personas), min(args.muse_users, len(personas))
    muse_at = {int(j * n / k) for j in range(k)} if k else set()   # spread over the file
    for i, p in enumerate(personas):
        jobs += [(BASE, p, 1), (BASE, p, 2), ("nemotron-3.5-super", p, 1)]
        if i in muse_at:
            jobs.append((MUSE, p, 1))
    print(f"{len(jobs)} conversations of 8 questions ...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        res = list(ex.map(lambda j: interview(llm, j[0], j[1], j[2], args.mock), jobs))
    rows = [r for rs, _ in res for r in rs]
    cost = sum(c for _, c in res)
    if not args.mock:
        ANSWERS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows, cost


def avg_band(rows, dim):
    s = [r["score"] for r in rows if r["dim"] == dim and r["score"] is not None]
    return (None, None) if not s else (round(sum(s) / len(s), 2), P.band(sum(s) / len(s)))


def check1_fails():
    if not CHECK1.exists():
        return None
    wrong = defaultdict(int)
    for line in CHECK1.read_text().splitlines():
        r = json.loads(line)
        wrong[r["persona_id"]] += 0 if r["ok"] else 1
    return wrong


def pct(n, d):
    return f"{100 * n / d:.0f}% of {d}" if d else "n/a"


def report(args, personas, rows, cost):
    by = defaultdict(list)
    for r in rows:
        by[(r["persona_id"], r["model"], r["run"])].append(r)
    c1 = check1_fails()
    table = []
    for p in personas:
        pid, gt = p["id"], p["ground_truth"]
        base = by[(pid, BASE, 1)]
        if not base:
            continue
        row = {"id": pid, "final_band": gt["final_band"], "mismatch_type": gt["mismatch_type"],
               "true_will_band": P.band(gt["willingness"]), "true_beh_band": P.band(gt["behavioral"])}
        # check 2
        ok2 = True
        for dim, key in (("willingness", "will"), ("behavioral", "beh")):
            a, b = avg_band(base, dim)
            row[f"c2_{key}_avg"], row[f"c2_{key}_band"] = a, b
            if b is None or abs(b - P.band(gt[dim])) > 1:
                ok2 = False
        row["unclear_answers"] = sum(r["option"] is None for r in base)
        row["check2"] = "pass" if ok2 else "FAIL"
        # check 3
        second = {r["q"]: r["option"] for r in by[(pid, BASE, 2)]}
        same = sum(1 for r in base if r["option"] is not None and r["option"] == second.get(r["q"]))
        row["c3_same_of_8"] = same
        row["check3"] = "pass" if same >= args.repeat_min else "FAIL"
        # check 5
        models = [BASE] + [m for m in OTHERS if by[(pid, m, 1)]]
        bands = {m: {d: avg_band(by[(pid, m, 1)], d)[1] for d in DIMS} for m in models}
        spread_ok, all_same = True, True
        for d in DIMS:
            vals = [bands[m][d] for m in models]
            if None in vals or max(vals) - min(vals) >= 2:
                spread_ok = False
            if None in vals or len(set(vals)) > 1:
                all_same = False
        row["c5_models"] = len(models)
        row["c5_bands"] = " / ".join(f"{bands[m]['willingness']},{bands[m]['behavioral']}" for m in models)
        row["c5_all_same"] = all_same
        row["check5"] = "pass" if spread_ok else "FAIL"
        if c1 is not None:
            row["check1"] = "FAIL" if c1.get(pid, 0) >= 2 else "pass"
        checks = ["check2", "check3", "check5"] + (["check1"] if c1 is not None else [])
        row["fails"] = sum(row[c] == "FAIL" for c in checks)
        row["exclude"] = row["fails"] >= 2
        table.append(row)

    n = len(table)
    lines = [f"# Persona checks 2, 3 and 5 ({n} test users, backstories on)", "",
             f"Each test user answered 8 new multiple-choice questions (4 willingness, 4 behavior, none "
             f"from `question_bank.json`) with no noise. Each option has a fixed score. "
             f"Script: `mirofish/persona_checks.py`." + (" **MOCK RUN: fake answers.**" if args.mock else ""),
             "", "| check | rule | users that fail |", "|---|---|---|"]
    lines.append(f"| 2. profile | average willingness and behavior score in the true band or one away "
                 f"| {pct(sum(r['check2'] == 'FAIL' for r in table), n)} |")
    lines.append(f"| 3. repeat | same option on at least {args.repeat_min} of 8 in a second conversation "
                 f"| {pct(sum(r['check3'] == 'FAIL' for r in table), n)} |")
    n5 = sum(r["c5_models"] == 3 for r in table)
    lines.append(f"| 5. models | DeepSeek, Nemotron (and Muse on {n5} users) within one band on both "
                 f"| {pct(sum(r['check5'] == 'FAIL' for r in table), n)} |")
    if c1 is not None:
        lines.append(f"| 1. facts (from `{CHECK1.relative_to(ROOT)}`) | fewer than 2 wrong facts "
                     f"| {pct(sum(r['check1'] == 'FAIL' for r in table), n)} |")
    excl = [r["id"] for r in table if r["exclude"]]
    lines += ["", f"**Users that fail 2 or more checks (left out of the scoring): {len(excl)}**"
              + (": " + ", ".join(excl) if excl else "."), ""]

    # extra detail
    for dim, key in (("willingness", "will"), ("behavioral", "beh")):
        exact = sum(r[f"c2_{key}_band"] == r[f"true_{key}_band"] for r in table)
        lines.append(f"- Check 2, {dim}: exact band {pct(exact, n)}.")
    same_all = sum(r["c3_same_of_8"] for r in table)
    lines.append(f"- Check 3: same option on {pct(same_all, 8 * n)} answers overall.")
    lines.append(f"- Check 5: all models gave exactly the same two bands for {pct(sum(r['c5_all_same'] for r in table), n)} users.")
    lines.append(f"- Unclear answers (no option could be read): {sum(r['unclear_answers'] for r in table)} of {8 * n}.")
    panic = [r for r in table if r["mismatch_type"] == PANIC]
    if panic:
        bold = sum(r["c2_will_band"] is not None and r["c2_will_band"] >= r["true_will_band"] - 1 for r in panic)
        fear = sum(r["c2_beh_band"] is not None and r["c2_beh_band"] <= r["true_beh_band"] + 1 for r in panic)
        gap = sum(None not in (r["c2_will_avg"], r["c2_beh_avg"]) and r["c2_will_avg"] > r["c2_beh_avg"] for r in panic)
        lines += ["", f"**\"{PANIC}\" users ({len(panic)}).** They must talk bold and act scared.", "",
                  f"- Willingness answers bold enough (true band or one away): {pct(bold, len(panic))}",
                  f"- Behavior answers scared enough (true band or one away): {pct(fear, len(panic))}",
                  f"- Willingness average higher than behavior average: {pct(gap, len(panic))}",
                  f"- Pass check 2: {pct(sum(r['check2'] == 'pass' for r in panic), len(panic))}"]
    if cost and not args.mock:
        lines += ["", f"Cost of this run: about ${cost:.2f}."]

    cols = ["id", "final_band", "mismatch_type", "true_will_band", "c2_will_band", "true_beh_band",
            "c2_beh_band", "check2", "c3_same_of_8", "check3", "c5_bands", "check5"] + \
           (["check1"] if c1 is not None else []) + ["fails", "exclude"]
    lines += ["", "## Per user", "",
              "c5 bands: willingness,behavior band from each model, in the order DeepSeek / Nemotron / Muse.", "",
              "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in sorted(table, key=lambda r: (-r["fails"], r["id"])):
        lines.append("| " + " | ".join(("**yes**" if r[c] else "") if c == "exclude" else str(r[c]) for c in cols) + " |")

    text = "\n".join(lines) + "\n"
    print(text)
    if args.mock:
        print("(mock run: nothing saved)")
        return
    (HERE / "persona_checks_235.md").write_text(text)
    with open(HERE / "persona_checks_235.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        w.writeheader()
        w.writerows(table)
    (HERE / "persona_checks_exclude.json").write_text(json.dumps(excl, indent=2) + "\n")
    print("Saved mirofish/persona_checks_235.md, .csv, persona_checks_exclude.json and the answers.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, help="only this many users, spread over the bands")
    ap.add_argument("--muse-users", type=int, default=10, help="how many users Muse also plays (default 10)")
    ap.add_argument("--repeat-min", type=int, default=5, help="check 3 passes with this many same answers of 8")
    ap.add_argument("--rescore", action="store_true", help="rebuild the tables from saved answers, no API calls")
    ap.add_argument("--mock", action="store_true", help="fake answers, no cost, saves nothing")
    args = ap.parse_args()
    R.load_env()
    personas = R.load_personas(C.EXPERIMENT_PERSONAS, args.limit)
    if args.rescore:
        rows = [json.loads(x) for x in ANSWERS.read_text().splitlines()]
        for r in rows:   # read the options again, in case the parser changed
            q = next(q for q in QUESTIONS if q["id"] == r["q"])
            r["option"] = parse_letter(r["answer"], q)
            r["score"] = None if r["option"] is None else q["opts"][r["option"]][1]
        return report(args, personas, rows, 0)
    rows, cost = collect(args, personas)
    report(args, personas, rows, cost)


if __name__ == "__main__":
    main()
