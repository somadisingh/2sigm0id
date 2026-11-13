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

_(none yet)_
