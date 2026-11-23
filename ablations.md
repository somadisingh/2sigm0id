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
- **Nov 15, test 5 (Somaditya, written after the run).** The prediction for D gives a reason that was out of date before the run: it says the stop rule simulates D's answers with the weaker form model. Since the Nov 12 review, D's belief uses its own spoken answer model to choose questions and to stop (`channel="spoken"` in `belief.py`). This entry should have been made before the run (plan task P2b); we make it now, after we saw the results. We keep the prediction ("D: more than 5%") as it was written, but we withdraw its reason. So D's result below holds as a number, but it does not support that reason. Plan P2b also listed tests 7 and 8; they are the two Nov 14 entries above.

## Follow-up tests 9 and 10 (Nov 22, written before the reruns)

These test the two fixes from the failure analysis (`failure_D_capacity.md`, `failure_analysis_2to4.md`). The settings were chosen on the full run's recorded answers, so only the new interviews test them.

**Engine changes (`belief.py`, both on by default from Nov 22):**

1. **Conflicting facts need a majority** (`CONFLICT_RULE = "majority"`). Clear spoken statements of a fact that agree form a group. Only a group with more than half of the statements counts. With no such group (for example one statement against one), the fact counts as not known until another statement decides. On the full run's recorded answers, this lowers D's capacity error from 0.164 to 0.159 at 10 questions and from 0.140 to 0.133 at 15, and helps every D method at every budget a little.
2. **The stop rule needs confidence** (`STOP_CONFIDENCE = 0.80`). Stop only when the change chance is under 5% *and* the engine gives its most likely band at least 80%. On the recorded runs, the band then changes after the stop in 0% to 3.4% of runs (C and D, 10 and 15 questions), against 7% to 14% before, and 1.1 to 3.7 questions per run are saved.

**Test-user change (noise version 3, `--fix-slips`, off by default):** when the interviewer asks to clarify a fact that the test user stated falsely (a planned contradiction), the test user says it was a mistake and gives the true value. Reason: in the full run, a planned contradiction could fire again on the clarifying question with the same wrong value, so in 74 facts the false value was stated more often than the true one. A person who misspoke would usually correct it when asked. This changes the test users after we saw the results, so we report it as a separate arm and never mix it with the full run. Check on 20 users (Nov 22): 8 of 8 corrections were read as the true value.

**Runs** (all 100 test users, 5/10/15 questions, 3 repeats; U054 is left out in the scoring):

- `results/rerun_engine.jsonl`: C, D, DN with the new engine and the old noise.
- `results/rerun_fixslips.jsonl`: D with the new engine and noise version 3.

**Test 9: what the engine changes do** (rerun_engine against the full run, paired). Predictions: D's capacity error is lower by 0.003 to 0.010 at 10 and 15 questions; D's avg error is lower by 0.001 to 0.005 (may not be clear). DN gains less than D, because it cannot re-ask. C's avg error changes by less than 0.005 (forms get no contradictions; only the questions after the stop change). The band changes after the stop point in under 5% of runs for C and D at every budget.

**Test 10: what realistic slips do** (D in rerun_fixslips against D in rerun_engine, paired: same users, repeats and noise seeds). Predictions: D's capacity error on heavy-noise users is lower by at least 0.03 at 15 questions; D's avg error at 10 and 15 is lower by 0.005 to 0.015; D is still not clearly better than C at 10 questions.

## Results of tests 9 and 10 (scored Nov 22)

Full numbers: `results/rerun_compare.txt` (made by `rerun_compare.py`). 2,700 + 900 interviews, no errors. Each value is the rerun minus the earlier run, paired, with a 95% range. Negative means the rerun is better. Note: the rerun is a new set of interviews, so each difference also contains run-to-run chance, not only the change.

**Test 9 (engine changes):**

