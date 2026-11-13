"""Generate the full test-user set: truth first, then everything else follows from it.

    python generate_users.py --repo ../2sigm0id --base ../personas_with_backstories.json

Writes:
  personas_100.json          the 5 hand-built users (S1-S5) + 95 generated ones (U006-U100)
  personas_pilot.json        10 extra users for choosing form questions; never scored
  seeds/seed_batch_01.md...  MiroFish seed documents, 20 people each

How each user is built:
  1. Pick the final band (20 users per band overall) and whether it's a mismatch user.
  2. Pick the band of each dimension from that.
  3. Capacity: sample finances until the team's capacity formula lands in the right band,
     at least 0.03 from a band edge. Capacity is never typed in by hand.
  4. Willingness and behavioral: a score inside the band, at least 0.03 from its edges.
  5. Demographics, goal, experience and style are drawn to fit the finances and attitudes
     (e.g. a 'sold in a panic' past only for low-behavioral users who have invested).
  6. Noise: a third clean, a third moderate, a third heavy.
Everything uses a fixed random seed, so rerunning gives the same 100 users.
"""
import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

EDGES = (0.2, 0.4, 0.6, 0.8)
MISMATCH_TYPES = ["says aggressive, would panic-sell",
                  "says aggressive, can't afford it",
                  "can afford risk, prefers caution"]


def band(s):
    return min(5, int(s * 5) + 1)


def safe(s):
    return min(abs(s - e) for e in EDGES) >= 0.03


def score_in_band(rng, b):
    lo, hi = (b - 1) / 5 + 0.04, b / 5 - 0.04   # 0.04 so rounding never lands on 0.0299...
    return round(rng.uniform(lo, hi), 2)


# ------------------------------------------------------------------ finances

FIN_RANGES = {  # loose ranges per capacity band; rejection sampling does the rest
    1: dict(h=[1, 2, 4, 5, 6, 8], e=[0.25, 0.5, 0.5, 1, 2], inc=["unstable", "partly commission-based"],
            d=(0.25, 0.55), dep=[0, 1, 2, 3]),
    2: dict(h=[3, 4, 5, 6, 8, 10, 12, 15], e=[0.5, 1, 1, 2, 3], inc=["unstable", "partly commission-based", "stable"],
            d=(0.15, 0.45), dep=[0, 0, 1, 2, 3]),
    3: dict(h=[6, 8, 10, 12, 15, 20], e=[1, 2, 3, 4, 6], inc=["partly commission-based", "stable", "stable"],
            d=(0.05, 0.30), dep=[0, 0, 1, 2]),
    4: dict(h=[10, 12, 15, 20, 25, 30], e=[3, 4, 6, 8, 9], inc=["stable", "very stable"],
            d=(0.0, 0.20), dep=[0, 0, 1, 2]),
    5: dict(h=[7, 9, 15, 20, 25, 30, 35], e=[9, 12, 12, 18, 24], inc=["very stable", "stable and high"],
            d=(0.0, 0.10), dep=[0, 0, 0, 1]),
}


def sample_finances(rng, cap_band, cap_fn):
    r = FIN_RANGES[cap_band]
    for _ in range(5000):
        f = {
            "horizon_yrs": rng.choice(r["h"]),
            "emergency_fund_months": rng.choice(r["e"]),
            "income_stability": rng.choice(r["inc"]),
            "debt_to_income": round(rng.uniform(*r["d"]), 2),
            "dependents": rng.choice(r["dep"]),
        }
        cap, _ = cap_fn(f)
        if band(cap) == cap_band and safe(cap):
            return f, cap
    sys.exit(f"Couldn't hit capacity band {cap_band}; widen FIN_RANGES.")


# ------------------------------------------------------------------ people

