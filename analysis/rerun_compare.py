"""Tests 9 and 10 in ablations.md (Nov 22): score the reruns against the full run. No API calls.

python -m analysis.rerun_compare > results/rerun_compare.txt

Test 9: the engine changes (results/rerun_engine.jsonl against results/experiment_full.jsonl).
Test 10: noise version 3 (D in results/rerun_fixslips.jsonl against D in rerun_engine).
All comparisons are paired on the same test user, budget and repeat. U054 is left out.
"""
from analysis.common import BUDGETS, R, cap, err, exact, heavy, level, load, pair, stop_lines


def main():
    full = load("experiment_full.jsonl")
    eng = load("rerun_engine.jsonl")
    out = ["## Test 9: engine changes (rerun_engine - full run; negative = rerun better)"]
    for m in ("C", "D", "DN"):
        for bu in BUDGETS:
            out.append(f"{m} b{bu}: avg error {level(full, m, bu, err)} -> {level(eng, m, bu, err)}, "
                       f"diff {pair(eng, full, m, m, bu, err)}")
            out.append(f"      capacity {level(full, m, bu, cap)} -> {level(eng, m, bu, cap)}, diff {pair(eng, full, m, m, bu, cap)}; "
                       f"exact band {pair(eng, full, m, m, bu, exact)}")
    out.append("\nStop rule in the rerun (promise: under 5%); full run for comparison:")
    for m in ("C", "D"):
        out += stop_lines(eng, m)
        out += [s.replace("   ", "   (full run) ", 1) for s in stop_lines(full, m)]
    out.append("\nAgainst A from the full run (A is not affected by the changes):")
    for m in ("C", "D"):
        for bu in BUDGETS:
            out.append(f"   {m} - A b{bu}: avg error {pair(eng, full, m, 'A', bu, err)}; exact {pair(eng, full, m, 'A', bu, exact)}")
    out.append("   D - C (both reruns) " + "; ".join(f"b{bu} {pair(eng, eng, 'D', 'C', bu, err)}" for bu in BUDGETS))

    if (R / "rerun_fixslips.jsonl").exists():
        fx = load("rerun_fixslips.jsonl")
        out.append("\n## Test 10: noise version 3 (D fixslips - D rerun_engine; negative = fixslips better)")
        for bu in BUDGETS:
            out.append(f"D b{bu}: avg error {level(eng, 'D', bu, err)} -> {level(fx, 'D', bu, err)}, diff {pair(fx, eng, 'D', 'D', bu, err)}")
            out.append(f"      capacity {level(eng, 'D', bu, cap)} -> {level(fx, 'D', bu, cap)}, diff {pair(fx, eng, 'D', 'D', bu, cap)}; "
                       f"heavy users capacity {pair(fx, eng, 'D', 'D', bu, cap, heavy)}; exact {pair(fx, eng, 'D', 'D', bu, exact)}")
        out.append("\nD with noise version 3 against the forms (forms get no false facts in any version):")
        for bu in BUDGETS:
            out.append(f"   D(v3) - C(rerun) b{bu}: {pair(fx, eng, 'D', 'C', bu, err)}; D(v3) - A(full) b{bu}: "
                       f"{pair(fx, full, 'D', 'A', bu, err)}; exact vs A {pair(fx, full, 'D', 'A', bu, exact)}")
        n = sum(1 for r in fx.values() for t in r["turns"] if (t.get("correction") or {}).get("on_reask"))
        out.append(f"   re-ask corrections in noise version 3: {n}")
        out += stop_lines(fx, "D")
    print("\n".join(out))


if __name__ == "__main__":
    main()