| Prediction | Result | Held? |
|---|---|---|
| D capacity lower by 0.003 to 0.010 at 10 and 15 | −0.001 at 10, −0.001 at 15, not clear | No. The replay gain (0.005 to 0.007) did not show in new interviews. |
| D avg error lower by 0.001 to 0.005 | −0.002 at 10, −0.001 at 15, not clear | Yes in size, but not clear |
| DN gains less than D | DN gained more: avg error −0.007 at 15 (clear) | No |
| C avg error changes by less than 0.005 | +0.005 at 5 (clear), +0.003 at 10, +0.002 at 15 | Mostly. C became a little worse; C capacity at 10 is +0.011 (clear). Cause (checked): the conflict rule does not touch forms. The confidence floor keeps C longer in "settle the band" mode, so it asks fewer questions that sharpen single scores (24% → 16% of turns at 10). Where C asked the same questions in both runs, the capacity change is 0.000. |
| Band changes after the stop in under 5% (C and D, every budget) | C 0.0% / 1.1% / 4.3%; D 0.0% / 2.2% / 3.0% (full run: 0% to 14.3%) | **Yes** |

The stop rule fix works: the stop is now safe, and it still saves 1.0 to 3.9 questions per run at 10 and 15 questions. The conflict rule gives no clear gain in new interviews.

**Test 10 (noise version 3, D only):**

| Prediction | Result | Held? |
|---|---|---|
| Heavy-noise users' capacity lower by at least 0.03 at 15 | −0.023 (−0.053 to +0.007), not clear | No (right direction, smaller) |
| D avg error lower by 0.005 to 0.015 at 10 and 15 | −0.003 at 10, −0.006 at 15, both not clear | Partly (15 only, not clear) |
| D still not clearly better than C at 10 | D(v3) − C = +0.005, not clear | Yes |

With realistic slips, D's capacity error is clearly lower at 10 questions (−0.015) and lower at 15 (−0.011, not clear). The test users made 124 corrections on re-asks. D still does not beat the forms on avg error: at 15 questions D(v3) is worse than C (+0.011, clear) and A (+0.010, clear). D's exact-band rate at 10 questions stays clearly higher than A's (+0.178).

**What this means for the final report:** (1) the stop rule is now reliable (under 5% at every budget for C and D); (2) part of D's capacity gap came from the test users repeating false facts, not from the interviewer; (3) even so, the adaptive interviewer is not more accurate than the forms on avg error. Its gain is the exact band at 10 questions.

## Follow-up tests 11 to 13 (Nov 22, written before the results)

Two generative AI parts that were agreed on Nov 13 (`plan.md`, "Waiting to-dos"), and one stop-rule fix from `failure_analysis_2to4.md` section 4 (fix 2). Each is tested against the engine of Nov 22 (tests 9 and 10).

**Test 11: embedding retrieval for DR** (no new interviews). `retrieval.py` finds labeled pilot answers that look like a new answer, and DR shows them to the extractor as examples. Until now the search was BM25 (word overlap). The new search uses an embedding model (all-MiniLM-L6-v2: it turns a text into 384 numbers that capture its meaning, so "half a year of savings" is near "six months saved"). Test on the 290 labeled pilot answers, never using examples from the same pilot user:

- (a) Label distance, no API calls: for each answer, how far the labels of the 3 retrieved examples are from its own label (0 to 1 scale), for BM25, the embedding search and random examples. Prediction: both are better than random. The embedding search is better than BM25 on willingness and behavior (answers in different words), and about the same on money facts (numbers decide those, and embeddings handle numbers poorly).
- (b) Extraction, `pilot.py extract-eval` (about $0.30): DR with each search on the same answers. Prediction: no clear difference in fact accuracy (within 3 points) or score error (within 0.02). The pool is small (10 pilot users), so the best example is often the same for both searches.

**Test 12: AI-written questions (new method DW).** The engine still chooses what to ask (the same as D). GLM then words the question from the conversation so far, instead of using the bank's fixed spoken wording, so the interview reads like a conversation. Everything else is the same as D: re-asks, extractor, engine (Nov 22), noise version 2. Run: all 100 test users, 5/10/15 questions, 3 repeats, paired with D in `results/rerun_engine.jsonl` (same users, repeats and noise seeds). A trial on 20 users comes first. Predictions:

