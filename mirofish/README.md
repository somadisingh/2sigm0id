# Test users (Part 2)

Synthetic investors for the experiment. Truth comes first: each user's true capacity, willingness and behavioral scores are set before anything else, capacity is computed by `capacity.py`, and MiroFish only supplied backstories.

## Use this file

**`personas_100_with_backstories.json`**: the 100 test users, in the `personas.json` format from `SHARED_CONTRACT.md`.

- 20 users per final band; 35 mismatch users (13 panic-sell, 12 can't-afford, 10 cautious); noise about a third each clean / moderate / heavy.
- All pass `run_bakeoff.py`'s checks (capacity = formula, lowest-of-three band, 2-band mismatch rule, 0.03 from band edges).
- IDs describe the user, e.g. `U027-b1-cantafford-moderate`.
- Each user's `profile` block (name, bio, backstory, mbti, interested_topics) is extra and ignored by the runner. Backstories only affect the simulator once `prompts.py` includes `profile["backstory"]`.

**`personas_pilot.json`**: 10 separate users for choosing the fixed-form questions. Never scored.

## Files

| File | What it is |
|---|---|
| `personas_100_with_backstories.json` | Final 100 users (use this) |
| `personas_pilot.json` | 10 pilot users |
| `personas_100.json` | The same 100 before backstories were added |
| `personas_with_backstories.json` | The first 5 hand-built users (S1-S5); `generate_users.py` builds on them |
| `generate_users.py` | Builds the 95 other users and the seed docs (`python mirofish/generate_users.py --repo . --base mirofish/personas_with_backstories.json --out mirofish`) |
| `seed_investors.md`, `seeds/` | Documents given to MiroFish (S1-S5, then 5 batches) |
| `mirofish_to_personas.py` | Merges MiroFish output into the users by name; never touches truth fields; rejects Chinese backstories |
| `check_backstories.py` | Flags backstories that are missing, in Chinese, social-media framed, have wrong numbers, mention other users, or are too long |
| `patch_mirofish_english.py` | Makes a local MiroFish copy produce English (not part of our code) |
| `mirofish_clean/` | The 5 MiroFish batches after cleaning, plus the record of how they were cleaned |

## How the backstories were made

MiroFish (DeepSeek V4 Flash on Baseten) wrote personas from the seed docs. Its output described people as social-media accounts or organisations, and some details contradicted their true profiles, so each backstory was rewritten: facts and risk attitudes come from the user's true data, and only MiroFish details that fit (jobs, hobbies, sayings) were kept. Result: `check_backstories.py` flags 0/100, and every backstory matches the user's knowledge, loss history, willingness band and behavioral band.

The scripts in `mirofish_clean/` are a record of that cleaning; their file paths point to where it was done, not to this repo.
