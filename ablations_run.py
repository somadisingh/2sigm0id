"""Run the ablation tests in ablations.md on the full-run results (no new API calls).

python ablations_run.py results/experiment_full.jsonl > results/ablations.txt

Tests 1 to 6 compare recorded runs. Test 7 replays the recorded answers through the belief
engine with the starting evidence strengths. Test 8 is not run: ablations.md says it is not
needed when N_ROLLOUTS is 400 before the run, and it was (belief.py).
"""
import csv
import json
import sys
from collections import defaultdict
from statistics import mean

import belief as BE
import methods as M
from prompts import band
from score import DIMS, bootstrap_ci

BUDGETS = (5, 10, 15)
BANK = {i["id"]: i for i in M.load_bank()["items"]}


def err(p, t):
    return mean(abs(p[d] - t[d]) for d in DIMS)


def final_band(p):
    return min(band(p[d]) for d in DIMS)


def load(path):
    runs = {}
    for line in open(path):
        r = json.loads(line)
        if r.get("error") or not r.get("final_profile"):
            continue
        runs[(r["method"], int(r["budget"]), r["persona_id"], r["repeat"])] = r
    return runs


def paired(runs, a, b, budget, f, keep=lambda r: True):
    """Mean of f(run of a) - f(run of b) on the same user and repeat, with a 95% range."""
    diffs = []
    for (m, bu, pid, rep), r in runs.items():
        if m != a or bu != budget or not keep(r):
            continue
        o = runs.get((b, budget, pid, rep))
        if o:
            diffs.append(f(r) - f(o))
    lo, hi = bootstrap_ci(diffs)
    return len(diffs), mean(diffs) if diffs else None, lo, hi


def fmt(n, d, lo, hi, pct=False):
    if d is None:
        return "no pairs"
    k = 100 if pct else 1
    s = f"{d * k:+.1f} points" if pct else f"{d:+.3f}"
    rng = f"{lo * k:+.1f} to {hi * k:+.1f}" if pct else f"{lo:+.3f} to {hi:+.3f}"
    clear = "CLEAR" if lo is not None and (lo > 0 or hi < 0) else "not clear"
    return f"{s} ({rng}, n={n}, {clear})"


E = lambda r: err(r["final_profile"], r["truth"])  # noqa: E731
EXACT = lambda r: float(final_band(r["final_profile"]) == r["truth"]["final_band"])  # noqa: E731
dim_err = lambda d: (lambda r: abs(r["final_profile"][d] - r["truth"][d]))  # noqa: E731


def summary(path):
    rows = {}
    for r in csv.DictReader(open(path.replace(".jsonl", "_summary.csv"))):
        rows[(r["model"], int(r["setting"]))] = r
    return rows


def heavy(r):
    return r["persona_id"].endswith("-heavy")


def test_compare(runs, title, a, b, extra=()):
    out = [f"\n## {title}: {a} - {b} (negative = {a} better)"]
    for bu in BUDGETS:
        out.append(f"budget {bu}: avg error {fmt(*paired(runs, a, b, bu, E))}; "
                   f"band exact {fmt(*paired(runs, a, b, bu, EXACT), pct=True)}")
        for name, f, keep in extra:
            out.append(f"   {name}: {fmt(*paired(runs, a, b, bu, f, keep))}")
    return out


def cost_lines(summ, methods):
    out = []
    for bu in BUDGETS:
        parts = []
        for m in methods:
            s = summ[(m, bu)]
            parts.append(f"{m} ${float(s['sys_cost']):.4f}/profile, {float(s['sys_secs_per_turn']):.2f} s/turn")
        out.append(f"budget {bu}: " + "; ".join(parts))
    return out


def test5(runs):
    """Profile at the stop point against the profile at the end of the budget."""
    out = ["\n## Test 5: what the stop rule costs (profile at would_stop_at vs end of budget)"]
    for m in ("C", "D"):
        for bu in BUDGETS:
            rs = [r for (mm, b, _, _), r in runs.items() if mm == m and b == bu]
            fired = [r for r in rs if r["would_stop_at"] is not None]
            stop_p = []
            for r in rs:
                k = r["would_stop_at"]
                p = r["turns"][k]["profile_before"] if k is not None and k < len(r["turns"]) else r["final_profile"]
                stop_p.append(p)
            changed = [final_band(p) != final_band(r["final_profile"]) for p, r in zip(stop_p, rs)
                       if r["would_stop_at"] is not None]
            ex_stop = mean(final_band(p) == r["truth"]["final_band"] for p, r in zip(stop_p, rs))
            ex_end = mean(EXACT(r) for r in rs)
            e_stop = mean(err(p, r["truth"]) for p, r in zip(stop_p, rs))
            e_end = mean(E(r) for r in rs)
            saved = mean(bu - r["would_stop_at"] for r in fired) if fired else 0
            out.append(
                f"{m} budget {bu}: stop fired in {len(fired)}/{len(rs)} runs"
                + (f" at q{mean(r['would_stop_at'] for r in fired):.1f}" if fired else "")
                + f"; band changed after the stop point in {100 * mean(changed) if changed else 0:.1f}% of fired runs"
                + f"; band exact {100 * ex_stop:.0f}% at stop vs {100 * ex_end:.0f}% at end"
                + f"; avg error {e_stop:.3f} vs {e_end:.3f}; questions saved {saved:.1f} per fired run")
    return out


