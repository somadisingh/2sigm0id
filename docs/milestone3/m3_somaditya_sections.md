# Milestone 3 draft: results, cost and speed, failure analysis (Somaditya, Nov 16, 2026)

Draft sections for the combined Milestone 3 document. Sources: `plan.md` section 5a, `ablations.md`, `p4_numbers.md`, `failure_D_capacity.md`, `failure_analysis_2to4.md`, `persona_checks/`. All numbers leave out U054, the one test user that fails 2 or more persona checks. This changes no avg error by more than 0.001.

## Results

**Setup.** We ran 8 methods on 99 test users at 5, 10 and 15 questions, 3 times each (7,128 interviews, no errors). GLM 5.3 is the interviewer. DeepSeek V4 Flash plays the test users. Each test user gets the same planned noise in every method. Avg error is the mean distance between the estimated and the true scores (0 to 1, lower is better). "Band exact" is the share of interviews with the correct final band (1 to 5).

| Method | Avg error, 5 / 10 / 15 questions | Band exact at 10 |
|---|---|---|
| A: fixed form (baseline) | **0.125** / 0.113 / 0.090 | 50% |
| B: scripted interview | 0.150 / 0.130 / 0.113 | 42% |
| C: adaptive form (belief engine) | 0.130 / **0.103** / **0.086** | **71%** |
| D: adaptive interviewer (belief engine + AI model) | 0.138 / 0.116 / 0.107 | 60% |
| DR: D + retrieval | 0.134 / 0.115 / 0.109 | 62% |
| DP: D + token probabilities | 0.180 / 0.140 / 0.123 | 53% |
| DN: D without re-asks | 0.140 / 0.122 / 0.123 | 58% |
| D0: AI model only (Milestone 2 design) | 0.128 / 0.138 / 0.161 | 54% |

**Against the baseline.** Differences are paired on the same user and repeat, with a 95% bootstrap range. Negative error means better than A.

| | 5 questions | 10 questions | 15 questions |
|---|---|---|---|
| C − A, avg error | +0.005 (−0.002 to +0.012) | **−0.010 (−0.017 to −0.003)** | −0.004 (−0.009 to +0.002) |
| C − A, band exact | +1 point | **+21 points (+14 to +29)** | +5 points |
| D − A, avg error | +0.013 (+0.005 to +0.021) | +0.003 (−0.006 to +0.011) | +0.017 (+0.008 to +0.027) |
| D − A, band exact | −3 points | **+10 points (+3 to +17)** | −2 points |

**What we found.**

1. **The belief engine works best with a form.** C is the best method at 10 and 15 questions. At 10 questions it is the only method with a clearly lower error than A, and it gets 21 points more exact bands.
2. **D equals A on error at 10 questions and gets 10 points more exact bands.** It is worse than A at 5 and 15. Its problem is capacity (see the failure analysis). At 10 and 15 questions, D reads willingness and behavior as well as C.
3. **The belief engine is better than the AI model alone.** D is clearly better than D0 at 10 and 15 questions (−0.022 and −0.054). D0 gets worse with more questions; D gets better.
4. **Re-asks help.** D is clearly better than DN at 15 questions (−0.016, 9 points more exact bands).
5. **Retrieval adds nothing.** DR and D do not differ clearly at any budget. Token probabilities (DP) are clearly worse at all budgets.
6. **The results do not depend on the evidence strengths.** With other strengths, the order of the methods does not change at 10 questions. No error changes by more than 0.006 (ablation test 7).
7. **Talking style does not change D's result.** We ran 20 test users again with a different style (length, vocabulary, hedging). The error difference is at most 0.012 at every budget and is not clear.

All 8 ablation tests are in `ablations.md`, with the predictions we wrote before the run.

## Cost and speed

We log every AI call for every profile. The test users' cost is separate (about $0.001 per profile at 10 questions for all methods).

| Method (10 questions) | AI calls | Input tokens | System $ (list price) | Wait per turn (95th percentile) |
|---|---|---|---|---|
| A, C | 0 | 0 | $0 | 0 s (engine: 0.1 s) |
| B | 10.0 | 1,826 | $0.0031 | 0.86 s (2.1 s) |
| DP | 10.7 | 1,777 | $0.0029 | 0.99 s (2.5 s) |
| D | 11.5 | 7,380 | $0.0126 | 1.24 s (2.8 s) |
| DR | 11.6 | 9,737 | $0.0157 | 1.24 s (3.0 s) |
| D0 | 11.7 | 14,829 | $0.0272 | 1.75 s (3.5 s) |

