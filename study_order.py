"""The order (A first or D first) for each classmate in the study (task S5).

Participants come in pairs: in each pair (P01-P02, P03-P04, ...) a seeded coin flip decides
who does the form (A) first and who does the interview (D) first. So the two orders stay
balanced even if the study stops early, and nobody picks the order by convenience.

  python study_order.py            # writes study_order.json (40 IDs, seed below)

Assign IDs in the order people sign up: the first person gets P01, the next P02, and so on.
Do not skip or reuse an ID.
"""

import json
import random
from pathlib import Path

SEED = 20261114   # chosen once for this study; do not change after the study starts
N = 40
PATH = Path(__file__).resolve().parent / "study_order.json"


def make(n=N, seed=SEED):
    rng = random.Random(seed)
    order = {}
    for first in range(1, n + 1, 2):
        pair = [["A", "D"], ["D", "A"]]
        rng.shuffle(pair)
        for i, o in zip((first, first + 1), pair):
            order[f"P{i:02d}"] = o
    return {"seed": seed, "note": "pairs P01-P02, P03-P04, ... each have one A-first and one D-first",
            "order": order}


def load():
    return json.loads(PATH.read_text())["order"]


if __name__ == "__main__":
    data = make()
    PATH.write_text(json.dumps(data, indent=1))
    firsts = [o[0] for o in data["order"].values()]
    print(f"Wrote {PATH.name}: {len(firsts)} IDs, {firsts.count('A')} A-first, {firsts.count('D')} D-first")