def replay(r):
    """The recorded answers of one run, read again by a fresh belief engine."""
    m = r["method"]
    bank = BANK
    b = BE.Belief(channel="spoken" if m in ("D", "DR", "DN") else "form")
    for k, t in enumerate(r["turns"]):
        item = bank[t["item"]]
        if m in ("D", "DR", "DN"):
            M.apply_evidence(b, t["evidence"], k)
        elif m == "DP":
            q = (t["evidence"] or {}).get("option_probs")
            if q:
                b.observe_soft(item, q, k)
        else:
            b.observe_option(item, t["option"])
    return b.profile()


# Spoken settings fitted on the pilot users but not adopted (pilot/fit.md, Nov 12). The run
# used the starting spoken values, so for D, DR and DN test 7 replays with these instead.
SPOKEN_FITTED = {"spoken_sigma": {"stated": 0.125, "hypothetical": 0.075, "past": 0.1},
                 "spoken_lapse": 0.1, "fact_miss": 0.152}
SPOKEN = ("D", "DR", "DN")


def replay_all(runs, methods, values, source):
    as_run = BE.settings()
    BE.use(values, source)
    try:
        return {(m, bu, pid, rep): err(replay(r), r["truth"])
                for (m, bu, pid, rep), r in runs.items() if m in methods}
    finally:
        BE.use(as_run, as_run["source"])


def test7(runs):
    out = ["\n## Test 7: evidence strengths as run vs other values (same recorded answers)",
           "As run: form values fitted on the pilot users (pilot/fitted.json); spoken values = starting",
           "values (the spoken fit was not adopted, pilot/fit.md). So: A, B, C, DP are replayed with the",
           "starting form values; D, DR, DN with the fitted spoken values that were not adopted."]
    methods = ("A", "B", "C", "D", "DR", "DP", "DN")
    sample = [r for (m, b, _, rep), r in runs.items() if m in methods and rep == 0 and b == 10][:70]
    worst = max(max(abs(replay(r)[d] - r["final_profile"][d]) for d in DIMS) for r in sample)
    out.append(f"replay check with the run's values on {len(sample)} runs: largest difference {worst:.4f}")
    other = replay_all(runs, [m for m in methods if m not in SPOKEN], BE.STARTING, "starting guesses")
    other.update(replay_all(runs, SPOKEN, SPOKEN_FITTED, "spoken fitted, not adopted"))
    for bu in BUDGETS:
        out.append(f"budget {bu}:")
        run_order, alt_order = [], []
        for m in methods:
            keys = [k for k in other if k[0] == m and k[1] == bu]
            f_ = mean(E(runs[k]) for k in keys)
            s_ = mean(other[k] for k in keys)
            lo, hi = bootstrap_ci([other[k] - E(runs[k]) for k in keys])
            label = "spoken fitted" if m in SPOKEN else "starting form"
            out.append(f"   {m}: as run {f_:.3f}, {label} {s_:.3f}, change {s_ - f_:+.3f} ({lo:+.3f} to {hi:+.3f})")
            run_order.append((f_, m))
            alt_order.append((s_, m))
        out.append("   order as run:      " + " < ".join(m for _, m in sorted(run_order)))
        out.append("   order other values: " + " < ".join(m for _, m in sorted(alt_order)))
    return out


def main(path):
    runs = load(path)
    summ = summary(path)
    out = [f"Ablation tests on {path}: {len(runs)} runs"]
    out += test_compare(runs, "Test 1: what the belief engine adds", "D", "D0")
    out += cost_lines(summ, ("D", "D0"))
    out += test_compare(runs, "Test 2: what conversation adds", "D", "C",
                        [("willingness error", dim_err("willingness"), lambda r: True),
                         ("behavior error", dim_err("behavioral"), lambda r: True),
                         ("capacity error", dim_err("capacity"), lambda r: True)])
    out += test_compare(runs, "Test 3: what the re-asks add", "D", "DN",
                        [("heavy-noise users, avg error", E, heavy),
                         ("clean and moderate users, avg error", E, lambda r: not heavy(r))])
    for bu in BUDGETS:
        parts = []
        for m in ("D", "DN"):
            s = summ[(m, bu)]
            parts.append(f"{m} caught {float(s['contradiction_caught'] or 0):.0%} of {s['contradiction_turns']} "
                         f"contradictions, recovered {float(s['contra_recovered'] or 0):.0%} of {s['contra_targeted']}")
        out.append(f"budget {bu}: " + "; ".join(parts))
    out += test_compare(runs, "Test 4a: retrieval", "DR", "D")
    out += test_compare(runs, "Test 4b: token probabilities", "DP", "D")
    out += cost_lines(summ, ("D", "DR", "DP"))
    out += test5(runs)
    out += test_compare(runs, "Test 6: capacity formula vs the LLM's own estimate", "D", "D0",
                        [("capacity error", dim_err("capacity"), lambda r: True),
                         ("capacity band exact (+ = D better)",
                          lambda r: float(band(r["final_profile"]["capacity"]) == band(r["truth"]["capacity"])),
                          lambda r: True)])
    out += test7(runs)
    out.append("\n## Test 8: not run. ablations.md: not needed when N_ROLLOUTS is 400 before the run "
               "(belief.py has N_ROLLOUTS = 400 since the Nov 12 review).")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
