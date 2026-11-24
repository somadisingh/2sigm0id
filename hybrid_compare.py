"""Test 14 (Nov 24): the hybrid CW, money facts on the form and attitudes in conversation. No API calls.

python hybrid_compare.py > results/hybrid_compare.txt

CW in results/rerun_hybrid.jsonl, paired on test user, budget and repeat (U054 left out) with
C, D (rerun_engine.jsonl) and DW v2 (rerun_written_v2.jsonl), all with the old band rule.
CW - C: talking about attitudes with the same fact input. CW - DW: hearing the money facts in
conversation instead of on a form. Ranges resample whole test users.
"""
from statistics import mean

import config as C
from nl_benefits import RUNS, all_err, att_err, dim_err, schedule
from rerun_compare import BUDGETS, exact, load, pair, stop_lines
from score import noise_level

CW = load("rerun_hybrid.jsonl")
ALL = {**RUNS, **CW}


def main():
    print("# Test 14: hybrid CW. Negative = CW has less error (exact band: + = CW better).")
    groups = [("all", lambda r: True), ("no noise drawn", lambda r: not schedule(r)),
              ("clean test users", lambda r: noise_level(r["persona"]) == "clean"),
              ("heavy test users", lambda r: noise_level(r["persona"]) == "heavy")]
    for other in ("C", "DW", "D"):
        print(f"\n## CW - {other}")
        for bu in BUDGETS:
            print(f"b{bu}:")
            for name, keep in groups:
                print(f"   {name:>17}: avg error {pair(ALL, ALL, 'CW', other, bu, all_err, keep)}")
                if name == "all":
                    print(f"   {'':>17}  capacity {pair(ALL, ALL, 'CW', other, bu, dim_err('capacity'))}")
                    print(f"   {'':>17}  attitudes {pair(ALL, ALL, 'CW', other, bu, att_err)}")
                    print(f"   {'':>17}  exact band {pair(ALL, ALL, 'CW', other, bu, exact)}")
                else:
                    print(f"   {'':>17}  attitudes {pair(ALL, ALL, 'CW', other, bu, att_err, keep)}")

    print("\n## Levels (avg error | capacity | attitudes)")
    for m in ("C", "CW", "DW", "D"):
        for bu in BUDGETS:
            rs = [r for (mm, x, _, _), r in ALL.items() if mm == m and x == bu]
            print(f"{m} b{bu}: {mean(map(all_err, rs)):.3f} | {mean(map(dim_err('capacity'), rs)):.3f} | "
                  f"{mean(map(att_err, rs)):.3f}  (n={len(rs)})")

    print("\n## Form questions per CW interview")
    for bu in BUDGETS:
        rs = [r for (m, x, _, _), r in CW.items() if x == bu]
        print(f"b{bu}: {mean(sum(t['form'] for t in r['turns']) for r in rs):.2f} form, "
              f"{mean(sum(not t['form'] for t in r['turns']) for r in rs):.2f} conversation, "
              f"{mean(sum(t['reask'] for t in r['turns']) for r in rs):.2f} re-asks")

    print("\n## Stop rule (old band rule)")
    print("\n".join(stop_lines(CW, "CW")))

    print("\n## System cost and time per interview (test users not counted)")
    for m in ("C", "CW", "D", "DW"):
        rs = [r for (mm, x, _, _), r in ALL.items() if mm == m]
        usd = mean(sum((c["usage"]["in"] * C.MODELS[c.get("model") or r["interviewer"]]["price_in"]
                        + c["usage"]["out"] * C.MODELS[c.get("model") or r["interviewer"]]["price_out"]) / 1e6
                       for c in r["interviewer_calls"]) for r in rs)
        secs = mean(sum(t["system_latency"] + t["engine_secs"] for t in r["turns"]) / len(r["turns"]) for r in rs)
        print(f"{m}: ${usd:.4f} per interview (list price), {secs:.2f} s per question")


if __name__ == "__main__":
    main()
