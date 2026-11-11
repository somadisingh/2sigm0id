"""Persona checks 1 and 4 (plan.md, section 3): do the AI test users behave as designed?

  Check 1, facts:  each test user is asked its money facts directly, in a fresh conversation
                   with no noise. Code compares each answer with the true fact.
  Check 4, noise:  the planned noise must really show in the answers. Uses the turns of an
                   experiment results file, so no new interviews are needed.
                   - forms (A, C): a "flip" answer must lean away from the true score; a
                     "vague" answer must pick a middle option more often than clean answers do
                   - spoken (B, D): an injected contradiction must state the planned wrong
                     value; a judge model checks this, and the same judge also checks clean
                     answers about the same fact, which gives its false-alarm rate
                   - spoken "flip" turns: D's reading of the answer must lean away from the
                     true score
                   - "acquiescence" (agreeing with a hint) cannot be checked: our questions
                     never hint at an answer

  python check_personas.py facts                                   # about $0.06
  python check_personas.py noise results/experiment_100users_b10.jsonl   # about $0.10

Results: persona_checks/check1_facts.md and persona_checks/check4_noise.md.
Persona checks 2, 3, 5 and 6 are Siya's (plan.md, task S3).
"""

import argparse
import json
import random
import re
import statistics as st
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import config as C
import prompts as P
import run_bakeoff as R
from capacity import INCOME_SCORE
from check_extractor import norm
from llm import extract_json, strip_think
from score import probe_ok

HERE = Path(__file__).resolve().parent
OUT = HERE / "persona_checks"
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
ITEMS = {i["id"]: i for i in json.loads((HERE / "question_bank.json").read_text())["items"]}

FACT_PROBES = P.PROBES + [
    {"field": "debt_to_income", "kind": "number",
     "q": "Quick check outside the interview: roughly what percent of your monthly income goes to "
          "debt payments? Reply with just a number."},
    {"field": "income_stability", "kind": "choice",
     "q": "How would you describe your income? Reply with one of these: unstable, partly "
          "commission-based, stable, very stable."},
]
INCOME_WORDS = [("partly commission", 0.33), ("commission", 0.33), ("very stable", 1.0),
                ("unstable", 0.0), ("stable", 0.67)]   # longest phrases first


