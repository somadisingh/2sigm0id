"""Checks for the belief engine. Run: python test_belief.py (no API calls, a few seconds)."""

import json
import time
from pathlib import Path

import numpy as np

import belief as B
from capacity import INCOME_SCORE, capacity_from_facts
from methods import load_bank

HERE = Path(__file__).resolve().parent
BANK = load_bank()
ITEMS = {i["id"]: i for i in BANK["items"]}
POOL = [i for i in BANK["items"] if B.item_target(i) is not None]


def personas():
    out = json.loads((HERE / "personas.json").read_text())
    for f in ("mirofish/personas_100_with_backstories.json", "mirofish/personas_pilot.json"):
        if (HERE / f).exists():
            out += json.loads((HERE / f).read_text())
    return out


def test_formula_matches_capacity_py():
    for p in personas():
        f = p["finances"]
        got = B.capacity_vec(np.array([f["horizon_yrs"]]), np.array([f["emergency_fund_months"]]),
                             np.array([INCOME_SCORE[f["income_stability"]]]),
                             np.array([f["debt_to_income"]]), np.array([f["dependents"]]))[0]
        assert abs(got - capacity_from_facts(f)[0]) < 0.001, p["id"]


def test_known_facts_give_formula_capacity():
    """Every fact stated exactly -> the capacity estimate is the formula value."""
    for p in personas()[:20]:
        b = B.Belief()
        f = p["finances"]
        for fact in B.FACTS:
            v = INCOME_SCORE[f[fact]] if fact == "income_stability" else f[fact]
            for _ in range(3):
                b.observe_fact(fact, v, v)
        assert abs(b.profile()["capacity"] - p["ground_truth"]["capacity"]) < 0.02, p["id"]


def test_professors_example():
    """Says they like risk (willingness ~0.8) but behavior sits near the band 1/2 edge, and
    capacity is high. Behavior decides the band, so the engine should ask about behavior;
    another willingness question should be worth much less. With the starting settings
    (past actions = strongest evidence) the past-behavior question comes first."""
    fitted = B.settings()
    B.use(B.STARTING, "starting guesses")
    try:
        _professors_example(expect_past_first=True)
    finally:
        B.use(fitted, fitted["source"])
    _professors_example(expect_past_first=False)   # whatever settings are in use


def _professors_example(expect_past_first):
    b = B.Belief()
    for fact, v in (("horizon_yrs", 25), ("emergency_fund_months", 12), ("income_stability", 1.0),
                    ("debt_to_income", 0.0), ("dependents", 0)):
        b.observe_fact(fact, v, v)
    b.observe_option(ITEMS["WIL01"], 4)   # "willing to take chances" (0.75)
    b.observe_option(ITEMS["WIL09"], 5)   # strongly agree with losing years for growth (1.0)
    b.observe_option(ITEMS["BEH05"], 2)   # move some to cash (0.33)
    b.observe_option(ITEMS["BEH11"], 1)   # sell too (0.0)
    asked = {"WIL01", "WIL09", "BEH05", "BEH11", "CAP01", "CAP02", "CAP03", "CAP04", "CAP05"}
    cands = [i for i in POOL if i["id"] not in asked]
    best, info = b.choose(cands, left=6)
    s = b.score_items(cands)
    best_wil = max(s[i["id"]]["gain"] for i in cands if i["dimension"] == "willingness")
    assert best["dimension"] == "behavioral", (best["id"], info)
    if expect_past_first:
        assert best["id"] == "BEH02", (best["id"], info)
    assert s[best["id"]]["gain"] > 3 * best_wil, (s[best["id"]], best_wil)
    print(f"  professor's example ({B.SETTINGS_SOURCE}): asks {best['id']}, gain "
          f"{s[best['id']]['gain']:.3f} vs best willingness {best_wil:.3f}; most likely band "
          f"{info['top_band']} ({info['top_band_chance']:.0%}); mismatch chance {b.mismatch_chance():.0%}")


