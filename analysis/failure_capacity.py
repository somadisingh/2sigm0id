"""Failure analysis: why is method D's capacity error higher than C's? (No API calls.)

python -m analysis.failure_capacity results/experiment_full.jsonl > results/failure_capacity.txt

1. Capacity error and bias by method, budget and noise level.
2. Each money fact: the engine's final estimate against the truth, as weighted sub-score
   error (the part of the capacity error each fact causes), for D and C.
3. Each spoken fact reading in D: does its range hold the true value? Split by the noise
   injected on that turn, so reading errors and injected false facts are separated.
"""
import json
import sys
from collections import defaultdict
from statistics import mean

import belief as BE
import capacity as K
import methods as M

BANK = {i["id"]: i for i in M.load_bank()["items"]}
FACT_SUB = {"horizon_yrs": "horizon", "emergency_fund_months": "emergency",
            "income_stability": "income", "debt_to_income": "debt", "dependents": "dependents"}
SPOKEN = ("D", "DR", "DN")


def noise_level(pid):
    # not score.noise_level: the old placeholder users (S1 to S5) must stay out of the three groups
    return pid.rsplit("-", 1)[-1] if pid.rsplit("-", 1)[-1] in ("clean", "moderate", "heavy") else "other"


def true_value(fin, fact):
    v = fin[fact]
    return K.INCOME_SCORE[v] if fact == "income_stability" else float(v)


def sub(fact, v):
    """The 0-1 sub-score of one fact value (income is already a sub-score)."""
    f = {"horizon_yrs": 20, "emergency_fund_months": 12, "income_stability": "stable",
         "debt_to_income": 0.0, "dependents": 0}
    if fact == "income_stability":
        return v
    f[fact] = v
    return K.sub_scores(f)[FACT_SUB[fact]]


def replay(r):
    m = r["method"]
    b = BE.Belief(channel="spoken" if m in SPOKEN else "form")
    for k, t in enumerate(r["turns"]):
        item = BANK[t["item"]]
        if m in SPOKEN:
            M.apply_evidence(b, t["evidence"], k)
        elif m == "DP":
            q = (t["evidence"] or {}).get("option_probs")
            if q:
                b.observe_soft(item, q, k)
        else:
            b.observe_option(item, t["option"])
    return b


def fact_means(b):
    return {f: float((BE.FACT_GRIDS[f] * b.fact[f]).sum()) for f in BE.FACTS}


def part1(runs, out):
    out.append("## 1. Capacity error (mean |estimate - truth|) and bias (mean estimate - truth)")
    for bu in (5, 10, 15):
        out.append(f"budget {bu}:")
        for m in ("A", "C", "D", "DR", "DN", "DP", "D0"):
            rs = [r for r in runs if r["method"] == m and int(r["budget"]) == bu]
            line = []
            for lv in ("clean", "moderate", "heavy"):
                g = [r for r in rs if noise_level(r["persona_id"]) == lv]
                line.append(f"{lv} {mean(abs(r['final_profile']['capacity'] - r['truth']['capacity']) for r in g):.3f}")
            err = mean(abs(r["final_profile"]["capacity"] - r["truth"]["capacity"]) for r in rs)
            bias = mean(r["final_profile"]["capacity"] - r["truth"]["capacity"] for r in rs)
            out.append(f"   {m:3} error {err:.3f}  bias {bias:+.3f}  | " + ", ".join(line))


def part2(runs, out):
    out.append("\n## 2. Each fact's share of the capacity error (weight x |sub-score of estimate - sub-score of truth|)")
    out.append("   'asked' = share of runs where the fact's own question was asked at least once")
    for bu in (10, 15):
        for lv in ("all", "clean", "heavy"):
            out.append(f"budget {bu}, {lv} users:")
            for m in ("C", "D"):
                rs = [r for r in runs if r["method"] == m and int(r["budget"]) == bu
                      and (lv == "all" or noise_level(r["persona_id"]) == lv)]
                contrib, bias, asked = defaultdict(list), defaultdict(list), defaultdict(list)
                for r in rs:
                    est = fact_means(replay(r))
                    fin = r["persona"]["finances"]
                    items = {t["item"] for t in r["turns"]}
                    for f in BE.FACTS:
                        w = K.WEIGHTS[FACT_SUB[f]]
                        d = sub(f, est[f]) - sub(f, true_value(fin, f))
                        contrib[f].append(w * abs(d))
                        bias[f].append(w * d)
                        asked[f].append(any(BANK[i].get("fact") == f for i in items))
                total = sum(mean(v) for v in contrib.values())
                out.append(f"   {m}: sum {total:.3f} | " + "; ".join(
                    f"{f} {mean(contrib[f]):.3f} (bias {mean(bias[f]):+.3f}, asked {mean(asked[f]):.0%})"
                    for f in BE.FACTS))