- Accuracy: DW's avg error is within 0.01 of D's at every budget (not clearly different). Reason: the engine and the extractor are the same; only the wording changes.
- Leading questions: a judge from another company (Nemotron 3.5 Super) reads the bank wording and the written wording of the same questions and says if each hints at an answer. Written questions are flagged more often than bank questions, but in under 10% of cases.
- Acquiescence: the test users with "acquiescence" noise agree with what a question suggests. On their turns, DW's error is not clearly higher than D's.
- Cost and speed: one more GLM call per question. The cost per interview is 30% to 60% higher than D, and each question takes 1 to 4 seconds longer.

**Test 13: one band rule everywhere** (no new interviews). The score, the app and the live chat report the lowest of the three bands of the mean scores. The stop rule used the most likely band of the engine's final-band distribution, and the two differ in about 11% of D's stop points. The change: the stop rule, its 80% confidence floor and the live chat's "most likely band" all use the reported band (`BAND_RULE = "reported"` in `belief.py`). Test: replay the engine on the recorded answers of `results/rerun_engine.jsonl` (C and D) and recompute the stop point. Predictions: the band changes after the stop in under 5% of runs for C and D at every budget (as in test 9), D's rate goes down, C's changes by under 1 point (C's two rules rarely differ), and the questions saved per run change by under 0.5. Caveat: in a real run the questions after the stop point would differ a little (as in test 9).

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
| 5. Stop rule | C no, D yes (number only, reason withdrawn) | After the stop point, C's band changes in 8% of runs at 10 and 14% at 15 (promise: under 5%). D: 7% to 12%. |
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

Prediction: C 5% or fewer; D more than 5%; both lose 1 to 5 points of band exact; both save about a third of the questions. **Result:** D's number held (7% to 12%), but its written reason no longer applies (see "Changes", Nov 15). C did not hold: its band changes after the stop point in 8% of runs at 10 and 14% at 15, so the "under 5%" promise fails for C too. At 15, C loses 9 points of band exact by stopping. The questions saved are a third to a half of the budget. The avg error is always higher at the stop point (by 0.004 to 0.038). Both methods miss the promise, so the cause is the stop rule itself, not D's answer model. This goes into the failure analysis: the stop rule is too confident.

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

## Results of tests 11 and 13 (scored Nov 22)

**Test 11: embedding retrieval** (`retrieval_eval.py` → `results/retrieval_eval.txt`; `pilot.py extract-eval --readers D DR DRE` → `results/test11_extract.txt`, $1.17 at list price, more than the $0.30 we expected).

(a) Label distance of the 3 retrieved examples (lower is better):

| Answers | Random | BM25 | Embedding |
|---|---|---|---|
| Money facts (60) | 0.440 | **0.344** | 0.380 |
| Willingness (120) | 0.283 | **0.226** | 0.274 |
| Behavior (110) | 0.383 | **0.296** | 0.317 |
| All (290) | 0.353 | **0.277** | 0.312 |

Prediction: the embedding search is better on willingness and behavior. **It did not hold.** Both searches are better than random, but BM25 is better everywhere. A likely cause: we embed the question with the answer, as BM25 does, and all pool answers to one question share the same question text, so the embedding mostly finds "the same question" and not "the same stance". Added after we saw the result (not a planned test): embedding the answer only gives 0.286 overall (willingness 0.259, behavior 0.268, money facts 0.375). That is better than BM25 on behavior only.

(b) Extraction with the retrieved examples (DRE = DR with the embedding search), paired on the same 290 answers:

| Reader | Facts right (50) | Willingness error | Behavior error |
|---|---|---|---|
| D (no examples) | 0.88 | 0.105 | 0.085 |
| DR (BM25) | 0.82 | 0.096 | 0.081 |
| DRE (embedding) | 0.84 | 0.093 | 0.086 |