FIRST = """Aaliyah Aaron Abigail Adrian Aisha Alejandro Alex Amara Amir Ana Andre Anika Arjun Ava Beatriz
Ben Bianca Brandon Camila Carlos Chloe Chris Daniela Darius Deepa Derek Diego Elena Elijah Emeka Emily
Erin Esther Fatima Felix Gabriel Grace Hana Hector Imani Isaac Isabel Jamal Jasmine Javier Jenna Joel
Julia Kai Kavya Keisha Kenji Kevin Lara Leon Lily Lucas Malik Marcus Maria Mateo Megan Mei Miguel Mina
Nadia Nathan Nia Noah Nora Omar Olivia Oscar Paul Priya Quinn Rachel Rafael Rahul Rosa Ryan Sana Sean
Sofia Sam Talia Tariq Tessa Thomas Uma Valeria Victor Wei Will Xavier Yara Yusuf Zach Zoe Hugo Ines
Kofi Lena Ravi Sara Theo Vera Wendell Ximena Yuki Zainab""".split()
LAST = """Adams Ahmed Alvarez Anderson Bailey Bello Brooks Campbell Castillo Chen Cohen Cruz Davis Diaz
Edwards Evans Fischer Flores Garcia Gomez Green Gupta Hall Harris Hernandez Hill Huang Ibrahim Jackson
James Johnson Kaur Khan Kim Kowalski Lee Lewis Lopez Martin Mendoza Mitchell Moore Morales Murphy Nguyen
Okafor Ortiz Patel Perez Phillips Price Ramirez Reed Reyes Rivera Roberts Rodriguez Rossi Russell Sanchez
Santos Scott Shah Silva Singh Smith Sullivan Tanaka Taylor Thomas Torres Turner Vargas Walker Wang
Washington Watson White Williams Wilson Wright Yamamoto Young Zhang""".split()

OCCUPATIONS = {
    "unstable": ["rideshare driver", "food delivery courier", "freelance graphic designer", "restaurant server",
                 "freelance photographer", "musician who plays weddings", "construction day laborer",
                 "event bartender", "warehouse temp worker", "between jobs after a layoff"],
    "partly commission-based": ["car salesperson", "real estate agent", "hairstylist", "insurance agent",
                                "retail store manager paid partly on commission", "software sales rep",
                                "personal trainer", "travel agent"],
    "stable": ["elementary school teacher", "registered nurse", "software developer", "office manager",
               "medical lab technician", "marketing coordinator", "data analyst", "bank teller",
               "HVAC technician", "social worker", "UX designer", "pharmacy technician"],
    "very stable": ["city government clerk", "senior accountant", "tenured professor", "pharmacist",
                    "postal service supervisor", "public school principal", "civil engineer",
                    "hospital administrator"],
    "stable and high": ["physician", "corporate attorney", "senior software engineer", "dentist",
                        "owner of a small manufacturing business", "finance director"],
}
MIN_AGE = {"tenured professor": 36, "finance director": 35, "senior accountant": 30,
           "hospital administrator": 33, "public school principal": 35, "physician": 29, "dentist": 28,
           "corporate attorney": 27, "senior software engineer": 27, "postal service supervisor": 28,
           "owner of a small manufacturing business": 30, "civil engineer": 24, "pharmacist": 26}
HIGH_LIT_JOBS = {"senior accountant", "pharmacist", "physician", "corporate attorney", "finance director",
                 "senior software engineer", "data analyst", "software developer", "tenured professor",
                 "insurance agent", "bank teller", "software sales rep"}


def goal_for(rng, horizon, age, deps, partnered):
    if age >= 55:
        return rng.choice(["retirement income", "a comfortable retirement", "retirement and helping grandkids"])
    fits_retirement = abs(age + horizon - 65) <= 7
    if horizon <= 5:
        opts = ["a new car", "starting a small business", "a cushion before switching careers"]
        opts += ["a house down payment"] if age < 45 else ["home repairs"]
        opts += ["a wedding"] if not partnered and age < 40 else []
    elif horizon <= 12:
        opts = ["a bigger home", "early retirement savings"]
        opts += ["a house down payment"] if age < 45 else []
        opts += ["kids' college", "kids' college"] if deps and age < 48 else []
    else:
        opts = ["growing long-term wealth", "financial independence"]
        opts += ["retirement", "retirement", "retirement"] if fits_retirement else []
        opts += ["retirement and kids' college"] if fits_retirement and deps and age < 45 else []
    return rng.choice(opts)


def household_for(rng, deps, age):
    if deps == 0:
        return rng.choice(["single, lives alone", "single, shares an apartment", "married, no children",
                           "lives with a partner"] + (["married, grown children"] if age >= 48 else []))
    words = {1: "one", 2: "two", 3: "three"}
    if deps == 1:
        kind = "young" if age < 42 else "teenage"
        return rng.choice([f"single parent, one {kind} child", f"married, one {kind} child",
                           "supports an elderly parent"])
    kids = deps if rng.random() < 0.5 else deps - 1
    kind = "young" if age < 42 else "teenage"
    return f"married, {words.get(kids, kids)} {kind} child{'ren' if kids != 1 else ''}" \
        + ("; spouse not working" if kids < deps else "")


