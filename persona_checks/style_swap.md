# Style-swap test: does the way a person talks change method D's result? (Nov 16, 2026)

Task S6 in `plan.md`. Siya made 20 copies of test users, 4 for each true final band (`mirofish/personas_style_swap.json`, made by `mirofish/make_style_swap.py`). Each copy changes all three style fields (length, vocabulary, hedging) and nothing else: same true profile, facts, backstory, noise and seed. Somaditya ran them with method D at 5, 10 and 15 questions, 3 repeats each (180 interviews, same setup as the full run, no errors, $2.58). Each run is paired with its original's method D run in the full run at the same budget and repeat.

Script: `python style_swap_compare.py results/experiment_style_swap.jsonl results/experiment_full.jsonl`. Differences are swap minus original; negative means the swap is better.

| Budget | Pairs | Avg error, original | Avg error, swap | Difference (95% range) | Band exact, original / swap (difference, 95% range) | Final band differs |
|---|---|---|---|---|---|---|
| 5 | 60 | 0.138 | 0.150 | +0.012 (−0.003 to +0.027) | 53% / 52% (−2 points, −15 to +12) | 32% |
| 10 | 60 | 0.113 | 0.117 | +0.004 (−0.015 to +0.021) | 72% / 60% (−12 points, −27 to +3) | 48% |
| 15 | 60 | 0.103 | 0.098 | −0.005 (−0.021 to +0.009) | 70% / 73% (+3 points, −10 to +17) | 38% |

By dimension (all budgets): capacity +0.014 (−0.005 to +0.034), willingness +0.005 (−0.012 to +0.023), behavior −0.009 (−0.025 to +0.008). None is clear.

**Baseline.** The final band of the same original user also changes between two repeats of method D: 30% of users at 5 questions, 30% at 10 and 45% at 15. The swaps change the band in 32% to 48% of pairs, so about as often as a plain repeat does.

## What this means

1. **No clear effect of talking style.** At every budget the 95% range of the error difference includes 0, and the size is at most 0.012 (about a tenth of D's error).
2. **The largest single gap is band exact at 10 questions (72% to 60%).** Its range includes 0, and the same gap at 15 questions goes the other way, so we report it but do not claim it.
3. **Limits.** 20 users. Most copies became "technical" (135 of 180 runs) and "high hedging" (144 of 180), because most original users were plain and low-hedging, so the other directions have few runs. A test with 20 users finds only large effects; it cannot rule out a small one.