def part3(runs, out):
    out.append("\n## 3. D's spoken fact readings: does the read range hold the true value?")
    out.append("   own = the reading came from the fact's own question; other = read from an answer to another question")
    rows = defaultdict(lambda: defaultdict(lambda: [0, 0, []]))
    examples = defaultdict(list)
    for r in runs:
        if r["method"] != "D":
            continue
        fin = r["persona"]["finances"]
        for t in r["turns"]:
            facts = (t["evidence"] or {}).get("facts") or {}
            for f, v in facts.items():
                lo, hi = v["range"]
                tv = true_value(fin, f)
                tol = {"horizon_yrs": 0.5, "emergency_fund_months": 0.25, "debt_to_income": 0.005,
                       "dependents": 0.1, "income_stability": 0.01}[f]
                hit = lo - tol <= tv <= hi + tol
                own = BANK[t["item"]].get("fact") == f
                tgt = t.get("contradiction_target") or {}
                corr = t.get("correction") or {}
                if tgt.get("fact") == f:
                    kind = "contradiction aimed at this fact"
                elif corr.get("fact") == f and corr.get("phase") == "wrong":
                    kind = "planned mistake on this fact"
                elif corr.get("fact") == f and corr.get("phase") == "fix":
                    kind = "correction of this fact"
                elif {"vague", "flip"} & set(t["noise"]):
                    kind = "vague/flip on this turn"
                elif t["noise"]:
                    kind = "other noise (" + ",".join(sorted(set(t["noise"]))) + ")"
                else:
                    kind = "no noise"
                key = "own" if own else "other"
                cell = rows[kind][key]
                cell[0] += 1
                cell[1] += hit
                d = sub(f, (lo + hi) / 2) - sub(f, tv)
                cell[2].append(K.WEIGHTS[FACT_SUB[f]] * d)
                if not hit and kind == "no noise" and len(examples[f]) < 4:
                    examples[f].append((r["persona_id"], t["item"], fin[f], [lo, hi], t["a"][:220]))
    for kind in sorted(rows, key=lambda k: -sum(c[0] for c in rows[k].values())):
        parts = []
        for key in ("own", "other"):
            n, h, ds = rows[kind][key]
            if n:
                parts.append(f"{key}: {n} readings, {100 * h / n:.0f}% hold the truth, weighted bias {mean(ds):+.4f}")
        out.append(f"   {kind}: " + " | ".join(parts))
    out.append("\n   By fact, no-noise turns only:")
    by_fact = defaultdict(lambda: [0, 0, []])
    for r in runs:
        if r["method"] != "D":
            continue
        fin = r["persona"]["finances"]
        for t in r["turns"]:
            if t["noise"] or t.get("contradiction_target") or t.get("correction"):
                continue
            for f, v in ((t["evidence"] or {}).get("facts") or {}).items():
                lo, hi = v["range"]
                tv = true_value(fin, f)
                c = by_fact[f]
                c[0] += 1
                c[1] += (lo - 1e-6 <= tv <= hi + 1e-6) or abs((lo + hi) / 2 - tv) <= {"horizon_yrs": 0.5, "emergency_fund_months": 0.25, "debt_to_income": 0.005, "dependents": 0.1, "income_stability": 0.01}[f]
                c[2].append((lo + hi) / 2 - tv)
    for f, (n, h, ds) in by_fact.items():
        out.append(f"   {f}: {n} readings, {100 * h / n:.0f}% hold the truth, mean (reading - truth) {mean(ds):+.3f}")
    out.append("\n   Examples of misses on no-noise turns:")
    for f, ex in examples.items():
        for pid, item, tv, rng, a in ex[:2]:
            out.append(f"   {f} {pid} {item}: true {tv}, read {rng}: \"{a}\"")


def main(path):
    runs = [json.loads(line) for line in open(path)]
    runs = [r for r in runs if not r.get("error") and r.get("final_profile")]
    out = [f"D capacity failure analysis on {path}: {len(runs)} runs"]
    part1(runs, out)
    part2(runs, out)
    part3(runs, out)
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
