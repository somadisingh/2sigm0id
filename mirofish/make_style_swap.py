"""Style-swap test users (docs/plan.md, task S6).

Picks 20 of the 100 test users, 4 per true final band, and makes a copy of each with only the
`style` block changed: short <-> long, plain <-> technical (casual -> technical), low <-> high
hedging. "medium" goes to short/long or low/high, alternating, so every copy changes at least
two of the three style fields. The true profile, facts, noise and backstory stay the same.

Users whose backstory describes how they talk ("speaks precisely and briefly", "talks casually")
are skipped, because the backstory would fight the new style. Pilot users are never used.

  python mirofish/make_style_swap.py      # writes mirofish/personas_style_swap.json

Each copy has the id "<original id>-swap" and profile.style_swap_of = the original id, so the
result of each copy can be compared with its original's method D result.
"""

import copy
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "personas_100_with_backstories.json"
OUT = HERE / "personas_style_swap.json"
PER_BAND = 4
TALK = re.compile(r"\b(speaks?|talks? (casually|a lot|like a salesperson|about 'technical)|"
                  r"uses slang|likes phrases|often saying)\b", re.I)

FLIP = {"verbosity": {"short": "long", "long": "short", "medium": ("long", "short")},
        "vocabulary": {"plain": "technical", "technical": "plain", "casual": ("technical", "technical")},
        "hedging": {"low": "high", "high": "low", "medium": ("high", "low")}}


def swap(style, k):
    """k alternates the direction for 'medium' values."""
    out = {}
    for field, val in style.items():
        new = FLIP[field][val]
        out[field] = new[k % 2] if isinstance(new, tuple) else new
    return out


def extremeness(p):
    return sum(v != "medium" for v in p["style"].values())


def noise_total(p):
    n = p["noise"]
    return n["flip_prob"] + n["vague_rate"] + n["contradiction_rate"]


def main():
    users = json.loads(SRC.read_text())
    ok = [p for p in users if not TALK.search((p.get("profile") or {}).get("backstory", ""))]
    chosen = []
    for band in range(1, 6):
        pool = [p for p in ok if p["ground_truth"]["final_band"] == band]
        # most extreme style first, then lower noise; keep one of each mismatch type if possible
        pool.sort(key=lambda p: (-extremeness(p), noise_total(p), p["id"]))
        picked, types = [], set()
        for p in pool:
            t = p["ground_truth"]["mismatch_type"]
            if t not in types or len(picked) >= PER_BAND - 1:
                picked.append(p)
                types.add(t)
            if len(picked) == PER_BAND:
                break
        for p in pool:   # fill up if the type rule left gaps
            if len(picked) == PER_BAND:
                break
            if p not in picked:
                picked.append(p)
        chosen += picked

    out = []
    for k, p in enumerate(chosen):
        q = copy.deepcopy(p)
        q["id"] = f"{p['id']}-swap"
        q["style"] = swap(p["style"], k)
        q.setdefault("profile", {})["style_swap_of"] = p["id"]
        assert q["ground_truth"] == p["ground_truth"] and q["finances"] == p["finances"]
        assert sum(q["style"][f] != p["style"][f] for f in FLIP) >= 2
        out.append(q)

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out)} users to {OUT.relative_to(HERE.parent)}\n")
    print(f"{'new id':34} band  mismatch                            original style -> new style")
    for p, q in zip(chosen, out):
        o, n = p["style"], q["style"]
        print(f"{q['id']:34} {p['ground_truth']['final_band']}     {p['ground_truth']['mismatch_type']:35} "
              f"{o['verbosity']}/{o['vocabulary']}/{o['hedging']} -> {n['verbosity']}/{n['vocabulary']}/{n['hedging']}")


if __name__ == "__main__":
    main()