def age_for(rng, horizon, cap_band):
    if cap_band == 5 and horizon <= 10:           # pilot failure case: wealthy near-retiree
        return rng.randint(55, 62)
    if rng.random() < 0.5 and 22 <= 65 - horizon <= 62:   # saving for retirement
        return max(22, min(62, 65 - horizon + rng.randint(-2, 2)))
    return rng.randint(22, 50)


def investable_for(rng, income, age, cap_band):
    base = {"unstable": 2000, "partly commission-based": 6000, "stable": 12000,
            "very stable": 25000, "stable and high": 50000}[income]
    amt = base * ((age - 18) / 12) * rng.uniform(0.5, 1.6) * (0.6 + 0.15 * cap_band)
    return int(round(amt, -3)) or 1000


def experience_for(rng, beh_band, age, job):
    lit = "high" if job in HIGH_LIT_JOBS and rng.random() < 0.7 else rng.choice(["low", "low", "medium", "medium", "high"])
    invested_before = rng.random() < (0.3 + 0.012 * (age - 22))
    if not invested_before:
        return {"fin_literacy": lit, "past_loss_reaction": "none"}
    if beh_band <= 2:
        reaction = "sold" if rng.random() < 0.8 else "none"
    elif beh_band >= 4:
        reaction = "held" if rng.random() < 0.85 else "none"
    else:
        reaction = rng.choice(["held", "none", "sold"])
    return {"fin_literacy": lit, "past_loss_reaction": reaction}


def style_for(rng, lit, age):
    vocab_opts = ["plain", "casual"] + (["technical", "technical"] if lit == "high" else [])
    if age >= 45 and "casual" in vocab_opts:
        vocab_opts.remove("casual")
    return {"verbosity": rng.choice(["short", "medium", "medium", "long"]),
            "vocabulary": rng.choice(vocab_opts),
            "hedging": rng.choice(["low", "medium", "high"])}


def noise_for(rng, level):
    if level == "clean":
        return {"flip_prob": 0.0, "vague_rate": rng.choice([0.0, 0.05]), "contradiction_rate": 0.0,
                "correction_rate": 0.0, "acquiescence": rng.choice([0.0, 0.05]), "refuses_numbers": False}
    if level == "moderate":
        return {"flip_prob": rng.choice([0.0, 0.1]), "vague_rate": rng.choice([0.1, 0.15, 0.2]),
                "contradiction_rate": rng.choice([0.05, 0.1]), "correction_rate": 0.05, "acquiescence": rng.choice([0.05, 0.1, 0.15]),
                "refuses_numbers": rng.random() < 0.15}
    return {"flip_prob": rng.choice([0.2, 0.25, 0.3]), "vague_rate": rng.choice([0.3, 0.4, 0.5]),
            "contradiction_rate": rng.choice([0.15, 0.2, 0.3]), "correction_rate": 0.10, "acquiescence": rng.choice([0.15, 0.2, 0.3]),
            "refuses_numbers": rng.random() < 0.3}


# ------------------------------------------------------------------ dimension bands

def dimension_bands(rng, final, mismatch):
    """Return {capacity, willingness, behavioral} bands and the mismatch label."""
    if mismatch:
        kind = mismatch
        low = {"says aggressive, would panic-sell": "behavioral",
               "says aggressive, can't afford it": "capacity",
               "can afford risk, prefers caution": "willingness"}[kind]
        high = "capacity" if kind == "can afford risk, prefers caution" else "willingness"
        third = ({"capacity", "willingness", "behavioral"} - {low, high}).pop()
        b = {low: final, high: rng.randint(final + 2, 5), third: rng.randint(final, min(5, final + 2))}
        return b, kind
    b = {d: rng.choice([final, min(5, final + 1)]) for d in ("capacity", "willingness", "behavioral")}
    b[rng.choice(list(b))] = final
    return b, "none"


# ------------------------------------------------------------------ seed text

WILL_WORDS = {1: "avoids risk and would rather earn little than lose anything",
              2: "is fairly cautious and gets uneasy with big swings",
              3: "accepts some ups and downs in exchange for growth",
              4: "is comfortable taking real risk for higher growth",
              5: "wants maximum growth and insists losses don't scare them"}
BEH_WORDS = {1: "When their own money has actually been falling, they get out fast and lose sleep",
             2: "Watching their own balance shrink makes them anxious, and they tend to cut their losses",
             3: "When markets turn rough they feel uneasy and might trim a little, but mostly sit tight",
             4: "When markets turn rough they stay calm and wait it out",
             5: "When markets turn rough they see a bargain and add more"}
