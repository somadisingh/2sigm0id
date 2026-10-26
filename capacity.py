"""Capacity formula: how much loss a person can afford, from their money facts alone.

One formula, used in three places:
  - setting each test user's TRUE capacity (personas.json), instead of a hand-picked number
  - scoring capacity in the form-based methods, once the team switches them over
  - the "collect facts, let the formula score" version of the interviewer (the capacity ablation)

How it works:
  1. Each fact becomes a 0-1 sub-score (higher = can afford more loss).
  2. A weighted average combines them.
  3. Weakest-link caps: some situations limit capacity no matter how good the rest looks.
     A plain average let P2's 30-year horizon hide that it has half a month of savings.

The weights and caps are our own judgment, written down so they can be argued with.
Change them here, rerun `python capacity.py`, and note the change in the shared contract.
"""

# 1. Sub-scores ---------------------------------------------------------------

HORIZON_FULL_YEARS = 20      # 20+ years until the money is needed = full marks
EMERGENCY_FULL_MONTHS = 12   # a year of expenses saved = full marks
DEBT_ZERO_SHARE = 0.40       # debt payments at 40% of income or more = zero marks
DEPENDENT_PENALTY = 0.25     # each dependent takes a quarter off, down to zero

INCOME_SCORE = {             # persona income descriptions -> 0-1
    "unstable": 0.0,
    "partly commission-based": 0.33,
    "stable": 0.67,
    "very stable": 1.0,
    "stable and high": 1.0,
}


def sub_scores(f):
    """f = a persona's "finances" block. Returns each fact's 0-1 sub-score."""
    income = f["income_stability"]
    if income not in INCOME_SCORE:
        raise ValueError(f"Unknown income_stability '{income}'. Add it to INCOME_SCORE in capacity.py.")
    return {
        "horizon": min(1.0, f["horizon_yrs"] / HORIZON_FULL_YEARS),
        "emergency": min(1.0, f["emergency_fund_months"] / EMERGENCY_FULL_MONTHS),
        "income": INCOME_SCORE[income],
        "debt": max(0.0, 1 - f["debt_to_income"] / DEBT_ZERO_SHARE),
        "dependents": max(0.0, 1 - DEPENDENT_PENALTY * f["dependents"]),
    }


# 2. Weights (sum to 1) -------------------------------------------------------
# Horizon matters most: money needed soon can't wait out a drop. Emergency savings
# next: without them, any surprise forces a sale at the worst time.
WEIGHTS = {"horizon": 0.30, "emergency": 0.25, "income": 0.20, "debt": 0.15, "dependents": 0.10}

# 3. Weakest-link caps --------------------------------------------------------
# (description, test, highest capacity allowed)
CAPS = [
    ("needs the money within 3 years", lambda f: f["horizon_yrs"] < 3, 0.20),
    ("less than 1 month of emergency savings", lambda f: f["emergency_fund_months"] < 1, 0.35),
    ("debt payments at 40% of income or more", lambda f: f["debt_to_income"] >= 0.40, 0.35),
]


def capacity_from_facts(f):
    """Returns (capacity 0-1, explanation dict)."""
    subs = sub_scores(f)
    raw = sum(WEIGHTS[k] * subs[k] for k in WEIGHTS)
    applied = [(why, cap) for why, test, cap in CAPS if test(f)]
    score = min([raw] + [cap for _, cap in applied])
    return round(score, 3), {"sub_scores": subs, "weighted": round(raw, 3),
                             "caps": [why for why, _ in applied]}


if __name__ == "__main__":
    import json
    from pathlib import Path

    assert abs(sum(WEIGHTS.values()) - 1) < 1e-9, "weights must sum to 1"
    personas = json.loads((Path(__file__).resolve().parent / "personas.json").read_text())
    print(f"{'persona':26} {'formula':>7} {'in file':>7}  sub-scores (horizon, emergency, income, debt, dependents)  caps")
    for p in personas:
        cap, why = capacity_from_facts(p["finances"])
        s = why["sub_scores"]
        subs = ", ".join(f"{s[k]:.2f}" for k in WEIGHTS)
        print(f"{p['id']:26} {cap:7.3f} {p['ground_truth']['capacity']:7.3f}  {subs:52}  {'; '.join(why['caps']) or '-'}")
