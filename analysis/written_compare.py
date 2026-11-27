"""Ablation test 12 (Nov 22): AI-written questions (DW) against bank wording (D).

python -m analysis.written_compare [--judge-sample 300] > results/written_compare.txt

Accuracy: DW in results/rerun_written.jsonl against D in results/rerun_engine.jsonl, paired
on test user, budget and repeat (same engine, same noise schedule). U054 is left out.
Leading questions: a judge from another company (Nemotron 3.5 Super, NVIDIA) reads the bank
wording and the written wording of the same sampled questions, each on its own, and says if
the question hints at an answer. About $0.10.
"""
import argparse
import json
import random
import re
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

import config as C
import methods as M
import run_bakeoff as RB
from llm import extract_json, strip_think
from analysis.rerun_compare import BUDGETS, err, exact, load, pair, level, stop_lines

BANK = {i["id"]: i for i in M.load_bank()["items"]}
JUDGE_SYSTEM = (
    "You check one question from an interview about how a person invests. Say if the question "
    "is leading: it suggests, hints at or pushes toward a particular answer (for example by "
    "giving an example answer, assuming an answer, or showing which answer is good). A question "
    "that only asks, even in a friendly way, is not leading. Reply with ONE JSON object and "
    'nothing else: {"leading": true or false, "why": "<a few words>"}')


# openings that restate an earlier answer ("Since you're leaning toward growth, ..."), test 12
RESTATE_RE = re.compile(r"^(since|given|sticking with|that fits|so (protecting|growth|safety|you)|with (that|your)|"
                        r"you've|you'?re|as you|because you|keeping (that|in mind))", re.I)
LEADING_RE = re.compile(r'^\s*(?:\{?\s*"leading"\s*:\s*)?(true|false)\b', re.I)


def judge(llm, key, q, setting, tries=3):
    """True/False, or None if the judge gives no usable answer in `tries` calls. Some replies
    lose their first characters ('false, "why": ...'), so a bare true/false at the start counts."""
    for _ in range(tries):
        # one user message: with a separate system message, this judge often replied that
        # it could not see the question (Nov 23)
        r = llm.chat(key, [{"role": "user", "content": f"{JUDGE_SYSTEM}\n\nThe question to check: {q}"}],
                     setting, 4000 if setting != "off" else 400, 0.0)
        obj = extract_json(r["text"])
        if isinstance(obj, dict) and isinstance(obj.get("leading"), bool):
            return obj["leading"]
        m = LEADING_RE.match(strip_think(r["text"]) or "")
        if m:
            return m.group(1).lower() == "true"
    return None


def cost(rs):
    """List-price dollars per interview, all models."""
    tot = 0.0
    for r in rs:
        for c, default in [(c, r["interviewer"]) for c in r["interviewer_calls"]] + [(c, r["user"]) for c in r["user_calls"]]:
            m = C.MODELS[c.get("model") or default]
            tot += (c["usage"]["in"] * m["price_in"] + c["usage"]["out"] * m["price_out"]) / 1e6
    return tot / len(rs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="rerun_written.jsonl", help="DW run to score (test 12b: rerun_written_v2.jsonl)")
    ap.add_argument("--judge-sample", type=int, default=300)
    ap.add_argument("--judge", default="nemotron-3.5-super")
    ap.add_argument("--setting", default="low")
    args = ap.parse_args()
    eng, dw = load("rerun_engine.jsonl"), load(args.file)
    out = [f"## AI-written questions, {args.file} (DW - D; negative = DW better)"]
    for bu in BUDGETS:
        out.append(f"b{bu}: avg error D {level(eng, 'D', bu, err)} -> DW {level(dw, 'DW', bu, err)}, "
                   f"diff {pair(dw, eng, 'DW', 'D', bu, err)}; exact band {pair(dw, eng, 'DW', 'D', bu, exact)}")
    acq = lambda r: any("acquiescence" in (t.get("noise") or []) for t in r["turns"])  # noqa: E731
    out.append("\nTest users with acquiescence noise in the run (they go along with hints):")
    for bu in BUDGETS:
        out.append(f"   b{bu}: {pair(dw, eng, 'DW', 'D', bu, err, acq)}")
    out.append("\nAgainst the forms (rerun C):")
    for bu in BUDGETS:
        out.append(f"   DW - C b{bu}: {pair(dw, eng, 'DW', 'C', bu, err)}")
    out.append("\nStop rule:")
    out += stop_lines(dw, "DW")
    for name, runs, m in (("D", eng, "D"), ("DW", dw, "DW")):
        rs = [r for (mm, _, _, _), r in runs.items() if mm == m]
        secs = mean(t["system_latency"] for r in rs for t in r["turns"])
        out.append(f"{name}: ${cost(rs):.4f} per interview (list price), {secs:.2f} s of system time per question, "
                   f"{mean(len(r['interviewer_calls']) for r in rs) / mean(len(r['turns']) for r in rs):.2f} system calls per question")
    if args.file != "rerun_written.jsonl":
        v1 = load("rerun_written.jsonl")
        out.append("\nAgainst DW version 1 (this run - v1; negative = this run better):")
        for bu in BUDGETS:
            out.append(f"   b{bu}: avg error {pair(dw, v1, 'DW', 'DW', bu, err)}; acquiescence users "
                       f"{pair(dw, v1, 'DW', 'DW', bu, err, acq)}; exact {pair(dw, v1, 'DW', 'DW', bu, exact)}")
    written = [(BANK[t["item"]]["spoken"], t["q"]) for r in dw.values() for t in r["turns"] if not t["reask"]]
    out.append(f"written questions: {len(written)}, same as the bank wording: "
               f"{sum(a == b for a, b in written)}; open by restating an earlier answer (code check): "
               f"{100 * mean(bool(RESTATE_RE.match(b)) for _, b in written):.1f}%")
    if args.judge_sample:
        rng = random.Random(0)
        sample = rng.sample(written, min(args.judge_sample, len(written)))
        llm = RB.make_llm(False)
        with ThreadPoolExecutor(max_workers=8) as ex:
            bank_j = list(ex.map(lambda x: judge(llm, args.judge, x[0], args.setting), sample))
            dw_j = list(ex.map(lambda x: judge(llm, args.judge, x[1], args.setting), sample))
        ok = [(a, b) for a, b in zip(bank_j, dw_j) if a is not None and b is not None]
        out.append(f"\nLeading questions (judge {args.judge}, {len(ok)} of {len(sample)} sampled questions judged):")
        out.append(f"   bank wording flagged {100 * mean(a for a, _ in ok):.1f}%, written wording flagged {100 * mean(b for _, b in ok):.1f}%")
        out.append(f"   written flagged but bank not: {sum(b and not a for a, b in ok)}; bank flagged but written not: {sum(a and not b for a, b in ok)}")
        flagged = [s for s, (a, b) in zip(sample, zip(bank_j, dw_j)) if b and not a][:8]
        out += [f"   e.g. BANK: {x[0]}\n        DW:   {x[1]}" for x in flagged]
    print("\n".join(out))


if __name__ == "__main__":
    main()
