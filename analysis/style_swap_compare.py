"""Style-swap test (plan.md, task S6): does the way a person talks change method D's result?

python -m analysis.style_swap_compare results/experiment_style_swap.jsonl results/experiment_full.jsonl

Each style-swap user is a copy of one of the 100 test users with only the `style` block changed
(mirofish/make_style_swap.py). Its noise is seeded the same way, so each run is paired with the
original's method D run at the same budget and repeat. No API calls.
"""
import json
import sys
from collections import defaultdict
from statistics import mean

from analysis.common import err, low_band
from score import DIMS, bootstrap_ci


def load(path, method="D"):
    out = {}
    for line in open(path):
        r = json.loads(line)
        if r.get("error") or not r.get("final_profile") or r["method"] != method:
            continue
        out[(r["persona_id"], int(r["budget"]), r["repeat"])] = r
    return out


def rng(xs, users=None):
    lo, hi = bootstrap_ci(xs, groups=users)
    clear = "CLEAR" if lo is not None and (lo > 0 or hi < 0) else "not clear"
    return f"{mean(xs):+.3f} ({lo:+.3f} to {hi:+.3f}, {clear})"


def main(swap_path, full_path):
    swap, full = load(swap_path), load(full_path)
    style_of = {}
    pairs = defaultdict(list)
    for (pid, bu, rep), s in swap.items():
        orig_id = s["persona"]["profile"]["style_swap_of"]
        o = full.get((orig_id, bu, rep))
        if o:
            pairs[bu].append((s, o))
            style_of[orig_id] = (o["persona"]["style"], s["persona"]["style"])
    out = [f"Style-swap test: {sum(len(v) for v in pairs.values())} paired method D runs "
           f"({len(style_of)} users). Differences are swap - original; negative = the swap is better."]
    out.append("\n| budget | pairs | avg error, original | avg error, swap | difference (95% range) "
               "| band exact, original / swap | final band differs |")
    out.append("|---|---|---|---|---|---|---|")
    for bu in sorted(pairs):
        ps = pairs[bu]
        diffs = [err(s) - err(o) for s, o in ps]
        ex_o = mean(low_band(o["final_profile"]) == o["truth"]["final_band"] for _, o in ps)
        ex_s = mean(low_band(s["final_profile"]) == s["truth"]["final_band"] for s, _ in ps)
        differs = mean(low_band(s["final_profile"]) != low_band(o["final_profile"]) for s, o in ps)
        out.append(f"| {bu} | {len(ps)} | {mean(err(o) for _, o in ps):.3f} | {mean(err(s) for s, _ in ps):.3f} "
                   f"| {rng(diffs, [o['persona_id'] for _, o in ps])} | {100 * ex_o:.0f}% / {100 * ex_s:.0f}% | {100 * differs:.0f}% |")
    out.append("\nBy dimension (all budgets): swap - original")
    allp = [p for v in pairs.values() for p in v]
    for d in DIMS:
        out.append(f"   {d}: {rng([abs(s['final_profile'][d] - s['truth'][d]) - abs(o['final_profile'][d] - o['truth'][d]) for s, o in allp], [o['persona_id'] for _, o in allp])}")
    out.append("\nBy the new style (all budgets): swap - original avg error")
    for field in ("verbosity", "vocabulary", "hedging"):
        groups = defaultdict(list)
        for s, o in allp:
            groups[s["persona"]["style"][field]].append(err(s) - err(o))
        out.append(f"   {field}: " + "; ".join(f"now {k}: {mean(v):+.3f} (n={len(v)})" for k, v in sorted(groups.items())))
    out.append("\nBaseline for comparison: the same original user's method D band also changes between "
               "repeats. Share of originals whose final band differs between repeat 0 and repeat 1:")
    for bu in sorted(pairs):
        ids = {o["persona_id"] for _, o in pairs[bu]}
        same_user = [(full.get((i, bu, 0)), full.get((i, bu, 1))) for i in ids]
        same_user = [(a, b) for a, b in same_user if a and b]
        out.append(f"   budget {bu}: {100 * mean(low_band(a['final_profile']) != low_band(b['final_profile']) for a, b in same_user):.0f}% "
                   f"of {len(same_user)} users")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
