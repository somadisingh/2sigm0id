"""Check the question bank and test it with a rule-based answerer.

  python check_question_bank.py              # format checks + rule-based test on personas.json
  python check_question_bank.py --write-md   # also rewrite question_bank.md from the JSON

The rule-based answerer uses no AI: it answers fact questions straight from each
persona's facts and every other question with the option closest to the persona's
true score. It is also the "non-LLM answerer" control from the shared contract.
"""

import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIMS = ("capacity", "willingness", "behavioral")
BUDGETS = ("5", "10", "15")

# How persona income descriptions map to CAP03's options (by option score).
INCOME_SCORE = {
    "unstable": 0.0, "partly commission-based": 0.33, "stable": 0.67,
    "very stable": 1.0, "stable and high": 1.0,
}


def band(score):
    return min(5, int(score * 5) + 1)


def load():
    return json.loads((HERE / "question_bank.json").read_text())


def check_format(bank):
    problems = []
    items = bank["items"]
    ids = [i["id"] for i in items]
    if len(ids) != len(set(ids)):
        problems.append("duplicate item ids")
    for dim in DIMS:
        pri = sorted(i["priority"] for i in items if i["dimension"] == dim)
        if pri != list(range(1, len(pri) + 1)):
            problems.append(f"{dim}: priorities should be 1..{len(pri)} with no gaps, got {pri}")
    for i in items:
        if i["dimension"] not in DIMS:
            problems.append(f"{i['id']}: unknown dimension {i['dimension']}")
        if not i.get("text") or not i.get("spoken"):
            problems.append(f"{i['id']}: needs both 'text' and 'spoken' wording")
        scores = [o["score"] for o in i["options"] if o["score"] is not None]
        if len(i["options"]) < 3:
            problems.append(f"{i['id']}: fewer than 3 options")
        if any(not 0 <= s <= 1 for s in scores):
            problems.append(f"{i['id']}: a score is outside 0-1")
        if scores != sorted(scores) or len(set(scores)) != len(scores):
            problems.append(f"{i['id']}: scores should rise strictly from option to option")
        if min(scores) != 0 or max(scores) != 1:
            problems.append(f"{i['id']}: scores should span 0 to 1")
    for b, alloc in bank["short_form_allocation"].items():
        if sum(alloc.values()) != int(b):
            problems.append(f"short form {b}: allocation adds up to {sum(alloc.values())}")
        for dim, n in alloc.items():
            if n > sum(i["dimension"] == dim for i in items):
                problems.append(f"short form {b}: asks for {n} {dim} items, bank has fewer")
    return problems


def short_form(bank, budget):
    """Default short form: the top-priority items in each dimension."""
    if budget == "all":
        return list(bank["items"])
    alloc = bank["short_form_allocation"][budget]
    chosen = []
    for dim in DIMS:
        pool = sorted((i for i in bank["items"] if i["dimension"] == dim), key=lambda i: i["priority"])
        chosen += pool[:alloc[dim]]
    return chosen


def in_range(value, rng):
    lo, hi = rng
    return value >= lo and (hi is None or value < hi)


def rule_based_answer(item, persona):
    """Return the chosen option for one item."""
    fact = item.get("fact")
    if fact == "income_stability":
        target = INCOME_SCORE[persona["finances"]["income_stability"]]
        return min(item["options"], key=lambda o: abs(o["score"] - target))
    if fact == "past_loss_reaction":
        value = persona["experience"]["past_loss_reaction"]
        return next(o for o in item["options"] if o.get("fact_value") == value)
    if fact:
        value = persona["finances"][fact]
        return next(o for o in item["options"] if in_range(value, o["range"]))
    target = persona["ground_truth"][item["dimension"]]
    scored = [o for o in item["options"] if o["score"] is not None]
    return min(scored, key=lambda o: abs(o["score"] - target))


def score_form(items, answers):
    out = {}
    for dim in DIMS:
        vals = [answers[i["id"]]["score"] for i in items
                if i["dimension"] == dim and answers[i["id"]]["score"] is not None]
        out[dim] = st.mean(vals) if vals else 0.5
    return out


