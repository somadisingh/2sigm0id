"""Failure analysis, parts 2 to 4 (no API calls). Part 1 (D's capacity) is failure_capacity.py.

python failure_more.py results/experiment_full_excl.jsonl > results/failure_more.txt

2. Why D and DR are worst on heavy-noise users.
3. Why D0 (the LLM keeps the scores itself) gets worse as the conversation gets longer.
4. Why the stop rule misses its promise (band changes after the stop point in under 5% of runs).
"""
import json
import sys
from collections import defaultdict
from statistics import mean

import numpy as np

import belief as BE
import methods as M
from prompts import band
from score import DIMS, bootstrap_ci

BANK = {i["id"]: i for i in M.load_bank()["items"]}
SPOKEN = ("D", "DR", "DN")


def level(r):
    return r["persona_id"].rsplit("-", 1)[-1]


def err(p, t):
    return mean(abs(p[d] - t[d]) for d in DIMS)


def low_band(p):
    return min(band(p[d]) for d in DIMS)


def false_fact(r):
    return any(t.get("contradiction_target") or (t.get("correction") or {}).get("phase") == "wrong"
               for t in r["turns"])


def ci(xs):
    lo, hi = bootstrap_ci(xs)
    return f"{mean(xs):+.3f} ({lo:+.3f} to {hi:+.3f})"


def part2(runs, out):
    out.append("## 2. Heavy-noise users")
    out.append("Error per dimension by noise level (mean |estimate - truth|):")
    for bu in (10, 15):
        for m in ("A", "C", "D", "DR", "DN", "D0"):
            parts = []
            for lv in ("clean", "moderate", "heavy"):
                g = [r for r in runs if r["method"] == m and r["budget"] == bu and level(r) == lv]
                parts.append(f"{lv} " + "/".join(f"{mean(abs(r['final_profile'][d] - r['truth'][d]) for r in g):.3f}"
                                                for d in DIMS) + f" (avg {mean(err(r['final_profile'], r['truth']) for r in g):.3f})")
            out.append(f"   budget {bu} {m:3}: " + "; ".join(parts) + "   [capacity/willingness/behavior]")
    out.append("\nNoise turns per run on heavy users (budget 15):")
    for m in ("C", "D"):
        c = defaultdict(list)
        g = [r for r in runs if r["method"] == m and r["budget"] == 15 and level(r) == "heavy"]
        for r in g:
            kinds = defaultdict(int)
            for t in r["turns"]:
                for k in t["noise"]:
                    kinds[k] += 1
            for k in ("vague", "flip", "contradiction", "correction", "acquiescence", "refuses_numbers"):
                c[k].append(kinds[k])
        out.append(f"   {m}: " + ", ".join(f"{k} {mean(v):.2f}" for k, v in c.items()))
    out.append("\nD and DR on heavy users, split by a false fact (contradiction or planned mistake) in the run:")
    for m in ("D", "DR"):
        for bu in (10, 15):
            g = [r for r in runs if r["method"] == m and r["budget"] == bu and level(r) == "heavy"]
            for name, sel in (("with false fact", [r for r in g if false_fact(r)]),
                              ("without", [r for r in g if not false_fact(r)])):
                if sel:
                    out.append(f"   {m} b{bu} {name}: {len(sel)} runs, avg {mean(err(r['final_profile'], r['truth']) for r in sel):.3f}, "
                               + ", ".join(f"{d} {mean(abs(r['final_profile'][d] - r['truth'][d]) for r in sel):.3f}" for d in DIMS))
    out.append("\nPaired D - C on heavy users (same user and repeat), per dimension; negative = D better:")
    for bu in (10, 15):
        idx = {(r["persona_id"], r["repeat"]): r for r in runs if r["method"] == "C" and r["budget"] == bu}
        g = [(r, idx[(r["persona_id"], r["repeat"])]) for r in runs
             if r["method"] == "D" and r["budget"] == bu and level(r) == "heavy"]
        out.append(f"   budget {bu}: " + "; ".join(
            f"{d} {ci([abs(a['final_profile'][d] - a['truth'][d]) - abs(b['final_profile'][d] - b['truth'][d]) for a, b in g])}"
            for d in DIMS))
        gf = [(a, b) for a, b in g if not false_fact(a)]
        out.append(f"      without false fact in D's run ({len(gf)} pairs): " + "; ".join(
            f"{d} {ci([abs(a['final_profile'][d] - a['truth'][d]) - abs(b['final_profile'][d] - b['truth'][d]) for a, b in gf])}"
            for d in DIMS))


