"""Faithfulness test for method D's extractor: does each reading come from what the person said?

A reading is one piece of evidence the extractor took from an answer, for example
"horizon 4-6 years" or "willingness 0.8". A judge model from a different company (default:
Nemotron 3.5 Super, NVIDIA; the extractor is GLM, the simulated users are DeepSeek) decides
if the answer supports the reading, and must quote the words that support it. Code then
checks that the quote really is in the answer, so the judge can't invent support either.

Readings about the question's own topic ("asked") are reported apart from readings the
extractor took from other parts of the answer ("volunteered"), where made-up facts are
most likely.

  python check_extractor.py results/pilot_extract_eval.jsonl        # pilot.py extract-eval output
  python check_extractor.py results/experiment.jsonl --sample 300   # D and DR turns of a run
"""

import argparse
import json
import random
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import config as C
import methods as M
import retrieval
import run_bakeoff as R
from llm import extract_json

JUDGE_SYSTEM = (
    "You check one reading of a person's interview answer. The reading is supported only if "
    "the answer states it or clearly implies it. For a number range, the answer must give a "
    "value inside the range, or words that clearly mean such a value. For a score from 0 to 1, "
    "the answer must say something about that topic, and the score must be a fair reading of it "
    "(within about 0.25). Reply with ONE JSON object and nothing else: "
    '{"supported": true or false, "quote": "<the shortest exact words from the answer that '
    'support the reading, or empty>"}')
JUDGE_MESSAGE = 'Question: {question}\nAnswer: "{answer}"\nReading: {reading}'
ITEMS = {i["id"]: i for i in M.load_bank()["items"]}


def describe(kind, name, v):
    if kind == "fact":
        lo, hi = v["range"]
        if name == "income_stability":
            word = {0.0: "unstable", 0.33: "partly commission-based", 0.67: "stable", 1.0: "very stable"}
            return f"{M.FACT_TEXT[name]}: {word.get(round(lo, 2), lo)}"
        if name == "debt_to_income":
            return f"{M.FACT_TEXT[name]}: between {lo:.0%} and {hi:.0%} of income"
        return f"{M.FACT_TEXT[name]}: between {lo:g} and {hi:g}"
    if kind == "willingness":
        return (f"how they say they feel about risk: {v['score']} on a scale where 0.1 = very "
                "cautious, 0.5 = some risk for some growth, 0.9 = wants maximum growth")
    when = "something that actually happened" if v.get("kind") == "past" else "what they think they would do"
    return (f"what they do in a real loss: {v['score']} on a scale where 0.1 = sells everything, "
            f"0.3 = sells a good part, 0.5 = sells a little, mostly holds, 0.7 = holds calmly, "
            f"0.9 = buys more; this describes {when}")


def readings(ev, reader, question, answer, item_id, source):
    """Split one evidence object into separate readings."""
    out = []
    if not isinstance(ev, dict) or "facts" not in ev:
        return out
    asked_topic = retrieval.topic(ITEMS[item_id])
    for name, v in ev["facts"].items():
        out.append(("fact", name, v))
    for d in ("willingness", "behavioral"):
        if ev.get(d):
            out.append((d, d, ev[d]))
    return [{"reader": reader, "source": source, "question": question, "answer": answer,
             "kind": k, "name": n, "asked": n == asked_topic, "reading": describe(k, n, v)}
            for k, n, v in out]


def load(path):
    recs = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    rows = []
    for r in recs:
        if "D" in r and "DR" in r:   # pilot.py extract-eval output
            for reader in ("D", "DR"):
                rows += readings(r[reader], reader, r["question"], r["answer"], r["item"], r["persona_id"])
        elif r.get("method") in ("D", "DR") and not r.get("error"):
            for t in r["turns"]:
                rows += readings(t.get("evidence"), r["method"], t["q"], t["a"], t["item"], r["persona_id"])
    return rows


def norm(text):
    text = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip(" .,!?\"'")


def judge(llm, key, row, setting="off"):
    msgs = [{"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": JUDGE_MESSAGE.format(**row)}]
    r = llm.chat(key, msgs, setting, 4000 if setting != "off" else 400, 0.0)
    obj = extract_json(r["text"])
    if not isinstance(obj, dict) or not isinstance(obj.get("supported"), bool):
        return {**row, "verdict": "judge failed"}
    quote = str(obj.get("quote") or "")
    found = bool(quote.strip()) and norm(quote) in norm(row["answer"])
    verdict = ("not supported" if not obj["supported"]
               else "supported" if found else "supported, quote not found")
    return {**row, "verdict": verdict, "quote": quote}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--judge", default="nemotron-3.5-super", choices=sorted(C.MODELS))
    ap.add_argument("--sample", type=int, default=0, help="judge a random sample of this many readings")
    ap.add_argument("--setting", default="low", help="judge thinking: low (default) or off. Off agreed with itself on only 85%% of readings")
    ap.add_argument("--tag", default="", help="suffix for the output files, to keep repeated checks apart")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    if C.MODELS[args.judge]["family"] == C.MODELS[C.EXPERIMENT_INTERVIEWER]["family"]:
        raise SystemExit("The judge must come from a different company than the extractor.")
    R.load_env()
    llm = R.make_llm(args.mock)
    rows = load(args.file)
    if args.sample and args.sample < len(rows):
        rows = random.Random(0).sample(rows, args.sample)
    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        judged = list(ex.map(lambda r: judge(llm, args.judge, r, args.setting), rows))

    groups = defaultdict(list)
    for j in judged:
        groups[(j["reader"], "asked" if j["asked"] else "volunteered", j["kind"])].append(j["verdict"])
    lines = [f"# Extractor faithfulness: {Path(args.file).name} ({len(judged)} readings, judge {args.judge})", "",
             "| reader | topic | reading | n | not supported | quote not found | judge failed |",
             "|---|---|---|---|---|---|---|"]
    for key in sorted(groups):
        v = groups[key]
        pct = lambda s: f"{100 * v.count(s) / len(v):.0f}%"  # noqa: E731
        lines.append(f"| {' | '.join(key)} | {len(v)} | {pct('not supported')} | "
                     f"{pct('supported, quote not found')} | {pct('judge failed')} |")
    lines += ["", "not supported: the judge found no support in the answer. quote not found: the judge "
              "said supported but its quote is not in the answer, so the support is unverified."]
    bad = [j for j in judged if j["verdict"] == "not supported"][:8]
    if bad:
        lines += ["", "Examples of unsupported readings:", ""]
        lines += [f'- {j["reader"]}, {j["name"]}: "{j["reading"]}" from answer "{j["answer"][:160]}"' for j in bad]
    text = "\n".join(lines) + "\n"
    out = Path(args.file).with_name(Path(args.file).stem + f"_faithfulness{args.tag}.md")
    if not args.mock:
        out.write_text(text)
        out.with_suffix(".jsonl").write_text("".join(json.dumps(j) + "\n" for j in judged))
        print(f"Saved {out.name}")
    print(text)


if __name__ == "__main__":
    main()
