"""Where does talking help? (instructor feedback on Milestone 3, Nov 24). No API calls.

python nl_benefits.py > results/nl_benefits.txt

Compares the conversation methods (D, DN, DW v2) with the adaptive form (C) on the runs we
already have, paired on test user, budget and repeat (U054 left out):
  1. error per dimension: capacity is where the spoken methods meet false money facts that a
     form never sees; willingness and behavior get the same kind of input in both
  2. error by the noise the test user's schedule had (the same draws for every method)
  3. what the re-asks do (D against DN, and band fixes on re-ask turns)
  4. how often D flags a planted contradiction
  5. system cost and time (the test users' calls are not counted)
"""
import random
import zlib
from statistics import mean

import config as C
import run_bakeoff as RB
from rerun_compare import BUDGETS, load, low_band, pair
from score import noise_level

ATT = ("willingness", "behavioral")
ENGINE = load("rerun_engine.jsonl")
DW = load("rerun_written_v2.jsonl")
RUNS = {**ENGINE, **DW}


def dim_err(d):
    return lambda r: abs(r["final_profile"][d] - r["truth"][d])


def att_err(r):
    return mean(abs(r["final_profile"][d] - r["truth"][d]) for d in ATT)


def all_err(r):
    return mean(abs(r["final_profile"][d] - r["truth"][d]) for d in ("capacity",) + ATT)


_SCHED = {}


def schedule(r):
    """The noise kinds drawn for this test user, repeat and budget, before any method
    filters them (methods.run_form draws them from the same seeded stream)."""
    key = (r["persona_id"], r["repeat"], r["budget"])
    if key not in _SCHED:
        rng = random.Random(zlib.crc32(f"{r['persona_id']}|{r['repeat']}".encode()))
        _SCHED[key] = {k for t in range(r["budget"]) for k in RB.draw_noise(rng, r["persona"], t)}
    return _SCHED[key]


def has(kind):
    return lambda r: kind in schedule(r)


def false_fact(r):
    return any(t.get("contradiction_target") or (t.get("correction") or {}).get("phase") == "wrong"
               for t in r["turns"])


def section(title):
    print(f"\n## {title}")


def main():
    print("# Where does talking help? Negative = the first method has less error.")
    print("Runs: C, D, DN in rerun_engine.jsonl; DW in rerun_written_v2.jsonl (both use the old band rule).")

    section("1. Error per dimension, method - C")
    for m in ("D", "DW"):
        for bu in BUDGETS:
            parts = [f"{d[:4]} {pair(RUNS, RUNS, m, 'C', bu, dim_err(d))}" for d in ("capacity",) + ATT]
            print(f"{m} b{bu}: " + "; ".join(parts))
            print(f"   attitudes only (willingness + behavior): {pair(RUNS, RUNS, m, 'C', bu, att_err)}")

    section("2. By the noise in the test user's schedule (method - C, avg error over 3 dims | attitudes only)")
    groups = [("no noise drawn", lambda r: not schedule(r)), ("vague", has("vague")), ("flip", has("flip")),
              ("contradiction", has("contradiction")), ("acquiescence", has("acquiescence"))]
    for lvl in ("clean", "moderate", "heavy"):
        groups.append((f"{lvl} test users", lambda r, lvl=lvl: noise_level(r["persona"]) == lvl))
    for m in ("D", "DW"):
        for bu in BUDGETS:
            print(f"{m} b{bu}:")
            for name, keep in groups:
                print(f"   {name:>20}: {pair(RUNS, RUNS, m, 'C', bu, all_err, keep)} | "
                      f"{pair(RUNS, RUNS, m, 'C', bu, att_err, keep)}")

    section("3. What the re-asks do")
    for bu in BUDGETS:
        print(f"D - DN b{bu}: all dims {pair(RUNS, RUNS, 'D', 'DN', bu, all_err)}; "
              f"capacity {pair(RUNS, RUNS, 'D', 'DN', bu, dim_err('capacity'))}; "
              f"runs with a false fact {pair(RUNS, RUNS, 'D', 'DN', bu, all_err, false_fact)}")
    for m in ("D", "DW"):
        for bu in BUDGETS:
            rs = [r for (mm, x, _, _), r in RUNS.items() if mm == m and x == bu]
            fixed = broke = same = n = 0
            for r in rs:
                for i, t in enumerate(r["turns"]):
                    if not t["reask"]:
                        continue
                    n += 1
                    after = r["turns"][i + 1]["profile_before"] if i + 1 < len(r["turns"]) else r["final_profile"]
                    truth = r["truth"]["final_band"]
                    was, now = low_band(t["profile_before"]) == truth, low_band(after) == truth
                    fixed += (not was) and now
                    broke += was and not now
                    same += was == now
            print(f"{m} b{bu}: {n} re-asks in {len(rs)} runs ({n / len(rs):.2f} per run); final band "
                  f"wrong->right {fixed}, right->wrong {broke}, no change {same}")

    section("4. Planted false facts and contradictions: does the interviewer flag them?")
    for m in ("D", "DW"):
        for bu in BUDGETS:
            rs = [r for (mm, x, _, _), r in RUNS.items() if mm == m and x == bu]
            planted = [r for r in rs if any(t.get("contradiction_target") for t in r["turns"])]
            clean = [r for r in rs if not false_fact(r)]
            flagged = lambda r: any(f.startswith("contradiction") for t in r["turns"] for f in t["flags_after"])
            print(f"{m} b{bu}: contradiction planted in {len(planted)} runs, flagged in "
                  f"{sum(map(flagged, planted))} ({mean(map(flagged, planted)) if planted else 0:.0%}); "
                  f"runs with no false fact flagged anyway: {sum(map(flagged, clean))} of {len(clean)}")

    section("5. System cost and time per interview (test users not counted)")
    for m in ("C", "D", "DN", "DW"):
        rs = [r for (mm, x, _, _), r in RUNS.items() if mm == m]
        usd = mean(sum((c["usage"]["in"] * C.MODELS[c.get("model") or r["interviewer"]]["price_in"]
                        + c["usage"]["out"] * C.MODELS[c.get("model") or r["interviewer"]]["price_out"]) / 1e6
                       for c in r["interviewer_calls"]) for r in rs)
        secs = mean(sum(t["system_latency"] + t["engine_secs"] for t in r["turns"]) / len(r["turns"]) for r in rs)
        calls = mean(len(r["interviewer_calls"]) / len(r["turns"]) for r in rs)
        print(f"{m}: ${usd:.4f} per interview (list price), {secs:.2f} s per question, {calls:.2f} AI calls per question")


if __name__ == "__main__":
    main()
