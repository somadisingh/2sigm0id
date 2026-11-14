# Ablation plan for the full run

Written by Preyansh before the full run (Nov 13, 2026). We fix the tests, the measures and the predictions here before we see the results. We do not add, remove or change a test after the run starts. If we must change something, we write the change and the reason in the "Changes" section at the end, with the date.

An ablation removes or changes one part of the system to measure what that part adds.

## Rules for all tests

- **Test users:** Siya's 100 test users (`mirofish/personas_100_with_backstories.json`). The 10 pilot users are never scored.
- **Budgets and repeats:** 5, 10 and 15 questions; 3 repeats. Every method meets the same test users with the same noise schedule.
- **Main measure:** avg error, the average distance between the final profile and the true profile over the three scores (0 to 1, lower is better).
- **Other measures:** band exact (share of runs where the final band is exactly right), and system $ and wait per turn from `score.py`.
- **How we compare:** paired on the same test user, budget and repeat. We report the mean difference in avg error with a 95% bootstrap range (`score.py`, `paired_table`).
- **When a difference is clear:** only when the 95% range of the paired difference does not include zero. Run-to-run noise is about 0.03 in avg error, so we do not rank methods on smaller differences without that range.
- **Main budget:** we state each prediction at budget 10, and we report budgets 5 and 15 too.
- **Many tests:** we run 8 tests. One of them can look clear by chance. We report all 8, also the ones that show no difference.

## Tests

### 1. What the belief engine adds

| | |
|---|---|
| Question | Does code that chooses the questions (the belief engine) give a better profile than an LLM that does everything? |
| Compare | D (engine) against D0 (LLM only, prompt v1) |
| Measure | avg error, band exact, system $ per profile, wait per turn |
| Data so far | 5 test users, budget 10: D 0.114, D0 0.107. Too small to rank. D costs 62% less and is 4 times faster per turn. |
| Prediction | No clear difference in avg error. D costs at least 50% less per profile and is at least 3 times faster per turn. |

### 2. What conversation adds

| | |
|---|---|
| Question | With the same engine, is a spoken interview better than a form? |
| Compare | D against C |
| Measure | avg error, willingness error, band exact |
| Data so far | 100 test users, budget 10, one run: D 0.116, C 0.104. Paired D − C: +0.011 (−0.002 to +0.026), not clear. D's willingness error is higher (0.131 against 0.111). |
| Prediction | C is better than D by 0.005 to 0.02, mainly because of D's willingness error. With 3 repeats, the difference may become clear. |

### 3. What the clarifying questions add

| | |
|---|---|
| Question | Does re-asking a fact after a contradiction make D more accurate? |
| Compare | D against D without re-asks (a fact can be asked only once) |
| Measure | avg error; on runs with an injected contradiction: recovery (share of runs where the estimate came back after the contradiction) and the share of contradictions caught |
| Data so far | None. **The code has no method without re-asks yet.** Somaditya must add one (for example "DN", where `MAX_ASKS_PER_FACT` = 1). |
| Prediction (AI test users, full run) | Small overall effect (under 0.01). Clear only for heavy-noise users, where re-asks raise recovery. At budget 5, re-asks may hurt, because each one uses up a question. |
| Prediction (real users, not tested in the full run) | The effect is larger for real people, because they contradict and correct themselves more often than the injected noise schedule, and one spoken answer moves the engine's belief a lot (fitted spread 0.05 to 0.10). Descriptive check: the live chat (P3) logs each re-ask and the band before and after it. We report the share of re-asks that changed the band in the classmate study. With 10 to 15 people, this is not a test of the claim. |

### 4. What each generative AI part adds

| | |
|---|---|
| Question | Does retrieval (DR), or reading the token probabilities (DP), read answers better than plain D? |
| Compare | D against DR; D against DP |
| Measure | avg error, system $ per profile |
| Data so far | Pilot readings: DR against D, willingness −0.012 (−0.025 to 0.000), behavior −0.005, not clear. DP against D: willingness +0.017, behavior +0.027 (worse), at 78% lower cost per answer. End to end, 5 users: D 0.168, DR 0.168, DP 0.178. |
| Prediction | DR: no clear difference in avg error from D; DR costs about 30% more per profile. DP: worse than D by 0.01 to 0.02, and costs about 60% less per profile. |

### 5. What the stop rule costs

