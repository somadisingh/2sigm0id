"""Helpers shared by the scripts in analysis/: load recorded runs and compare methods on them.

A run is one interview: one method, one budget (5, 10 or 15 questions), one test user and one
repeat. load() keys every run by those four values, so two methods can be compared on exactly the
same test users ("paired"). Nothing here calls an AI model.
"""
import json
from pathlib import Path
from statistics import mean

from prompts import band
from score import DIMS, bootstrap_ci

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"   # results/ is not in git: the run files are made by run_bakeoff.py
# test users that failed 2 or more persona checks (only U054); left out of every comparison
EXCLUDE = set(json.loads((ROOT / "mirofish" / "persona_checks_exclude.json").read_text()))
BUDGETS = (5, 10, 15)


def load(name):
    out = {}
    for line in open(R / name):
        r = json.loads(line)
        if r.get("error") or not r.get("final_profile") or r["persona_id"] in EXCLUDE:
            continue
        out[(r["method"], int(r["budget"]), r["persona_id"], r["repeat"])] = r
    return out


def profile_error(p, t):
    """Avg error of a profile p against the true scores t: mean |estimate - truth| over the three scores."""
    return mean(abs(p[d] - t[d]) for d in DIMS)


def err(r):
    return profile_error(r["final_profile"], r["truth"])


def dim_err(d):   # error on one score, for example dim_err("capacity")
    return lambda r: abs(r["final_profile"][d] - r["truth"][d])


def cap(r):
    return abs(r["final_profile"]["capacity"] - r["truth"]["capacity"])


def low_band(p):   # the final band: the lowest of the three bands
    return min(band(p[d]) for d in DIMS)


def exact(r):
    return float(low_band(r["final_profile"]) == r["truth"]["final_band"])


def heavy(r):
    return r["persona_id"].endswith("-heavy")


def false_fact(r):   # the test user stated a wrong money fact somewhere in this run
    return any(t.get("contradiction_target") or (t.get("correction") or {}).get("phase") == "wrong"
               for t in r["turns"])


def pair(a, b, ma, mb, bu, f, keep=lambda r: True):
    """f(method ma) - f(method mb) on the same test users and repeats, with a 95% range.
    CLEAR means the range does not include 0. Runs come from a (for ma) and b (for mb)."""
    keys = [(pid, rep, r) for (m, x, pid, rep), r in a.items()
            if m == ma and x == bu and keep(r) and (mb, bu, pid, rep) in b]
    d = [f(r) - f(b[(mb, bu, pid, rep)]) for pid, rep, r in keys]
    if not d:
        return "no pairs"
    lo, hi = bootstrap_ci(d, groups=[pid for pid, _, _ in keys])   # resample test users
    clear = "CLEAR" if lo > 0 or hi < 0 else "not clear"
    return f"{mean(d):+.3f} ({lo:+.3f} to {hi:+.3f}, n={len(d)}, {clear})"


def level(runs, m, bu, f, keep=lambda r: True):   # mean of f over one method and budget
    v = [f(r) for (mm, x, _, _), r in runs.items() if mm == m and x == bu and keep(r)]
    return f"{mean(v):.3f}" if v else "-"


def stop_lines(runs, m):
    """How often the stop rule fired, and how often the band changed after it (the promise: under 5%)."""
    out = []
    for bu in BUDGETS:
        rs = [r for (mm, x, _, _), r in runs.items() if mm == m and x == bu]
        fired = [r for r in rs if r["would_stop_at"] is not None and r["would_stop_at"] < len(r["turns"])]
        if not fired:
            out.append(f"   {m} b{bu}: stop never fired")
            continue
        ch = [low_band(r["turns"][r["would_stop_at"]]["profile_before"]) != low_band(r["final_profile"]) for r in fired]
        saved = sum(bu - r["would_stop_at"] for r in fired) / len(rs)
        out.append(f"   {m} b{bu}: fired in {len(fired)}/{len(rs)}, band changes after the stop in "
                   f"{100 * mean(ch):.1f}%, {saved:.1f} questions saved per run")
    return out
