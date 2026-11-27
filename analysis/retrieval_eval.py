"""Ablation test 11 (a), Nov 22: how close are the labels of the retrieved examples to the
answer's own label? BM25 against embedding search against random examples, on the 290
labeled pilot answers. Never uses examples from the same pilot user. No API calls.

python -m analysis.retrieval_eval > results/retrieval_eval.txt
"""
import random
from collections import defaultdict
from statistics import mean

import retrieval

K = 3
# label scale for each topic, so every distance is on a 0 to 1 scale
SPAN = {"horizon_yrs": 30, "emergency_fund_months": 12, "debt_to_income": 1, "dependents": 4}


def label(e):
    g = e["gold"]
    return g.get("score", g.get("value"))


def dist(a, b):
    la, lb = label(a), label(b)
    if a["topic"] == "income_stability":
        return float(la != lb)
    if isinstance(la, (int, float)) and isinstance(lb, (int, float)):
        return min(1.0, abs(la - lb) / SPAN.get(a["topic"], 1))
    return float(la != lb)


def main():
    bm, em = retrieval.Pool.load(search="bm25"), retrieval.Pool.load(search="embedding")
    rng = random.Random(0)
    res = defaultdict(lambda: defaultdict(list))
    for e in bm.entries:
        is_fact = e["topic"] != e["dimension"]
        item = {"fact": e["topic"]} if is_fact else {"dimension": e["dimension"]}
        group = "money facts" if is_fact else e["dimension"]
        others = [o for o in bm.entries if o["topic"] == e["topic"] and o["persona_id"] != e["persona_id"]]
        picks = {"bm25": bm.similar(item, e["question"], e["answer"], K, e["persona_id"]),
                 "embedding": em.similar(item, e["question"], e["answer"], K, e["persona_id"]),
                 "random": rng.sample(others, min(K, len(others)))}
        for name, ex in picks.items():
            if ex:
                d = mean(dist(e, o) for o in ex)
                res[group][name].append(d)
                res["all"][name].append(d)
                res[group][name + " top1"].append(dist(e, ex[0]))
        res[group]["same top example"].append(float(picks["bm25"][0] is picks["embedding"][0]
                                                    or picks["bm25"][0]["answer"] == picks["embedding"][0]["answer"]))
    print(f"Label distance of the {K} retrieved examples (0 = same label, lower is better)\n")
    for g in ("money facts", "willingness", "behavioral", "all"):
        r = res[g]
        if not r:
            continue
        line = f"{g:12} n={len(r['bm25']):3}: " + ", ".join(f"{n} {mean(r[n]):.3f}" for n in ("random", "bm25", "embedding"))
        if g != "all":
            line += f" | best example only: bm25 {mean(r['bm25 top1']):.3f}, embedding {mean(r['embedding top1']):.3f}" \
                    f" | same best example {100 * mean(r['same top example']):.0f}%"
        print(line)


if __name__ == "__main__":
    main()