| | |
|---|---|
| Question | If the system stops at the stop point, how much accuracy does it lose? |
| Compare | For C and for D: the profile at the stop point (`would_stop_at`) against the profile at the end of the budget |
| Measure | band exact at both points; share of runs where the band changes after the stop point (the promise is under 5%); avg error at both points; questions saved |
| Data so far | 100 test users, budget 10, C: the stop rule fired in 75 of 100 runs at question 6.5 on average. Band changed after it in 5% (D: 7%). Band exact 69% at the stop point, 72% at the end. Avg error 0.133 at the stop point, 0.103 at the end. |
| Prediction | C: the band changes after the stop point in 5% of runs or fewer. D: more than 5%, because the stop rule simulates D's remaining answers with the weaker form model, so it underestimates how much the band can still change and stops too early. Both lose 1 to 5 points of band exact at the stop point and save about a third of the questions. |

### 6. What the capacity formula adds

| | |
|---|---|
| Question | Is capacity from the formula better than the LLM's own capacity estimate? |
| Compare | capacity error of D (engine and `capacity.py`) against capacity error of D0 (the LLM's own estimate) |
| Measure | capacity error, capacity band exact |
| Data so far | 100 test users, budget 10: D capacity error 0.146. No D0 run on the 100 users yet. |
| Prediction | D's capacity error is clearly lower than D0's. |
| Caution | The true capacity of each test user is computed by the same formula (`capacity.py`) that D uses. So D has a built-in advantage. This test shows that the engine agrees with the truth label better than the LLM does, not that the formula measures real capacity better. Report it this way in Milestone 3. |

### 7. How much the results depend on the evidence strengths (proposed by Preyansh)

| | |
|---|---|
| Question | Do the conclusions change if we use the starting evidence strengths instead of the values fitted on the pilot users? |
| Compare | each method scored with `pilot/fitted.json` against the same recorded answers scored with the starting values in `belief.py` (no new API calls) |
| Measure | avg error for each method, and whether the order of the methods changes |
| Why | The fitted spoken strengths are very strong (spread 0.05 to 0.10). One spoken answer puts 75% of the belief within ±0.1 of the reading. The `belief.py` docstring asks for this report. |
| Data so far | 100 test users, D before the willingness fix: 0.129 with both settings. Pilot users, left out: D 0.107 → 0.089 with the fitted settings. |
| Prediction | The order of the methods does not change. D's avg error changes by less than 0.015. A and C change by less than 0.005. |
| Limit | C and D chose their questions with the fitted values. Re-scoring changes only how the answers are read, not which questions were asked. |

### 8. Is the stop point stable (proposed by Preyansh)

| | |
|---|---|
| Question | Does the stop point change if the engine simulates more futures? |
| Compare | `would_stop_at` with 100 simulated futures against 400 (`N_ROLLOUTS` in `belief.py`), on recorded runs |
| Measure | share of runs where the stop point differs; mean difference in questions |
| Why | Near the 5% limit, the decision depends on the random seed. In one test state, the engine stopped with 7 of 20 seeds. |
| Data so far | Only the seed test above. |
| Prediction | The stop point differs in 10% to 20% of runs, by less than 1 question on average. |
| Status | Depends on Somaditya's answer to the review. If he changes `N_ROLLOUTS` to 400 before the run, this test is not needed. |

## Methods in the full run

A, B, C, D, D0, DR, DP, and the new D without re-asks (test 3). C0 is not needed for these tests.

## Changes after this plan

- **Nov 14, test 7 (Somaditya).** The plan says the fitted spoken strengths are very strong (spread 0.05 to 0.10). That was the Nov 11 fit. The Nov 12 refit did not adopt the spoken settings (`pilot/fit.md`: they did not lower the error on left-out pilot users). So the full run used the fitted form values and the *starting* spoken values. A replay with the starting values cannot change D, DR or DN. So for D, DR and DN we replay with the fitted spoken values that were not adopted (`pilot/fit.md`). For A, B, C and DP we replay with the starting form values, as planned. The question of the test does not change.
- **Nov 14, test 8 (Somaditya).** Not run. `N_ROLLOUTS` was set to 400 in the Nov 12 review, before the run, so the plan says that this test is not needed.

## Results (full run, scored Nov 14)

File: `results/experiment_full.jsonl` (7,200 runs, no errors). Script: `python ablations_run.py results/experiment_full.jsonl`, output in `results/ablations.txt`. No new API calls. All differences are paired on the same test user, budget and repeat (300 pairs). "Clear" means that the 95% range does not include zero.

### Summary

| Test | Prediction held? | Main result (budget 10) |
|---|---|---|
| 1. Belief engine (D − D0) | Partly | D is clearly better at 10 and 15, D0 at 5. D costs 54% less, but it is only 1.4 times faster per turn, not 3 times. |
| 2. Conversation (D − C) | Size yes, reason no | C is clearly better at all budgets. The cause is D's capacity error, not willingness. |
| 3. Re-asks (D − DN) | No | Re-asks clearly help at 10 and 15, more at 15. The gain is on clean and moderate users, not heavy-noise users. They do not hurt at 5. |
| 4a. Retrieval (DR − D) | Yes | No clear difference at any budget. DR costs 25% more. |
| 4b. Token probabilities (DP − D) | Yes at 10 | DP is clearly worse at all budgets. It costs 77% less. |
| 5. Stop rule | C no, D yes | After the stop point, C's band changes in 8% of runs at 10 and 14% at 15 (promise: under 5%). D: 7% to 12%. |
| 6. Capacity formula (D − D0) | No | D0's own capacity estimate is clearly better at 5 and 10. D is better only at 15. |
| 7. Evidence strengths | Mostly | The order of the methods does not change at 10 and 15. At 5, C moves from 2nd to 4th. All changes are under 0.008. |
| 8. Stop-point stability | Not run | See "Changes". |

### 1. What the belief engine adds (D − D0)

| Budget | Avg error | Band exact | D system $ / D0 system $ | Wait per turn, D / D0 |
|---|---|---|---|---|
| 5 | +0.010 (+0.001 to +0.020), clear | −9.7 points, clear | $0.0062 / $0.0100 (38% less) | 1.23 s / 1.62 s |
| 10 | −0.022 (−0.032 to −0.013), clear | +6.0 points, not clear | $0.0126 / $0.0272 (54% less) | 1.24 s / 1.75 s |
| 15 | −0.054 (−0.066 to −0.043), clear | +16.3 points, clear | $0.0189 / $0.0504 (62% less) | 1.29 s / 1.76 s |

Prediction: no clear difference; D at least 50% cheaper and 3 times faster. **Result:** the difference is clear at every budget, and its sign changes with the budget. D0 is better with 5 questions. D is much better with 15, because D0 gets worse as the conversation gets longer (0.128, 0.137, 0.160). The cost part held at 10 and 15. The speed part did not hold: D is only 1.3 to 1.4 times faster per turn. The "4 times" came from 5 users.

### 2. What conversation adds (D − C)

| Budget | Avg error | Band exact | Willingness error | Behavior error | Capacity error |
|---|---|---|---|---|---|
| 5 | +0.008, clear | −3.3 points, not clear | −0.019, clear (D better) | +0.027, clear | +0.017, clear |
| 10 | +0.013, clear | −11.3 points, clear | −0.012, not clear | +0.005, not clear | +0.045, clear |
| 15 | +0.021, clear | −7.7 points, clear | +0.009, not clear | +0.009, not clear | +0.043, clear |

Prediction: C better by 0.005 to 0.02, mainly because of D's willingness error. **Result:** the size held (C is clearly better at all budgets). The reason did not hold. D's willingness error is now as good as C's or better (the Nov 11 fix worked). At 10 and 15, almost all of the gap is capacity. Conversation adds nothing to accuracy until D reads money facts as well as a form does.

### 3. What the re-asks add (D − DN)

| Budget | Avg error | Band exact | Heavy-noise users | Clean and moderate users | Contradictions caught, D / DN | Recovered, D / DN |
|---|---|---|---|---|---|---|
| 5 | −0.002, not clear | +0.0 points | +0.004, not clear | −0.005, not clear | 75% / 74% | 71% / 43% (24 and 23 runs) |
| 10 | −0.007 (−0.013 to −0.000), clear | +3.0, not clear | −0.005, not clear | −0.007, not clear | 60% / 53% | 50% / 48% |
| 15 | −0.017 (−0.024 to −0.009), clear | +9.3 points, clear | −0.013, not clear | −0.018, clear | 56% / 44% | 56% / 49% |

Prediction: small effect (under 0.01), clear only for heavy-noise users; may hurt at 5. **Result:** the effect grows with the budget and is clear at 10 and 15. The gain is clear for clean and moderate users, not for heavy-noise users (93 runs each budget, wide range). Re-asks do not hurt at 5. The prediction for real users is not tested here (classmate study).

### 4. What each generative AI part adds

| Budget | DR − D | DP − D | System $ per profile, D / DR / DP |
|---|---|---|---|
| 5 | −0.004, not clear | +0.042 (+0.034 to +0.050), clear | $0.0062 / $0.0077 / $0.0013 |
| 10 | −0.001, not clear | +0.024 (+0.017 to +0.031), clear | $0.0126 / $0.0157 / $0.0029 |
| 15 | +0.002, not clear | +0.017 (+0.009 to +0.024), clear | $0.0189 / $0.0236 / $0.0048 |

Prediction: DR no clear difference, about 30% more cost; DP worse by 0.01 to 0.02, about 60% less cost. **Result:** DR held (no clear difference, 25% more cost). DP held at 10 and 15 (+0.024 and +0.017); at 5 it is worse than predicted (+0.042). DP costs 74% to 79% less than D. Band exact: DP is 8 to 9 points lower than D at every budget, clear.

### 5. What the stop rule costs

The profile at the stop point (`would_stop_at`) against the profile at the end of the budget. "Band changed" counts only the runs where the stop rule fired.

| Method, budget | Stop fired | Band changed after the stop | Band exact, stop / end | Avg error, stop / end | Questions saved |
|---|---|---|---|---|---|
| C, 5 | 97 of 300 (q2.7) | 0.0% | 51% / 51% | 0.145 / 0.129 | 2.3 |
| C, 10 | 237 of 300 (q6.6) | **8.0%** | 68% / 71% | 0.127 / 0.103 | 3.4 |
| C, 15 | 289 of 300 (q8.1) | **14.2%** | 65% / 74% | 0.124 / 0.086 | 6.9 |
| D, 5 | 52 of 300 (q3.7) | 11.5% | 47% / 48% | 0.142 / 0.138 | 1.3 |
| D, 10 | 196 of 300 (q7.3) | 7.1% | 60% / 60% | 0.127 / 0.115 | 2.7 |
| D, 15 | 247 of 300 (q9.5) | 10.5% | 68% / 67% | 0.123 / 0.106 | 5.5 |

Prediction: C 5% or fewer; D more than 5%; both lose 1 to 5 points of band exact; both save about a third of the questions. **Result:** D held. C did not: its band changes after the stop point in 8% of runs at 10 and 14% at 15, so the "under 5%" promise fails for C too. At 15, C loses 9 points of band exact by stopping. The questions saved are a third to a half of the budget. The avg error is always higher at the stop point (by 0.004 to 0.038). This goes into the failure analysis: the stop rule is too confident.

### 6. What the capacity formula adds (D − D0, capacity only)

| Budget | Capacity error | Capacity band exact |
|---|---|---|
| 5 | +0.080 (+0.065 to +0.097), clear (D0 better) | −37 points, clear |
| 10 | +0.019 (+0.003 to +0.036), clear (D0 better) | −9 points, clear |
| 15 | −0.034 (−0.049 to −0.018), clear (D better) | +8 points, clear |

Prediction: D's capacity error clearly lower than D0's. **Result:** held only at 15. At 5 and 10, the LLM's own estimate is clearly better, although D uses the same formula that made the truth labels. So the formula is not the problem. The problem is how D gets the facts into it. D asks as many money questions as C (1.7, 3.8 and 5.8 per run at 5, 10 and 15; C: 1.8, 3.2 and 4.2), so the number of questions is not the cause. The weak part is the reading of spoken fact answers. This is the first item of the failure analysis. The caution in the test still applies.

### 7. Evidence strengths (same recorded answers, read again)

A, B, C and DP: as run (fitted form values) against the starting form values. D, DR and DN: as run (starting spoken values) against the fitted spoken values that were not adopted. See "Changes".

| Method | Budget 5 | Budget 10 | Budget 15 |
|---|---|---|---|
| A | 0.125 → 0.131 | 0.113 → 0.115 | 0.090 → 0.088 |
| B | 0.151 → 0.157 | 0.131 → 0.131 | 0.112 → 0.111 |
| C | 0.129 → 0.136 | 0.103 → 0.102 | 0.086 → 0.086 |
| DP | 0.180 → 0.183 | 0.139 → 0.142 | 0.123 → 0.123 |
| D | 0.138 → 0.135 | 0.115 → 0.117 | 0.106 → 0.109 |
| DR | 0.134 → 0.132 | 0.114 → 0.116 | 0.108 → 0.110 |
| DN | 0.140 → 0.140 | 0.122 → 0.126 | 0.123 → 0.129 |

A replay with the run's own values gives back the recorded profiles (largest difference 0.0001 on 70 runs). Prediction: the order does not change; D changes by under 0.015; A and C by under 0.005. **Result:** the order is the same at 10 and 15. At 5, C moves from 2nd to 4th (behind DR and D), but the gaps at 5 are under 0.007. D changes by 0.003 or less (held). A and C change by up to 0.007 at budget 5 (a little over the prediction) and by 0.002 or less at 10 and 15. Limit: the questions were chosen with the run's values; only the reading changes.

### What this means for Milestone 3

1. The belief engine makes D cheaper than D0 and much better in long interviews (test 1).
2. A form (C) with the same engine is still better than a conversation (D), and the gap is capacity (tests 2 and 6).
3. Re-asks help, and more with more questions (test 3).
4. Retrieval adds cost and no accuracy. Token probabilities save cost and lose accuracy (test 4).
5. The stop rule saves a third to a half of the questions, but its 5% promise does not hold for C or D (test 5).
6. The results do not depend on the evidence strengths (test 7).
