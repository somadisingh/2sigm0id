# Failure analysis 1: method D's capacity error (Nov 14, 2026)

Written by Somaditya for Milestone 3. Data: the full run (`results/experiment_full.jsonl`, 7,200 interviews). Script: `python failure_capacity.py results/experiment_full.jsonl` (no API calls). All numbers are capacity error: the mean distance between the estimated and the true capacity score (0 to 1, lower is better).

## 1. The problem

D reads willingness and behavior as well as the forms do or better. But its capacity error is much higher than C's, and this is the main reason that C is better than D overall (ablation tests 2 and 6).

| Budget | A | C | D | D0 |
|---|---|---|---|---|
| 5 | 0.205 | 0.183 | 0.200 | 0.120 |
| 10 | 0.165 | 0.119 | 0.163 | 0.144 |
| 15 | 0.082 | 0.096 | 0.140 | 0.173 |

## 2. Main finding: the error comes from false facts, not from reading

The test users have planned noise. One kind is a **false fact**: the test user states a clearly wrong money fact (for example "debt payments eat about half my income" when the truth is 4%), or makes a planned mistake and corrects it on the next turn. **Only spoken methods receive false facts.** A form has no follow-up questions, so the forms (A and C) get only the "vague" and "flip" noise (`methods.py`, `FORM_NOISE`).

We split D's runs into runs with a false fact and runs without one:

| Budget | D runs with a false fact | Capacity error, with false fact | Capacity error, without | C (never gets false facts) |
|---|---|---|---|---|
| 10 | 89 of 300 (30%) | 0.226 (bias −0.156) | 0.137 (bias −0.011) | 0.119 |
| 15 | 120 of 300 (40%) | 0.217 (bias −0.148) | **0.088** (bias −0.020) | 0.096 |

Without false facts, D's capacity at 15 questions is better than C's. By noise level, D is the best method of all on clean users at 15 questions (0.061; A 0.072, C 0.086), and the worst on heavy-noise users (0.235; C 0.108). Heavy-noise users have the highest rate of false facts (15% to 30% of turns).

**D reads clear answers well.** Each spoken fact reading is a range (for example 0.06 to 0.08). On turns with no noise, the range holds the true value in 97% of readings from the fact's own question (2,158 readings). On turns with a false fact aimed at that fact, it holds the true value in 0% to 10% (407 readings). So the extractor reads what the test user says. The problem is what the engine does with a false statement after that.

## 3. Why one false fact costs so much

Three parts of the system add to each other.

1. **One clear statement is very strong evidence.** The engine treats a clear spoken fact as 46 times more likely inside its range than outside (`FACT_MISS` = 0.1). A false statement and a true statement of the same fact cancel each other. The belief is then split about 50/50 between the true and the false value.
2. **The weakest-link caps turn a split into a large drop.** Most false facts push a fact past a cap in `capacity.py`: "need the money in about 2 years" (cap 0.20), "under a month of savings" (cap 0.35), "debt is half my income" (cap 0.35). When a large part of the belief is under a cap, the mean capacity falls a lot. For users whose true finances trigger no cap, the engine's final belief gives a cap 33% to 39% chance after a false fact, and 6% to 10% without one. This is why the bias is about −0.15: D underestimates capacity after a false fact.
3. **Asking again does not fix it with these test users.** D flags the contradiction on the same turn in 75% to 86% of cases, and asks about that fact again in 60% to 64% of cases. But when D asks again, the AI test user repeats the false value in about a third of cases (35 of 98 re-asks). In 8 of these, no noise was planned for that turn: the test user stayed consistent with its own earlier false statement. A real person would more likely correct it. Runs where D asked again ended with a *higher* capacity error (0.27 to 0.29) than runs where it did not (0.16 to 0.18). Part of this is selection (the false fact came earlier, so more questions were left). But it shows that a re-ask does not reliably recover the truth here.

## 4. Smaller causes (also in runs without false facts)