WORD_NUMS = {w: n for n, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty".split())}
WORD_NUMS.update({"thirty": 30, "forty": 40, "fifty": 50, "a couple": 2, "a few": 3,
                  "none": 0, "nobody": 0, "no one": 0, "nothing": 0, "no ": 0, "half": 0.5,
                  "quarter": 0.25})


def first_number(text, field):
    """The first number in an answer, in digits or words ("three months", "zero", "half a
    month", "twenty-five"). For savings, "a year" counts as 12 months."""
    a = " " + text.lower().replace("-", " ") + " "
    found = [(m.start(), float(m.group())) for m in NUM_RE.finditer(a)]
    for w, n in WORD_NUMS.items():
        for m in re.finditer(r"\b" + re.escape(w.strip()) + (r"\b" if not w.endswith(" ") else r"\s"), a):
            val = n
            nxt = a[m.end():].split()
            if n in (20, 30, 40, 50) and nxt and nxt[0] in WORD_NUMS and 0 < WORD_NUMS[nxt[0]] < 10:
                val = n + WORD_NUMS[nxt[0]]   # "twenty five"
            found.append((m.start(), float(val)))
    if field == "emergency_fund_months" and not found and re.search(r"\ba year\b", a):
        return 12.0
    if not found:
        return None
    pos, val = min(found)
    if field == "emergency_fund_months" and re.match(r"\s*[\w.]+\s+years?\b", a[pos:]):
        val *= 12   # "two years of expenses"
    return val


def fact_ok(field, answer, p):
    """True if the answer matches the test user's true fact. Tolerances as in stage 2:
    savings within 1 month or 50%, horizon within 2 years or 30%, dependents exact, debt
    within 5 points or 30%."""
    a = (answer or "").lower()
    if field == "past_loss_reaction":
        return probe_ok(field, answer, p)
    if field == "income_stability":
        got = next((s for w, s in INCOME_WORDS if w in a), None)
        return got is not None and abs(got - INCOME_SCORE[p["finances"]["income_stability"]]) < 0.01
    x = first_number(a, field)
    if x is None:
        return False
    truth = p["finances"][field]
    if field == "debt_to_income":
        truth *= 100
        return abs(x - truth) <= max(5.0, 0.3 * truth)
    if field == "dependents":
        return x == truth
    if field == "emergency_fund_months":
        return abs(x - truth) <= max(1.0, 0.5 * truth)
    return abs(x - truth) <= max(2.0, 0.3 * truth)


def facts(args):
    llm = R.make_llm(args.mock)
    personas = R.load_personas(C.EXPERIMENT_PERSONAS, args.limit)
    if args.rescore:   # score saved answers again (for example after a scoring fix); no API calls
        saved = [json.loads(x) for x in (HERE / "results" / "persona_check1_facts.jsonl").read_text().splitlines()]
        by_id = {p["id"]: p for p in personas}
        rows = [{**r, "ok": fact_ok(r["field"], r["answer"], by_id[r["persona_id"]])}
                for r in saved if r["persona_id"] in by_id]
        return report_facts(args, personas, rows)

    def one(p):
        msgs = [{"role": "system", "content": P.build_user_system(p)}]
        rows = []
        for pr in FACT_PROBES:
            msgs.append({"role": "user", "content": pr["q"]})
            r = llm.chat(C.EXPERIMENT_USER, msgs, C.EXPERIMENT_USER_REASONING, C.USER_MAX_TOKENS,
                         C.USER_TEMPERATURE)
            a = strip_think(r["text"]) or "(no answer)"
            msgs.append({"role": "assistant", "content": a})
            rows.append({"persona_id": p["id"], "field": pr["field"], "answer": a,
                         "ok": fact_ok(pr["field"], a, p),
                         "refuses_numbers": p["noise"]["refuses_numbers"]})
        return rows

    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        rows = [r for rs in ex.map(one, personas) for r in rs]
    report_facts(args, personas, rows)


def report_facts(args, personas, rows):
    by_p = defaultdict(list)
    for r in rows:
        by_p[r["persona_id"]].append(r)
    lines = [f"# Persona check 1: facts ({len(personas)} test users, backstories "
             f"{'on' if C.USE_BACKSTORIES else 'off'})", "",
             "Each test user answers six direct questions about its facts, in a fresh conversation "
             "with no noise. Code compares the answer with the true fact.", "",
             "| fact | right, all users | right, users told to avoid numbers |", "|---|---|---|"]
    for pr in FACT_PROBES:
        f = [r for r in rows if r["field"] == pr["field"]]
        a = [r["ok"] for r in f if not r["refuses_numbers"]]
        b = [r["ok"] for r in f if r["refuses_numbers"]]
        lines.append(f"| {pr['field']} | {st.mean(a):.0%} of {len(a)} | "
                     f"{f'{st.mean(b):.0%} of {len(b)}' if b else '-'} |")
    fails = {pid: [r for r in rs if not r["ok"]] for pid, rs in by_p.items()}
    two = sorted(pid for pid, fs in fails.items() if len(fs) >= 2 and not by_p[pid][0]["refuses_numbers"])
    lines += ["", f"Users with all six facts right: {sum(not fs for fs in fails.values())} of {len(by_p)}.",
              f"Users (not told to avoid numbers) with 2 or more wrong facts: {len(two)}"
              + (f": {', '.join(two)}" if two else "."), "",
              "Wrong answers (first 15):", ""]
    wrong = [r for r in rows if not r["ok"] and not r["refuses_numbers"]][:15]
    by_id = {p["id"]: p for p in personas}
    for r in wrong:
        p = by_id[r["persona_id"]]
        truth = p["experience"]["past_loss_reaction"] if r["field"] == "past_loss_reaction" else p["finances"][r["field"]]
        lines.append(f'- {r["persona_id"]}, {r["field"]}: true {truth}, said "{r["answer"][:100]}"')
    write(args, "check1_facts", lines, rows)


JUDGE_SYSTEM = (
    "You check one answer from an interview. Decide if the answer states the given statement, "
    "or clearly implies it. Reply with ONE JSON object and nothing else: "
    '{"says_it": true or false, "quote": "<the shortest exact words from the answer that '
    'state it, or empty>"}')
JUDGE_MESSAGE = 'Question: {q}\nAnswer: "{a}"\nStatement: {statement}'


def says(llm, key, q, a, statement):
    """Judge: does the answer state the statement? Needs a quote that is in the answer."""
    msgs = [{"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": JUDGE_MESSAGE.format(q=q, a=a, statement=statement)}]
    r = llm.chat(key, msgs, "low", 4000, 0.0)
    obj = extract_json(r["text"])
    if not isinstance(obj, dict) or not isinstance(obj.get("says_it"), bool):
        return None
    quote = str(obj.get("quote") or "")
    return obj["says_it"] and bool(quote.strip()) and norm(quote) in norm(a)


def leans_away(score, truth):
    """A flipped answer sits closer to the mirror of the true score than to the true score.
    Undecidable when the true score is near the middle."""
    if score is None or abs(truth - 0.5) < 0.15:
        return None
    return abs(score - (1 - truth)) < abs(score - truth)


def noise(args):
    llm = R.make_llm(args.mock)
    recs = [json.loads(x) for x in Path(args.file).read_text().splitlines() if x.strip()]
    recs = [r for r in recs if not r.get("error")]
    lines = [f"# Persona check 4: does the planned noise really happen? ({Path(args.file).name})", ""]

    # forms: flip and vague, by rule
    lines += ["## Form answers (methods A and C), checked by rule", "",
              "| noise | turns | checkable | answer shows it | same rule on clean answers |",
              "|---|---|---|---|---|"]
    form = [(r, t) for r in recs if r["method"] in ("A", "C") for t in r["turns"]
            if t["item"] in ITEMS and ITEMS[t["item"]]["dimension"] != "capacity"]
    def flip_rule(r, t):
        return leans_away(t["score"], r["truth"][ITEMS[t["item"]]["dimension"]])
    def mid_rule(r, t):
        return None if t["score"] is None else 0.25 <= t["score"] <= 0.75
    for kind, rule in (("flip", flip_rule), ("vague", mid_rule)):
        hit = [rule(r, t) for r, t in form if kind in t["noise"]]
        base = [rule(r, t) for r, t in form if not t["noise"]]
        h, b = [x for x in hit if x is not None], [x for x in base if x is not None]
        lines.append(f"| {kind} | {len(hit)} | {len(h)} | {st.mean(h):.0%} | {st.mean(b):.0%} of {len(b)} |")
    lines += ["", "flip: the chosen option is closer to the mirror of the true score than to the true "
              "score (not checkable when the true score is within 0.15 of the middle). vague: the "
              "chosen option scores between 0.25 and 0.75.", ""]

    # spoken: injected contradictions, by judge, with a false-alarm control
    contra = [(r, t) for r in recs if r["method"] in ("B", "D") for t in r["turns"]
              if "contradiction" in t["noise"] and t.get("contradiction_target")]
    control = []
    for r, t in contra:   # clean answers by the same user about the same fact
        tgt = t["contradiction_target"]
        for u in r["turns"]:
            if not u["noise"] and u["item"] in ITEMS and ITEMS[u["item"]].get("fact") == tgt["fact"]:
                control.append((r, u, tgt))
    rng = random.Random(0)
    if args.sample and len(control) > args.sample:
        control = rng.sample(control, args.sample)
    statement = lambda tgt: tgt["wrong"].removeprefix("say ")  # noqa: E731
    jobs = [("contradiction", r, t, t["contradiction_target"]) for r, t in contra] + \
           [("control", r, u, tgt) for r, u, tgt in control]
    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        verdicts = list(ex.map(lambda j: says(llm, "nemotron-3.5-super", j[2]["q"], j[2]["a"], statement(j[3])), jobs))
    res = defaultdict(list)
    for (kind, r, t, tgt), v in zip(jobs, verdicts):
        res[(kind, r["method"])].append(v)
    lines += ["## Spoken answers (methods B and D): injected contradictions", "",
              "A judge model (Nemotron 3.5 Super, with thinking) decides if the answer states the planned "
              "wrong value. It must quote the words, and code checks that the quote is in the answer. "
              "The control asks the same judge about clean answers by the same user about the same fact, "
              "where the wrong value should not appear.", "",
              "| method | contradiction turns: wrong value stated | control, clean answers: wrong value 'found' |",
              "|---|---|---|"]
    for m in ("B", "D"):
        c = [v for v in res[("contradiction", m)] if v is not None]
        k = [v for v in res[("control", m)] if v is not None]
        lines.append(f"| {m} | {st.mean(c):.0%} of {len(c)} | " + (f"{st.mean(k):.0%} of {len(k)}" if k else "-") + " |")
    by_fact = defaultdict(list)
    for (kind, r, t, tgt), v in zip(jobs, verdicts):
        if kind == "contradiction" and v is not None:
            by_fact[tgt["fact"]].append(v)
    lines += ["", "By fact: " + ", ".join(f"{f} {st.mean(v):.0%} of {len(v)}" for f, v in sorted(by_fact.items())), ""]

    # spoken flips: D's own reading leans away from the true score
    def d_turns(flipped):
        out = []
        for r in recs:
            if r["method"] != "D":
                continue
            for t in r["turns"]:
                dim = ITEMS.get(t["item"], {}).get("dimension")
                if dim in (None, "capacity") or (("flip" in t["noise"]) != flipped) or (not flipped and t["noise"]):
                    continue
                got = (t.get("evidence") or {}).get(dim)
                out.append(leans_away(got["score"] if got else None, r["truth"][dim]))
        return [x for x in out if x is not None]
    f, b = d_turns(True), d_turns(False)
    if f:
        lines += ["## Spoken answers (method D): flips", "",
                  f"D's reading leans away from the true score in {st.mean(f):.0%} of {len(f)} flip turns, "
                  f"and in {st.mean(b):.0%} of {len(b)} clean turns.", ""]
    acq = sum("acquiescence" in t["noise"] for r in recs for t in r["turns"])
    lines += ["## Acquiescence", "",
              f"{acq} turns carried the note \"if the question hints at an answer, go along with it\". "
              "Our bank questions never hint at an answer, so this noise cannot show and cannot be "
              "checked. It has no effect in this design.", ""]
    write(args, "check4_noise", lines, [{"job": j[0], "method": j[1]["method"], "persona_id": j[1]["persona_id"],
                                         "q": j[2]["q"], "a": j[2]["a"], "statement": statement(j[3]),
                                         "verdict": v} for j, v in zip(jobs, verdicts)])


def write(args, name, lines, raw):
    text = "\n".join(lines) + "\n"
    if not args.mock:
        OUT.mkdir(exist_ok=True)
        (OUT / f"{name}.md").write_text(text)
        (HERE / "results").mkdir(exist_ok=True)
        (HERE / "results" / f"persona_{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in raw))
    print(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("facts")
    f.add_argument("--limit", type=int)
    f.add_argument("--rescore", action="store_true", help="score the saved answers again, with no API calls")
    f.add_argument("--mock", action="store_true")
    f.set_defaults(fn=facts)
    n = sub.add_parser("noise")
    n.add_argument("file")
    n.add_argument("--sample", type=int, default=200, help="at most this many control answers")
    n.add_argument("--mock", action="store_true")
    n.set_defaults(fn=noise)
    args = ap.parse_args()
    R.load_env()
    args.fn(args)


if __name__ == "__main__":
    main()