DRE − DR: willingness −0.003 (−0.010 to +0.004), behavior +0.006 (−0.005 to +0.020), facts +1 answer of 50. Prediction (no clear difference): **held.** Decision: DR keeps BM25 (`config.RETRIEVAL_SEARCH = "bm25"`). The embedding search stays in `retrieval.py` as an option. With only 10 pilot users in the pool, retrieval has little room to help; a bigger labeled pool (for example the classmate answers) is the better next step.

**Test 13: one band rule everywhere** (`band_rule_replay.py` → `results/band_rule_replay.txt`, no API calls). The replay with the old rule gives the recorded stop point in 100% of runs, so the replay is exact up to the stop point.

| Method, questions | Band changes after the stop: old rule → reported band | Questions saved per run |
|---|---|---|
| C, 5 | 0.0% → 0.0% | 0.45 → 0.33 |
| C, 10 | 1.1% → 0.0% | 1.71 → 1.34 |
| C, 15 | 4.3% → 1.9% | 3.95 → 3.58 |
| D, 5 | 0.0% → 0.0% | 0.08 → 0.04 |
| D, 10 | 2.2% → 0.0% | 0.96 → 0.77 |
| D, 15 | 3.0% → 3.0% | 3.13 → 2.83 |

Predictions: under 5% everywhere: **held**. D's rate goes down: held at 10 questions, the same at 15. C changes by under 1 point: **did not hold**, C at 15 improved by 2.4 points. Questions saved change by under 0.5: **held** (0.04 to 0.37 fewer). Decision: `BAND_RULE = "reported"` is the default from Nov 22. The stop rule, the live chat and the score now use one band. Caveat: in a new run the questions after the stop point would differ a little.

## Results of test 12 (scored Nov 23)

`written_compare.py` → `results/written_compare.txt`. 900 DW interviews (`results/rerun_written.jsonl`), no errors, paired with D in `rerun_engine.jsonl`. U054 is left out. Note: the DW run started before the band rule of test 13 was changed, so it used the same engine as D (`BAND_RULE = "mode"`); the pairing is fair. GLM wrote 7,560 questions; 14 fell back to the bank wording.

| Prediction | Result | Held? |
|---|---|---|
| Avg error within 0.01 of D, not clearly different | 5: −0.002 (not clear); 10: **−0.007 (−0.014 to −0.001, clear)**; 15: +0.004 (not clear) | Within 0.01: yes. Not clearly different: no. DW is clearly better at 10 questions, and its exact band is 5.4 points higher there (clear). |
| Written questions flagged as leading more often than bank questions, but in under 10% | bank 0.0%, written 12.9% (judge, 209 of 300 sampled questions; earlier judge versions gave 10.3% and 10.5%) | **No** (slightly over 10%) |
| Acquiescence: DW not clearly worse than D on those users | 5: +0.001, 10: −0.005 (not clear); 15: **+0.011 (clear)** | Yes at 5 and 10, **no at 15** |
| Cost 30% to 60% higher | $0.0197 vs $0.0139 per interview (+42%, list price) | Yes |
| Each question 1 to 4 s slower | +0.38 s of system time per question (1.70 vs 1.32 s) | No: faster than we expected |

**What the leading questions are.** Most flagged questions open by restating an earlier answer: "Since you're leaning toward growth, how much of this money would you feel okay putting into stocks?" A check in code (no judge) finds such an opening in 12.4% of the 7,560 written questions. This can push a person to answer in line with what they said before, so it can hide a real mismatch between what people say and what they do, which is the thing the profiler must find. The effect on acquiescence users at 15 questions (longer conversations have more to restate) fits this.

**Judge note.** With a separate system message, Nemotron 3.5 Super often replied that it could not see the question; we now send one message, and retry up to 3 times. It still gives no usable answer for about 30% of the questions, and some flags look wrong ("Got it, thanks. Now, say you put in $10,000 ..."). So we report the judge's rate together with the code check, which agrees (12.9% and 12.4%).

