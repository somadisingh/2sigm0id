"""Ablation test 13 (Nov 22): one band rule everywhere. Replays the engine on the recorded
answers of results/rerun_engine.jsonl (C and D) and finds the first turn where the stop rule
fires, with BAND_RULE "mode" (as run; a check that the replay matches the record) and
"reported" (the new rule). No API calls.

python -m analysis.band_rule_replay > results/band_rule_replay.txt
python -m analysis.band_rule_replay rerun_hybrid_ff.jsonl CWF > results/band_rule_replay_cwf.txt   # Nov 24
python -m analysis.band_rule_replay rerun_form_ff.jsonl CF > results/band_rule_replay_cf.txt
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from statistics import mean

import belief as BE
import methods as M
from analysis.common import EXCLUDE, R, low_band

BANK = M.load_bank()
POOL = M.engine_pool(BANK)
ITEMS = {i["id"]: i for i in BANK["items"]}


def stop_turn(r, rule):
    """The first turn where the engine (with BAND_RULE = rule) calls the band settled.
    Follows methods.run_form for C, CF, D, CW and CWF."""
    BE.BAND_RULE = rule
    method, budget = r["method"], int(r["budget"])
    hybrid = method in ("CW", "CWF")
    facts_first = min(5, budget // 2) if method in ("CWF", "CF") else 0
    b = BE.Belief(channel="spoken" if method in ("D", "CW", "CWF") else "form")
    if hybrid:
        b.form_dims = M.HYBRID_FORM_DIMS
    asks, unclear = {}, {}
    for k, t in enumerate(r["turns"]):
        cands = M.candidates(POOL, asks, unclear, k, method == "D" or hybrid, hybrid, facts_first)
        _, info = b.choose(cands, budget - k, seed=k)
        if info["settled"]:
            return k
        item = ITEMS[t["item"]]
        asks[item["id"]] = asks.get(item["id"], 0) + 1
        if method == "D" or (hybrid and not t["form"]):
            ev = t["evidence"] or dict(M.NO_EVIDENCE)
            flags = M.apply_evidence(b, ev, k)
            M.update_unclear(unclear, item, ev, flags, POOL)
        else:
            b.observe_option(item, t["option"])
    return None


def one(r):
    return r["method"], int(r["budget"]), r["would_stop_at"], stop_turn(r, "mode"), stop_turn(r, "reported"), r


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "rerun_engine.jsonl"
    methods = tuple(sys.argv[2:]) or ("C", "D")
    runs = [json.loads(x) for x in open(R / name)]
    runs = [r for r in runs if r["method"] in methods and not r.get("error") and r["persona_id"] not in EXCLUDE]
    with ProcessPoolExecutor() as ex:
        res = list(ex.map(one, runs, chunksize=8))
    print(f"Stop point replayed on the recorded answers of {name} ({', '.join(methods)}, U054 left out)\n")
    for m in methods:
        for bu in (5, 10, 15):
            rows = [x for x in res if x[0] == m and x[1] == bu]
            match = mean(x[2] == x[3] for x in rows)
            line = [f"{m} b{bu}: replay with 'mode' matches the recorded stop point in {100 * match:.0f}% of {len(rows)} runs"]
            for name, col in (("mode", 3), ("reported", 4)):
                fired = [x for x in rows if x[col] is not None and x[col] < bu]
                if not fired:
                    line.append(f"   {name:8}: stop never fired")
                    continue
                ch = [low_band(x[5]["turns"][x[col]]["profile_before"]) != low_band(x[5]["final_profile"]) for x in fired]
                saved = sum(bu - x[col] for x in fired) / len(rows)
                line.append(f"   {name:8}: fired in {len(fired)}/{len(rows)}, band changes after the stop in "
                            f"{100 * mean(ch):.1f}%, {saved:.2f} questions saved per run")
            print("\n".join(line))


if __name__ == "__main__":
    main()