def part3(runs, out):
    out.append("\n## 3. D0 gets worse in longer conversations")
    out.append("Error and bias per dimension by budget (bias = mean estimate - truth):")
    for bu in (5, 10, 15):
        g = [r for r in runs if r["method"] == "D0" and r["budget"] == bu]
        out.append(f"   budget {bu}: avg {mean(err(r['final_profile'], r['truth']) for r in g):.3f}; " + "; ".join(
            f"{d} {mean(abs(r['final_profile'][d] - r['truth'][d]) for r in g):.3f} (bias {mean(r['final_profile'][d] - r['truth'][d] for r in g):+.3f})"
            for d in DIMS))
    out.append("\nInside the same 15-question D0 conversations: the profile the LLM held after question k")
    g = [r for r in runs if r["method"] == "D0" and r["budget"] == 15]
    for k in (3, 5, 8, 10, 12):
        ps = [(r["turns"][k]["profile_before"], r["truth"]) for r in g if len(r["turns"]) > k]
        out.append(f"   after {k} answers: avg {mean(err(p, t) for p, t in ps):.3f}; " + "; ".join(
            f"{d} {mean(abs(p[d] - t[d]) for p, t in ps):.3f} (bias {mean(p[d] - t[d] for p, t in ps):+.3f})" for d in DIMS))
    out.append(f"   final (15 answers): avg {mean(err(r['final_profile'], r['truth']) for r in g):.3f}")
    out.append("\nD0 at 15 questions by true band of each dimension (bias = estimate - truth):")
    for d in DIMS:
        rows = defaultdict(list)
        for r in g:
            rows[band(r["truth"][d])].append(r["final_profile"][d] - r["truth"][d])
        out.append(f"   {d}: " + ", ".join(f"band {b} {mean(v):+.3f} (n={len(v)})" for b, v in sorted(rows.items())))
    out.append("\nD0 at 15 by noise level: " + ", ".join(
        f"{lv} {mean(err(r['final_profile'], r['truth']) for r in g if level(r) == lv):.3f}" for lv in ("clean", "moderate", "heavy")))
    out.append("D0 at 5 by noise level:  " + ", ".join(
        f"{lv} {mean(err(r['final_profile'], r['truth']) for r in runs if r['method'] == 'D0' and r['budget'] == 5 and level(r) == lv):.3f}"
        for lv in ("clean", "moderate", "heavy")))
    # how far scores move per answer: does D0 over-react late?
    out.append("\nD0 at 15: mean |change of a score after one answer|, by question number:")
    steps = defaultdict(list)
    for r in g:
        ps = [t["profile_before"] for t in r["turns"]] + [r["final_profile"]]
        for k in range(1, len(ps)):
            steps[k].append(mean(abs(ps[k][d] - ps[k - 1][d]) for d in DIMS))
    out.append("   " + ", ".join(f"q{k} {mean(v):.3f}" for k, v in sorted(steps.items())))
    sat = [mean(float(r["final_profile"][d] in (0.0, 0.05, 0.1, 0.9, 0.95, 1.0)) for d in DIMS) for r in g]
    out.append(f"   share of final scores at an extreme (<=0.1 or >=0.9): {mean(sat):.0%}; truth: "
               f"{mean(mean(float(r['truth'][d] <= 0.1 or r['truth'][d] >= 0.9) for d in DIMS) for r in g):.0%}")


def replay_to(r, k):
    """Belief after the first k turns of a recorded run (same evidence as in the run)."""
    m = r["method"]
    b = BE.Belief(channel="spoken" if m in SPOKEN else "form")
    for j, t in enumerate(r["turns"][:k]):
        item = BANK[t["item"]]
        if m in SPOKEN:
            M.apply_evidence(b, t["evidence"], j)
        else:
            b.observe_option(item, t["option"])
    return b


def part4(runs, out):
    out.append("\n## 4. The stop rule")
    out.append("At the stop point the engine said: under 5% chance that the rest of the budget changes its most "
               "likely final band. We check the promise with the engine's own band (most likely band of the "
               "final-band distribution) and with the scored band (lowest of the three bands of the mean scores).")
    for m in ("C", "D"):
        for bu in (10, 15):
            g = [r for r in runs if r["method"] == m and r["budget"] == bu and r["would_stop_at"] is not None
                 and r["would_stop_at"] < len(r["turns"])]
            own, scored, noise_after, calib, same_def = [], [], [], [], []
            for r in g:
                k = r["would_stop_at"]
                b_stop, b_end = replay_to(r, k), replay_to(r, len(r["turns"]))
                pmf_s, pmf_e = b_stop.final_pmf(b_stop.band_pmfs()), b_end.final_pmf(b_end.band_pmfs())
                top_s = int(np.argmax(pmf_s)) + 1
                own.append(top_s != int(np.argmax(pmf_e)) + 1)
                scored.append(low_band(r["turns"][k]["profile_before"]) != low_band(r["final_profile"]))
                noise_after.append(any(t["noise"] for t in r["turns"][k:]))
                calib.append((float(pmf_s.max()), top_s == r["truth"]["final_band"]))
                same_def.append(top_s == low_band(r["turns"][k]["profile_before"]))
            na = [o for o, n in zip(own, noise_after) if n]
            nn = [o for o, n in zip(own, noise_after) if not n]
            out.append(f"   {m} b{bu}: {len(g)} stops. Band changes after the stop: engine's own band {mean(own):.1%}, "
                       f"scored band {mean(scored):.1%}. Engine band = scored band at the stop in {mean(same_def):.0%}.")
            out.append(f"      engine's band changed: with noise after the stop {mean(na):.1%} (n={len(na)}), "
                       f"no noise after {mean(nn) if nn else 0:.1%} (n={len(nn)})")
            conf = mean(c for c, _ in calib)
            acc = mean(float(h) for _, h in calib)
            out.append(f"      at the stop, engine's chance for its top band {conf:.0%} on average; that band is the "
                       f"true final band in {acc:.0%}")


def main(path):
    runs = [json.loads(x) for x in open(path)]
    runs = [r for r in runs if not r.get("error") and r.get("final_profile")]
    for r in runs:
        r["budget"] = int(r["budget"])
    out = [f"Failure analysis parts 2-4 on {path}: {len(runs)} runs"]
    part2(runs, out)
    part3(runs, out)
    part4(runs, out)
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