**Against the forms:** DW − C is +0.001 at 10 questions (not clear; D − C was +0.008, clear) and +0.022 at 15 (clear). **Stop rule (DW, old band rule):** the band changes after the stop in 13.8% (4 of 29), 2.0% and 5.6% of runs.

**Decision for the final report.** DW is the clearest generative AI part of the interviewer: it is at least as accurate as D (better at 10 questions), for 42% more cost. Its weak point is that 12% of its questions restate an earlier answer. A next step (not tested): tell the writer not to mention earlier answers, and rerun DW (about $13 and 2.5 hours).

## Follow-up test 12b (Nov 23, written before the rerun)

**Change:** writer prompt version 2 for DW (`config.WRITE_PROMPT_VERSION = 2`). The writer must not mention, repeat or sum up anything the person said earlier; it may only use a short neutral link ("Okay.", "Next,") and plain words. Everything else is the same as test 12, including the old band rule (`BAND_RULE = "mode"`), so that DW v2 pairs with D and with DW v1. Run: `results/rerun_written_v2.jsonl`, 900 interviews.

Predictions:

- Questions that open by restating an earlier answer (code check): under 2% (v1: 12.4%). Judge's leading rate under 5% (v1: 12.9%).
- On acquiescence users at 15 questions, DW v2 is not clearly worse than D (v1: +0.011, clear).
- Avg error: within 0.01 of D at every budget. The gain at 10 questions may shrink (if it came from linking to earlier answers) or stay (if it came from plainer wording); we don't predict which.
- Cost about the same as DW v1 (+40% over D).

## Results of test 12b (scored Nov 23)

Run: `results/rerun_written_v2.jsonl`, 900 interviews, 0 errors. Scores: `results/written_compare_v2.txt`. Pairs are with D in `rerun_engine.jsonl` (n=297 per budget, U054 left out). Negative = DW v2 better.

| Questions | Avg error, DW v2 − D | Exact band, DW v2 − D | DW v2 − DW v1 (avg error) |
|---|---|---|---|
| 5 | −0.003 (not clear) | +4.0 points (not clear) | −0.000 (not clear) |
| 10 | +0.001 (not clear) | **+5.1 points (clear)** | **+0.008 (clear, v2 worse)** |
| 15 | −0.004 (not clear) | +0.3 points (not clear) | **−0.009 (clear, v2 better)** |

Predictions:

- **Restating: held.** 0.0% of 7,473 written questions open by restating an earlier answer (v1: 12.4%).
- **Leading: held.** The judge flagged 1.8% of written questions and 0.5% of the bank wording (218 of 300 sampled questions judged; v1: 12.9%). It flagged 4 written-only and 1 bank-only. The flagged examples are near-copies of the bank wording ("Okay, when markets are going down, ..."), so most of the 1.8% is judge noise, not real hints.
- **Acquiescence users at 15: held.** −0.004 against D (not clear); v1 was +0.011 (clear). Against v1 the change is −0.015 (clear).
- **Avg error within 0.01 of D: held** at every budget. The avg-error gain at 10 questions did not stay: −0.007 (clear) in v1, +0.001 now. So that gain most likely came from linking to earlier answers, the same thing that made v1 leading. The exact-band gain at 10 stays (+5.1 points, clear).
- **Cost: held.** $0.0194 per interview against $0.0197 for v1 and $0.0139 for D (+40%). System time 2.00 s per question against 1.32 s for D.

Other results:

- DW v2 − C: −0.001 at 5 (not clear), +0.009 at 10 (clear), +0.013 at 15 (clear). The forms stay ahead at 10 and 15, as for D.
- Stop rule (old band rule, kept for pairing): band changes after the stop in 11.1% at 5 (3 of 27), 1.2% at 10, 4.2% at 15. The 5-question figure is from very few stops; test 13 showed the reported band rule brings D under 5% at every budget.

**Decision:** DW v2 is the safe version of the AI-written questions: no leading wording, no loss against D, better band hits at 10 questions, about 40% more cost. It is not clearly better than D on avg error, so the app stays on D and the report gives DW v2 as a tested option.