def test_contradiction_widens_then_clarifies():
    b = B.Belief()
    assert b.observe_fact("horizon_yrs", 20, 25, turn=0) == []
    b.observe_fact("emergency_fund_months", 6, 6, turn=1)
    assert b.observe_fact("horizon_yrs", 2, 3, turn=2) == [0], "should flag the contradiction"
    s = b.score_items([ITEMS["CAP01"], ITEMS["CAP02"]])
    assert s["CAP01"]["gain"] > s["CAP02"]["gain"], s   # re-asking the conflicting fact is worth more
    h = b.fact["horizon_yrs"]
    long_now = h[B.FACT_GRIDS["horizon_yrs"] >= 11].sum()
    assert 0.2 < long_now < 0.8, long_now   # both stories still possible
    b.observe_fact("horizon_yrs", 20, 25, turn=3)   # the clarifying answer
    long_after = b.fact["horizon_yrs"][B.FACT_GRIDS["horizon_yrs"] >= 11].sum()
    assert long_after > 0.95, long_after
    print(f"  contradiction: P(horizon 11+ years) {long_now:.2f} after the conflict, "
          f"{long_after:.2f} after the clarifying answer")


def test_corrected_statement_is_not_flagged_again():
    """A true story, a false one (flagged), then the true story again twice: only the
    false statement is flagged."""
    b = B.Belief()
    flags = [b.observe_score("behavioral", s, "past", turn=i) for i, s in enumerate((0.33, 1.0, 0.33, 0.2))]
    assert flags == [[], [0], [], []], flags


def test_soft_evidence():
    """DP's soft evidence: a sure reading acts like a form answer; a spread-out one moves the
    belief less; a reading of "never happened" moves nothing."""
    item = ITEMS["BEH07"]   # sell everything / sell part / hold / buy more
    sure, form, spread = B.Belief(), B.Belief(), B.Belief()
    sure.observe_soft(item, [1, 0, 0, 0])
    form.observe_option(item, 1)
    spread.observe_soft(item, [0.4, 0.3, 0.2, 0.1])
    m = lambda b: b.profile()["behavioral"]  # noqa: E731
    assert abs(m(sure) - m(form)) < 1e-6
    assert m(sure) < m(spread) < 0.5
    never = B.Belief()
    never.observe_soft(ITEMS["BEH02"], [0, 0, 0, 0, 1])
    assert abs(m(never) - 0.5) < 1e-6


def test_small_differences_are_not_contradictions():
    b = B.Belief()
    b.observe_fact("emergency_fund_months", 4, 4, turn=0)
    assert b.observe_fact("emergency_fund_months", 4, 6, turn=1) == []
    b.observe_fact("horizon_yrs", 10, 10, turn=2)
    assert b.observe_fact("horizon_yrs", 12, 15, turn=3) == []


def test_stop_rule():
    fresh = B.Belief()
    assert fresh.change_chance(POOL[:10]) > 0.3   # knowing nothing, the band can still move
    b = B.Belief()
    for fact, v in (("horizon_yrs", 30), ("emergency_fund_months", 12), ("income_stability", 1.0),
                    ("debt_to_income", 0.0), ("dependents", 0)):
        b.observe_fact(fact, v, v)
    for _ in range(4):
        b.observe_option(ITEMS["BEH11"], 1)     # always sells: behavior clearly band 1
    rest = [i for i in POOL if i["dimension"] != "capacity"][:5]
    p = b.change_chance(rest)
    assert p < B.STOP_CHANCE, p
    print(f"  stop rule: change chance {fresh.change_chance(POOL[:10]):.2f} at the start, "
          f"{p:.2f} once behavior is clearly band 1 (stops under {B.STOP_CHANCE})")


def test_gains_are_valid_and_fast():
    b = B.Belief()
    t = time.monotonic()
    best, info = b.choose(POOL, left=15)
    secs = time.monotonic() - t
    s = b.score_items(POOL)
    assert all(v["gain"] >= 0 and v["var_cut"] >= 0 for v in s.values())
    assert secs < 2, secs
    print(f"  first question with nothing known: {best['id']} ({info['phase']}), {secs * 1000:.0f} ms")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