At 10 questions, D without false facts (0.137) is still worse than C (0.119). Two causes:

- **D asks some facts less often.** At 10 questions, D asks the income question in 26% of runs (C: 64%) and the dependents question in 5% (C: 14%). D picks these facts up from answers to other questions instead. Those readings are less accurate: 73% hold the truth, against 97% from the fact's own question. Example: "I've got a solid emergency fund" was read as 3 to 6 months when the truth is 24.
- **Income is hard to read from speech.** Income readings hold the true category in only 66% of no-noise readings ("very steady, I'm a nurse" was read as "very stable", the truth is "stable"). The categories are close in meaning.

## 5. Fixes we tested on the recorded answers (no new interviews)

| Change | D capacity error, budget 10 / 15 | C, budget 10 / 15 | Result |
|---|---|---|---|
| None (as run) | 0.163 / 0.140 | 0.119 / 0.096 | |
| Weaker fact evidence (`FACT_MISS` 0.3) | 0.183 / 0.160 | not affected | Worse. Clear true answers count for less too. |
| Median of capacity instead of mean | 0.157 / 0.135 | 0.104 / 0.079 | Better for both, but it helps C more and does not fix false-fact runs (0.223 / 0.217). |

So a different weighting does not solve the problem. The false fact must be resolved, not averaged.

## 6. Fixes that need new interviews (not done)

1. **When two clear statements of a fact conflict, do not score until a third one decides.** Exclude the conflicting fact from the capacity mean, or use the earlier statement, until a re-ask resolves the conflict. This needs a new run of D.
2. **Ask income and dependents directly** instead of waiting for them to come up in other answers.
3. **Use the median capacity** (tested above). It helps all engine methods, so it does not change the ranking. If we adopt it, we must rescore all methods and write it in `ablations.md` as a change.

We do not make these changes before Milestone 3. The full run is fixed, and a fix would need a new run of D, DR, DP and DN.

## 7. What Milestone 3 must say

1. D's capacity problem is mostly a reaction to false facts. Only spoken methods receive false facts, so the D against C comparison on capacity is partly a comparison of different noise. We report D's capacity error with and without false facts.
2. Without false facts, D reads money facts from speech as well as a form does (and better at 15 questions).
3. The engine has no good way to handle a false fact: one statement is strong evidence, the caps make a split belief costly, and re-asks do not reliably recover the truth with AI test users.
4. Limit: AI test users repeat their own false statements. Real people may correct themselves more often (ablation test 3, prediction for real users). The classmate study will show the re-asks with real people, but with 10 to 15 people it is only a description.

## Note on cost

The dollar figures in `score.py` use the list prices in `config.py`. They give $77.33 for the full run. The provider billed $43.54 for the last two days, including the full run and the test runs before it. GLM 5.3 is $68 of the $77 at list price, so the real price is lower, maybe because of a discount for repeated prompt text. Milestone 3 must say that our costs are list-price upper bounds. The ratios between methods are an estimate: a discount for repeated text helps methods with long prompts (D0, DR) more.

## Update (Nov 22): ablation tests 9 and 10 (new interviews)

- **Fix "conflicting facts need a majority" (in the engine from Nov 22):** on the recorded answers it lowered D's capacity error by 0.005 to 0.007. In new interviews the change is −0.001 at 10 and 15 questions (not clear). It does not fix the problem, because the AI test users usually state the false value again on the re-ask, so the false value often has the majority.
- **Test users who correct a false fact when asked again (noise version 3, a separate arm):** D's capacity error falls from 0.163 to 0.147 at 10 questions (clear) and from 0.139 to 0.128 at 15 (not clear). This supports point 4 of section 7: part of D's gap comes from how the AI test users act, not from the interviewer. Even so, D is not more accurate than the forms on avg error (at 15 questions D is worse than C by 0.011, clear).
- Full numbers: `ablations.md`, "Results of tests 9 and 10".
