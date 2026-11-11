"""Merge MiroFish's generated personas into our test users.

Truth comes first (personas.json: true scores, finances, style, noise). MiroFish only adds
backstory: its bio, persona text, MBTI and interests go into each user's `profile` block,
matched by name. Nothing in ground_truth, finances, style or noise is touched, and capacity
is re-checked against the team's capacity.py.

Usage:
    python mirofish_to_personas.py \
        --mirofish  MiroFish/backend/uploads/simulations/<sim_id>/reddit_profiles.json \
        --personas  personas.json \
        --repo      path/to/2sigmoid \
        --out       personas_with_backstories.json
"""
import argparse
import json
import re
import sys
from pathlib import Path


def norm(s):
    return " ".join((s or "").lower().split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirofish", required=True, nargs="+", help="one or more MiroFish reddit_profiles.json files")
    ap.add_argument("--personas", required=True, help="our personas.json (truth first)")
    ap.add_argument("--repo", help="team repo folder, to re-check capacity with capacity.py")
    ap.add_argument("--out", default="personas_with_backstories.json")
    a = ap.parse_args()

    mf = [agent for path in a.mirofish for agent in json.loads(Path(path).read_text(encoding="utf-8"))]
    users = json.loads(Path(a.personas).read_text(encoding="utf-8"))

    by_name = {}
    for agent in mf:
        by_name.setdefault(norm(agent.get("name")), agent)

    matched, missing, used, kept, chinese = 0, [], set(), 0, []
    todo = []
    for u in users:
        if u.get("profile", {}).get("source") not in (None, "generated", "mirofish"):
            kept += 1   # already has a reviewed backstory (e.g. S1-S5); don't overwrite it
        else:
            todo.append(u)
    for u in todo:
        name = norm(u.get("profile", {}).get("name"))
        agent = by_name.get(name)
        if agent is None:  # fall back: MiroFish sometimes uses only a first name (first names are unique)
            parts = name.split()
            hits = [ag for n, ag in by_name.items() if parts and n.split() and n.split()[0] == parts[0]]
            agent = hits[0] if len(hits) == 1 else None
        if agent is None:
            missing.append(u["profile"].get("name", u["id"]))
            continue
        if re.search(r"[\u4e00-\u9fff]", (agent.get("persona") or "") + (agent.get("bio") or "")):
            chinese.append(u["profile"].get("name", u["id"]))   # never merge a Chinese backstory
            used.add(norm(agent.get("name")))
            continue
        u["profile"].update({
            "bio": agent.get("bio", u["profile"].get("bio")),
            "backstory": agent.get("persona", u["profile"].get("backstory")),
            "mbti": agent.get("mbti"),
            # MiroFish's prompt is in Chinese, so short fields like topic tags sometimes come back
            # in Chinese even with the page in English; keep only the English tags.
            "interested_topics": [t for t in agent.get("interested_topics", [])
                                  if isinstance(t, str) and not re.search(r"[一-鿿]", t)],
            "source": "mirofish",
        })
        matched += 1
        used.add(norm(agent.get("name")))

    extra = sorted(set(by_name) - used)
    print(f"Matched {matched}/{len(todo)} users to MiroFish personas"
          + (f" ({kept} already-reviewed users left as they were)." if kept else "."))
    if missing:
        print(f"No MiroFish persona for {len(missing)}:", ", ".join(missing),
              "(rerun their batch, or write these by hand)")
    if chinese:
        print(f"REJECTED {len(chinese)} backstories written in Chinese (not merged):", ", ".join(chinese),
              "\n  -> run patch_mirofish_english.py, restart MiroFish, and rerun the batch(es) they came from")
    if extra:
        print(f"Ignored {len(extra)} MiroFish agents that aren't our users (e.g. {', '.join(extra[:4])}).")

    if a.repo:
        sys.path.insert(0, str(Path(a.repo).resolve()))
        from capacity import capacity_from_facts
        for u in users:
            cap, _ = capacity_from_facts(u["finances"])
            if abs(cap - u["ground_truth"]["capacity"]) > 0.005:
                sys.exit(f"{u['id']}: capacity {u['ground_truth']['capacity']} != formula {cap}")
        print("Capacity re-checked against capacity.py: OK")

    Path(a.out).write_text(json.dumps(users, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote", a.out)


if __name__ == "__main__":
    main()