def rule_based_test(bank, personas):
    print("RULE-BASED TEST (no AI). Error = |estimate - truth|; band = lowest of three.\n")
    forms = list(BUDGETS) + ["all"]
    summary = {f: {"err": [], "band": []} for f in forms}
    for p in personas:
        gt = p["ground_truth"]
        print(f"{p['id']}   truth: cap {gt['capacity']:.2f}  will {gt['willingness']:.2f}  "
              f"beh {gt['behavioral']:.2f}  band {gt['final_band']}")
        for f in forms:
            items = short_form(bank, f)
            answers = {i["id"]: rule_based_answer(i, p) for i in items}
            est = score_form(items, answers)
            err = st.mean(abs(est[d] - gt[d]) for d in DIMS)
            b = min(band(est[d]) for d in DIMS)
            summary[f]["err"].append(err)
            summary[f]["band"].append(b == gt["final_band"])
            label = f"{f} questions" if f != "all" else "all 35"
            print(f"   {label:13} cap {est['capacity']:.2f}  will {est['willingness']:.2f}  "
                  f"beh {est['behavioral']:.2f}  band {b}   error {err:.3f}")
        print()
    print("SUMMARY")
    for f in forms:
        label = f"{f} questions" if f != "all" else "all 35"
        s = summary[f]
        print(f"   {label:13} avg error {st.mean(s['err']):.3f}   band exact "
              f"{sum(s['band'])}/{len(s['band'])}")


def write_md(bank):
    names = {"capacity": "Capacity (what they can afford to lose)",
             "willingness": "Willingness (how they say they feel about risk)",
             "behavioral": "Behavior (what they would actually do in a loss)"}
    in_form = {b: {i["id"] for i in short_form(bank, b)} for b in BUDGETS}
    lines = [f"# Question bank {bank['version']}", "", bank["about"], "",
             "Generated from `question_bank.json` by `check_question_bank.py --write-md`; "
             "edit the JSON, not this file.", "",
             "**Scoring:** each answer scores 0 (lowest risk) to 1 (highest); a dimension is the "
             "average of its answered items; the final band is the lowest of the three. "
             "Short-form columns mark which items the default 5-, 10- and 15-question forms use.", ""]
    for dim in DIMS:
        lines += [f"## {names[dim]}", "",
                  "| # | ID | Question | Answers (score) | In forms |", "|---|---|---|---|---|"]
        for i in sorted((i for i in bank["items"] if i["dimension"] == dim), key=lambda i: i["priority"]):
            opts = "; ".join(f"{o['label']} ({'skip' if o['score'] is None else o['score']})"
                             for o in i["options"])
            forms = ", ".join(b for b in BUDGETS if i["id"] in in_form[b]) or "-"
            fact = f" *(fact: {i['fact']})*" if i.get("fact") else ""
            lines.append(f"| {i['priority']} | {i['id']} | {i['text']}{fact} | {opts} | {forms} |")
        lines.append("")
    lines += ["## Notes for review", "",
              f"- {bank['short_form_note']}",
              f"- {bank['scoring']['capacity_note']}",
              "- Behavior items ask people to predict what they would do. That is still self-report, "
              "so BEH02 (past behavior) is the strongest behavior item when the person has lived through a drop.", ""]
    (HERE / "question_bank.md").write_text("\n".join(lines))
    print("Wrote question_bank.md")


def main():
    bank = load()
    problems = check_format(bank)
    counts = {d: sum(i["dimension"] == d for i in bank["items"]) for d in DIMS}
    print(f"{len(bank['items'])} items: {counts}")
    if problems:
        print("FORMAT PROBLEMS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("Format OK.")
    for b in BUDGETS:
        print(f"  {b}-question form: {', '.join(i['id'] for i in short_form(bank, b))}")
    print()
    personas = json.loads((HERE / "personas.json").read_text())
    rule_based_test(bank, personas)
    if "--write-md" in sys.argv:
        write_md(bank)


if __name__ == "__main__":
    main()