1. **The belief engine makes D cheaper and faster than D0.** D costs 54% less than D0 at 10 questions and 62% less at 15. D0 sends the whole conversation with every call, so its input grows faster: 28,978 tokens at 15 questions against 11,124 for D.
2. **The engine itself is free.** It runs in code, with no AI call, in about 0.1 s per question.
3. **Cost against accuracy.** C has the best accuracy and costs nothing. D costs about 1 cent per profile for the same accuracy as A. Retrieval adds 25% cost and no accuracy. DP saves 77% of D's cost and loses accuracy. Chart: `results/experiment_full_cost_vs_error.png`.
4. **Our dollar figures are upper bounds.** They use list prices. The full run alone is $77.33 at list price. The provider billed $46.10 for all runs in the same period: the full run, the tests before it, the style-swap test and a persona check. So the real price is at most about 60% of the list price. A discount for repeated prompt text probably causes this. It helps the methods with long prompts (D0, DR) most, so the ratios between methods are estimates.

## Failure analysis

**1. D's capacity error comes from false facts.** Only spoken methods receive false money facts from the noisy test users. A form has no follow-up questions, so it gets only vague and flipped answers. Persona check 4 confirms that the false facts are in the answers (95% to 96% of planned contradictions, 1% to 4% false alarms).
- D runs with a false fact: capacity error 0.23 (10 questions) and 0.22 (15). Without one: 0.14 and 0.09. C: 0.12 and 0.10.
- D reads clear answers well. In turns with no noise, the read range holds the true value in 97% of cases.
- One false fact costs a lot for three reasons. One clear statement is strong evidence. The weakest-link caps in the capacity formula turn a 50/50 belief into a large drop. And a re-ask does not fix it: the AI test user repeats its false value in a third of re-asks.
- Fixes we tested on the recorded answers (weaker fact evidence, median instead of mean) do not solve it. The fix is to not score a fact while two clear statements of it conflict. This needs a new run.

**2. D and DR fail on heavy-noise users.** They are the best methods on clean users (0.062 at 15 questions; C 0.077). They are the worst engine methods on heavy-noise users (0.168 and 0.175; C 0.098). Most of the gap is capacity: 54% to 74% of D's heavy-noise runs contain a false fact. More questions do not help, because each spoken question is another chance for a false fact.

**3. D0 gets worse in longer conversations.** Its error rises from 0.128 to 0.161 between 5 and 15 questions. It drifts toward caution: its capacity bias goes from −0.06 to −0.13. At 15 questions it underestimates bold (band 5) users by about 0.2 on each score. The AI model treats each cautious sign as a reason to lower a score, and does not raise it back. The belief engine weighs every answer by the same rule, so D does not drift.

**4. The stop rule breaks its promise.** The rule stops when the rest of the budget has under a 5% chance to change the final band. It saves a third to a half of the questions. But the band changes after the stop in 7% to 14% of runs. We found three causes:
- The engine is too sure. It gives its top band 76% to 80% on average, but that band is correct in only 56% to 71% of runs.
- It stops when no remaining question can help, even when it is unsure. In a third of stops it is under 70% sure, and the band changes later in up to 23% of those.
- For D, the engine and the score use different band rules (most likely band against lowest of three). We fixed the same mismatch in the live chat.

A stricter limit alone does not fix it for C (it stays at about 7%). The fix is to stop only when the engine is also at least 85% sure, and to use one band rule everywhere.

**5. Smaller findings.**
- Planned "flip" noise is weak on forms: the answer leans away from the truth in only 27% of flip turns. So the forms get less effective noise than planned. This favors A and C a little in the comparison with D.
- People can read the band from the test users' answers. Three human readers got the exact band in 50% to 75% of 20 conversations and were within 1 band in 90% to 95%. Method D: 60% and 100%.

**Limits.** All test users are AI models. Real people may make fewer false statements and may correct them when asked. The classmate study tests this, but with 10 to 15 people it can only describe it.
