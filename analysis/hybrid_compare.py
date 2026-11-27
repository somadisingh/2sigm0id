"""Tests 14 and 15 (Nov 24): the hybrids CW and CWF (money facts first). No API calls.

python -m analysis.hybrid_compare > results/hybrid_compare.txt              # test 14: CW
python -m analysis.hybrid_compare CWF > results/hybrid_compare_ff.txt       # test 15: CWF, also against CW
python -m analysis.hybrid_compare CF > results/hybrid_compare_cf.txt        # test 16: CF, and CWF - CF

CW in results/rerun_hybrid.jsonl, paired on test user, budget and repeat (U054 left out) with
C, D (rerun_engine.jsonl) and DW v2 (rerun_written_v2.jsonl), all with the old band rule.
CW - C: talking about attitudes with the same fact input. CW - DW: hearing the money facts in
conversation instead of on a form. Ranges resample whole test users.
"""
import sys
from statistics import mean

import config as C
from analysis.nl_benefits import RUNS, all_err, att_err, dim_err, schedule
from analysis.rerun_compare import BUDGETS, exact, load, pair, stop_lines
from score import noise_level

H = sys.argv[1] if len(sys.argv) > 1 else "CW"
CW = load("rerun_hybrid.jsonl")
CWF = load("rerun_hybrid_ff.jsonl") if H in ("CWF", "CF") else {}
CF = load("rerun_form_ff.jsonl") if H == "CF" else {}
ALL = {**RUNS, **CW, **CWF, **CF}
HR = {"CW": CW, "CWF": CWF, "CF": CF}[H]
PAIRS = {"CW": [("CW", o) for o in ("C", "DW", "D")],
         "CWF": [("CWF", o) for o in ("C", "CW", "DW", "D")],
         "CF": [("CF", "C"), ("CWF", "CF"), ("CF", "CW"), ("CF", "DW")]}[H]
LEVELS = {"CW": ("C", "CW", "DW", "D"), "CWF": ("C", "CW", "CWF", "DW", "D"),
          "CF": ("C", "CF", "CW", "CWF", "DW", "D")}[H]


def main():
    print(f"# {H}. Negative = the first method has less error (exact band: + = first better).")
    groups = [("all", lambda r: True), ("no noise drawn", lambda r: not schedule(r)),
              ("clean test users", lambda r: noise_level(r["persona"]) == "clean"),
              ("heavy test users", lambda r: noise_level(r["persona"]) == "heavy")]
    for first, other in PAIRS:
        print(f"\n## {first} - {other}")
        for bu in BUDGETS:
            print(f"b{bu}:")
            for name, keep in groups:
                print(f"   {name:>17}: avg error {pair(ALL, ALL, first, other, bu, all_err, keep)}")
                if name == "all":
                    print(f"   {'':>17}  capacity {pair(ALL, ALL, first, other, bu, dim_err('capacity'))}")
                    print(f"   {'':>17}  attitudes {pair(ALL, ALL, first, other, bu, att_err)}")
                    print(f"   {'':>17}  exact band {pair(ALL, ALL, first, other, bu, exact)}")
                else:
                    print(f"   {'':>17}  attitudes {pair(ALL, ALL, first, other, bu, att_err, keep)}")

    print("\n## Levels (avg error | capacity | attitudes)")
    for m in LEVELS:
        for bu in BUDGETS:
            rs = [r for (mm, x, _, _), r in ALL.items() if mm == m and x == bu]
            print(f"{m} b{bu}: {mean(map(all_err, rs)):.3f} | {mean(map(dim_err('capacity'), rs)):.3f} | "
                  f"{mean(map(att_err, rs)):.3f}  (n={len(rs)})")

    print(f"\n## Form questions per {H} interview")
    for bu in BUDGETS:
        rs = [r for (m, x, _, _), r in HR.items() if x == bu]
        print(f"b{bu}: {mean(sum(t['form'] for t in r['turns']) for r in rs):.2f} form, "
              f"{mean(sum(not t['form'] for t in r['turns']) for r in rs):.2f} conversation, "
              f"{mean(sum(t['reask'] for t in r['turns']) for r in rs):.2f} re-asks")

    print("\n## Stop rule (old band rule)")
    print("\n".join(stop_lines(HR, H)))

    print("\n## System cost and time per interview (test users not counted)")
    for m in LEVELS:
        rs = [r for (mm, x, _, _), r in ALL.items() if mm == m]
        usd = mean(sum((c["usage"]["in"] * C.MODELS[c.get("model") or r["interviewer"]]["price_in"]
                        + c["usage"]["out"] * C.MODELS[c.get("model") or r["interviewer"]]["price_out"]) / 1e6
                       for c in r["interviewer_calls"]) for r in rs)
        secs = mean(sum(t["system_latency"] + t["engine_secs"] for t in r["turns"]) / len(r["turns"]) for r in rs)
        print(f"{m}: ${usd:.4f} per interview (list price), {secs:.2f} s per question")


if __name__ == "__main__":
    main()