LOSS_WORDS = {"none": "They have never been through a big investment loss.",
              "held": "In a past downturn they held on.",
              "sold": "In a past downturn they sold in a panic and still think about it."}


def seed_paragraph(u):
    p, d, f, e, gt = u["profile"], u["demographics"], u["finances"], u["experience"], u["ground_truth"]
    return (f"## {p['name']}\n\n{p['name']} is a {d['age']}-year-old {d['occupation']} ({d['household']}). "
            f"Their income is {f['income_stability']}; debt payments take about {int(f['debt_to_income'] * 100)}% "
            f"of it, and they have about {f['emergency_fund_months']} months of expenses saved. "
            f"{DEPS_WORDS.get(f['dependents'], str(f['dependents']) + ' people depend on them.')} They want to invest about ${f['investable_amount']:,} "
            f"for {f['goal']}, needing it in about {f['horizon_yrs']} years.\n\n"
            f"They describe themselves as someone who {WILL_WORDS[band(gt['willingness'])]}. "
            f"{BEH_WORDS[band(gt['behavioral'])]}. {LOSS_WORDS[e['past_loss_reaction']]} "
            f"Their knowledge of investing is {e['fin_literacy']}.\n")


DEPS_WORDS = {0: "No one depends on them financially.", 1: "One person depends on them financially.",
              2: "Two people depend on them financially.", 3: "Three people depend on them financially."}

SEED_HEADER = ("# New Investors Circle: Member Profiles (batch {n})\n\n"
               "The New Investors Circle is a free six-week workshop at a public library for adults who are "
               "just starting to invest for the long term. These members agreed to share a short profile so "
               "the group could get to know one another.\n\n")


# ------------------------------------------------------------------ main

