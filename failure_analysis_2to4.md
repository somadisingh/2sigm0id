# Failure analysis 2 to 4 (Nov 16, 2026)

Written by Somaditya for Milestone 3. Part 1 (D's capacity error) is `failure_D_capacity.md`. Data: the full run without U054, the one user that fails 2 or more of Siya's persona checks (`results/experiment_full_excl.jsonl`, 7,128 interviews). Script: `python failure_more.py results/experiment_full_excl.jsonl` (no API calls). "Error" is the mean distance between the estimated and the true score (0 to 1, lower is better).

## 2. Why D and DR are worst on heavy-noise users

D and DR are the best methods on clean users and the worst engine methods on heavy-noise users.

| Avg error, 15 questions | Clean | Moderate | Heavy |
|---|---|---|---|
| A (fixed form) | 0.083 | 0.084 | 0.100 |
| C (adaptive form) | 0.077 | 0.083 | 0.098 |
| D (adaptive interviewer) | **0.062** | 0.097 | 0.168 |
| DR (D with retrieval) | **0.062** | 0.096 | 0.175 |
| D0 (old LLM-only interviewer) | 0.103 | 0.138 | 0.246 |

Findings:

1. **Most of the gap is capacity, through false facts.** D against C on the same heavy users (paired): capacity +0.103 at 10 questions and +0.128 at 15 (both clear). Willingness and behavior differ less: +0.010 and +0.016 at 10 (not clear), +0.047 and +0.035 at 15 (clear, but a third of the capacity gap).
2. **Only spoken methods receive false facts, and heavy users give the most.** Heavy users give the forms and D the same number of vague and flip answers (6.0 and 3.1 per run at 15 questions). D also gets 1.7 contradictions and 0.1 planned mistakes per run. Of D's heavy runs, 54% at 10 questions and 74% at 15 contain a false fact. D's heavy capacity error is 0.25 with a false fact and 0.19 to 0.21 without. Part 1 explains why one false fact costs so much (strong evidence, weakest-link caps, re-asks that do not recover).
3. **More questions do not help D on heavy users.** C's heavy error falls from 0.121 to 0.098 between 10 and 15 questions; D's stays at 0.164 to 0.168. Each extra spoken question is another chance for a false fact.
4. **DR has the same problem.** Retrieval helps read a single answer but does nothing against a false statement.

What it means: the D against C gap on heavy users is mostly the false facts that only spoken methods receive. Without false facts, D's capacity gap to C on heavy users falls to +0.055 at 10 questions (clear) and +0.031 at 15 (not clear; only 24 pairs). Real people may make fewer and smaller false statements than our heavy-noise test users. The fix is the same as in part 1: do not score a fact while two clear statements of it conflict.

## 3. Why D0 gets worse in longer conversations

D0 (the LLM keeps the scores itself, no belief engine) is the only method whose error rises with the budget: 0.128 at 5 questions, 0.138 at 10, 0.161 at 15.

1. **D0 drifts toward caution as the conversation goes on.** Its bias (estimate minus truth) is negative for all three scores and grows with the budget: capacity −0.06, −0.10, −0.13 at 5, 10, 15 questions; behavior −0.05, −0.08, −0.11.
2. **Inside one conversation, D0 first improves, then gets worse.** In the 15-question runs, D0's error is 0.186 after 3 answers, 0.133 after 8, then 0.146 after 12 and 0.161 at the end. Each answer moves the scores less over time (0.06 at the start, 0.02 at the end), but the moves keep going in the same cautious direction.
3. **The bold users lose most.** At 15 questions, D0 underestimates true band-5 users by 0.20 on capacity, 0.17 on willingness and 0.22 on behavior. True band-1 users are about right (+0.03).
4. **Noise makes it worse.** D0 at 15 questions: 0.103 on clean users and 0.246 on heavy users.

What it means: with no record of the evidence, the LLM treats each cautious sign (a hedge, a vague answer, a planned flip) as a reason to lower the score, and it does not raise the score back when later answers are bold. So more questions add more cautious signs. This is a pattern in the numbers; we did not test the cause directly. The belief engine fixes it by design: every answer is weighed by the same rule, and the error of D falls with the budget (0.138, 0.116, 0.107).

## 4. Why the stop rule misses its promise

The rule: stop when asking the rest of the budget has under a 5% chance of changing the final band (`belief.py`). In the full run, the band changes after the stop point in 8% (C) and 7% (D) of runs at 10 questions, and 14% (C) and 11% (D) at 15. We found three causes.

1. **The engine is too sure of its band.** At the stop point, the engine gives its most likely band a 76% to 80% chance on average. That band is the true final band in 69% to 71% of runs for C and in 56% to 66% for D. When the belief is too narrow, the simulated futures move too little, so the change chance is too low.
2. **The rule stops when no question can help, even if the band is unsure.** In 13% to 37% of stops, the engine's change chance is exactly 0. In 15% to 32% of stops, the engine is under 70% sure of its band. In those stops the band changes later in 11% to 23% of runs. When the engine is at least 85% sure, it changes in 0% (C, 10 questions) to 7% (C, 15). The rule asks "can the remaining questions change the band?" and not "is the band known?".
3. **For D, the engine and the score use different band rules.** The engine stops on the most likely band of its final-band distribution. The score uses the lowest of the three bands of the mean scores. At D's stop point the two differ in 11% of runs (C: 1% to 4%). With the engine's own band, D's change rate is 3.6% at 10 questions (under 5%) and 6.5% at 15. This is the same mismatch as the one fixed in the live chat (`live_session.py`, Nov 14).

Not a cause: noise after the stop. For C at 10 questions the band changes more often when no noise comes after the stop (9.8%) than when noise does (3.9%).

**A stricter limit alone does not fix it.** Replayed on the recorded change chances (no new interviews):

| Limit | C, 10: changes after / questions saved per run | C, 15 | D, 10 | D, 15 |
|---|---|---|---|---|
| 5% (as run) | 8.1% / 2.7 | 14.3% / 6.6 | 7.3% / 1.8 | 10.6% / 4.5 |
| 2% | 7.8% / 2.0 | 9.0% / 5.2 | 8.4% / 1.3 | 6.0% / 2.9 |
| 1% | 7.2% / 1.7 | 7.1% / 4.4 | 7.5% / 1.0 | 5.2% / 2.4 |
| 0.5% | 7.3% / 1.6 | 7.1% / 3.7 | 6.3% / 0.9 | 4.3% / 2.0 |

C stays at about 7% at any limit, because of cause 2. (Caveat: with a stricter limit, a real run would have asked different questions after the old stop point. The table is an estimate.)

Fixes (need new runs, not done before Milestone 3):

1. Stop only when the change chance is under 5% **and** the engine is at least 85% sure of its band.
2. Use one band rule everywhere: the stop rule, the live chat and the score.
3. Widen the belief so that its confidence matches its accuracy (for example, fit a "temperature" on the pilot users).

What Milestone 3 must say: the stop rule saves a third to a half of the questions, but the "under 5%" promise does not hold (7% to 14%). It is a promise of the engine's model, and the model is too sure of itself.

**Update (Nov 22, ablation test 9, new interviews):** we added fix 1, with an 80% floor instead of 85% (`STOP_CONFIDENCE = 0.80`, chosen on the recorded runs). In the rerun, the band changes after the stop in 0.0% / 1.1% / 4.3% of C runs and 0.0% / 2.2% / 3.0% of D runs (5 / 10 / 15 questions). The promise now holds at every budget. The stop still saves 1.0 to 3.9 questions per run at 10 and 15 questions (before: 1.8 to 6.6). Fixes 2 and 3 are not done. Side effect: the form (C) stays longer in "settle the band" mode, so it asks fewer questions that sharpen single scores (at 10 questions: 24% of turns before, 16% after). Its capacity error at 10 questions rose by 0.011 (clear). Where C asked exactly the same questions in both runs, the change is 0.000, so the cause is the question choice, not the answers.

**Update (Nov 22, ablation test 13, replay):** fix 2 is done (`BAND_RULE = "reported"` in `belief.py`). The stop rule, the live chat and the score now use the same band: the lowest of the three bands of the mean scores. On the recorded answers of the rerun, the band changes after the stop in 0.0% to 1.9% (C) and 0.0% to 3.0% (D), and the stop saves 0.04 to 0.37 fewer questions per run. Fix 3 (widen the belief) is not done.