def build(rng, n_users, band_quota, mismatch_quota, start_idx, seed_start, cap_fn, names, id_prefix):
    plan = []
    for b, count in band_quota.items():
        mm = mismatch_quota.get(b, 0)
        kinds = [MISMATCH_TYPES[i % 3] for i in range(mm)]
        rng.shuffle(kinds)
        plan += [(b, k) for k in kinds] + [(b, None)] * (count - mm)
    rng.shuffle(plan)
    levels = (["clean", "moderate", "heavy"] * (n_users // 3 + 1))[:n_users]
    rng.shuffle(levels)

    users = []
    for i, ((final, mm), level) in enumerate(zip(plan, levels)):
        bands, kind = dimension_bands(rng, final, mm)
        fin, cap = sample_finances(rng, bands["capacity"], cap_fn)
        will, beh = score_in_band(rng, bands["willingness"]), score_in_band(rng, bands["behavioral"])
        age = age_for(rng, fin["horizon_yrs"], bands["capacity"])
        all_jobs = OCCUPATIONS[fin["income_stability"]]
        age = max(age, min(MIN_AGE.get(j, 22) for j in all_jobs))   # e.g. no 22-year-old physicians
        jobs = [j for j in all_jobs if MIN_AGE.get(j, 22) <= age]
        job = rng.choice(jobs)
        household = household_for(rng, fin["dependents"], age)
        partnered = "married" in household or "partner" in household
        fin["investable_amount"] = investable_for(rng, fin["income_stability"], age, bands["capacity"])
        fin["goal"] = goal_for(rng, fin["horizon_yrs"], age, fin["dependents"], partnered)
        exp = experience_for(rng, bands["behavioral"], age, job)
        idx = start_idx + i
        name = names.pop()
        tag = {"says aggressive, would panic-sell": "panic", "says aggressive, can't afford it": "cantafford",
               "can afford risk, prefers caution": "cautious"}.get(kind, "match")
        gt = {"capacity": cap, "willingness": will, "behavioral": beh,
              "final_band": min(band(cap), band(will), band(beh)), "mismatch_type": kind}
        users.append({
            "id": f"{id_prefix}{idx:03d}-b{gt['final_band']}-{tag}-{level}",
            "seed": seed_start + i,
            "ground_truth": gt,
            "demographics": {"age": age, "occupation": job, "household": household},
            "finances": {k: fin[k] for k in ("horizon_yrs", "emergency_fund_months", "income_stability",
                                             "debt_to_income", "dependents", "investable_amount", "goal")},
            "experience": exp,
            "style": style_for(rng, exp["fin_literacy"], age),
            "noise": noise_for(rng, level),
            "profile": {"name": name, "bio": f"{age}-year-old {job}.", "backstory": "", "source": "generated"},
        })
    return users


def validate(users, cap_fn):
    for u in users:
        gt = u["ground_truth"]
        cap, _ = cap_fn(u["finances"])
        assert abs(cap - gt["capacity"]) <= 0.005, (u["id"], "capacity")
        bands = [band(gt[d]) for d in ("capacity", "willingness", "behavioral")]
        assert gt["final_band"] == min(bands), (u["id"], "final band")
        assert (max(bands) - min(bands) >= 2) == (gt["mismatch_type"] != "none"), (u["id"], "mismatch")
        assert all(safe(gt[d]) for d in ("capacity", "willingness", "behavioral")), (u["id"], "edge")
    names = [u["profile"]["name"] for u in users]
    firsts = [n.split()[0] for n in names]
    assert len(set(names)) == len(names) and len(set(firsts)) == len(firsts), "names must be unique"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="team repo folder (for capacity.py)")
    ap.add_argument("--base", help="the 5 hand-built users (personas_with_backstories.json)")
    ap.add_argument("--total", type=int, default=100)
    ap.add_argument("--pilot", type=int, default=10)
    ap.add_argument("--batch", type=int, default=20, help="people per MiroFish seed document")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    sys.path.insert(0, str(Path(a.repo).resolve()))
    from capacity import capacity_from_facts as cap_fn

    rng = random.Random(a.seed)
    base = json.loads(Path(a.base).read_text()) if a.base else []
    taken = {u["profile"]["name"].split()[0] for u in base}
    firsts = [f for f in FIRST if f not in taken]
    rng.shuffle(firsts)
    lasts = LAST[:]
    rng.shuffle(lasts)
    names = [f"{f} {lasts[i % len(lasts)]}" for i, f in enumerate(firsts)]
    need = a.total - len(base) + a.pilot
    if len(names) < need:
        sys.exit(f"Need {need} unique first names; add more to FIRST.")

    # 20 per final band overall; ~35% mismatch, only possible for final bands 1-3
    per_band = a.total // 5
    have = Counter(u["ground_truth"]["final_band"] for u in base)
    have_mm = Counter(u["ground_truth"]["final_band"] for u in base if u["ground_truth"]["mismatch_type"] != "none")
    band_quota = {b: per_band - have[b] for b in range(1, 6)}
    target_mm = round(0.35 * a.total)
    mm_quota = {b: max(0, target_mm // 3 + (1 if b <= target_mm % 3 else 0) - have_mm[b]) for b in (1, 2, 3)}

    gen = build(rng, sum(band_quota.values()), band_quota, mm_quota, len(base) + 1, 300 + len(base) + 1,
                cap_fn, names, "U")
    users = base + gen
    pilot_quota = {b: a.pilot // 5 for b in range(1, 6)}
    pilot = build(rng, a.pilot, pilot_quota, {1: 1, 2: 1, 3: 1}, 1, 900, cap_fn, names, "PILOT")
    validate(users, cap_fn)
    validate(pilot, cap_fn)

    out = Path(a.out)
    (out / "seeds").mkdir(parents=True, exist_ok=True)
    (out / "personas_100.json").write_text(json.dumps(users, indent=2, ensure_ascii=False) + "\n")
    (out / "personas_pilot.json").write_text(json.dumps(pilot, indent=2, ensure_ascii=False) + "\n")
    todo = [u for u in users if not u["profile"].get("backstory")]
    for i in range(0, len(todo), a.batch):
        chunk = todo[i:i + a.batch]
        text = SEED_HEADER.format(n=i // a.batch + 1) + "\n".join(seed_paragraph(u) for u in chunk)
        (out / "seeds" / f"seed_batch_{i // a.batch + 1:02d}.md").write_text(text)

    fb = Counter(u["ground_truth"]["final_band"] for u in users)
    mm = Counter(u["ground_truth"]["mismatch_type"] for u in users)
    nz = Counter(u["id"].rsplit("-", 1)[-1] for u in gen)
    print(f"{len(users)} users ({len(base)} hand-built + {len(gen)} generated), {len(pilot)} pilot users")
    print("final band:   ", dict(sorted(fb.items())))
    print("mismatch:     ", dict(mm))
    print("noise (gen):  ", dict(nz))
    print(f"seed docs:     {len(range(0, len(todo), a.batch))} in seeds/ ({a.batch} people each)")
    print("All checks passed: capacity = formula, lowest-of-three, mismatch rule, 0.03 from edges, unique names.")


if __name__ == "__main__":
    main()
