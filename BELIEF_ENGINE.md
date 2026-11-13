# Belief engine

The belief engine (`belief.py`) answers the professor's first Milestone 2 question: how the system chooses the next question, how it measures uncertainty, and how it decides that another question is unlikely to change the final band.

Code holds the beliefs, chooses each question and decides when to stop. The LLM does only language work: it turns spoken answers into evidence and writes clarifying questions. Methods C and D share the engine, and methods A and B use it to score their answers. So all methods turn answers into a profile with one rule.

## How it works

1. **Beliefs.** Willingness and behavior are each a probability distribution over the 0–1 scale. A wide distribution means the engine is unsure. Every method starts from the same flat prior.
2. **Capacity.** Each money fact (horizon, emergency savings, income, debt, dependents) has its own distribution. The engine draws 2,000 samples of the five facts and runs the capacity formula (`capacity.py`) on each sample. Facts that nobody asked about stay uncertain, so capacity stays uncertain too.
3. **Evidence strength.** Each answer narrows one distribution. A past action is the strongest evidence, a stated feeling is weaker, and an answer about an imagined situation is the weakest. A vague answer counts half as much. A fixed lapse rate (10%) means that one answer can never rule a value out completely.
4. **Final band.** The engine combines the three distributions with the lowest-of-three rule. The result is a probability for each band, for example "band 2: 70%, band 1: 25%".
5. **Next question.** For each candidate question, the engine simulates the possible answers and calculates how much each answer would reduce the uncertainty about the final band (expected information gain). It asks the question with the highest gain.
6. **Stop rule.** Before each question, the engine simulates 100 possible futures. Each future draws a "true" person from the current belief, simulates the remaining questions and checks the final band. If the band changes in fewer than 5% of the futures, the band is settled. This rule is called stochastic curtailment. In the main experiment the engine keeps asking: it logs the stop point as `would_stop_at` and then asks the questions that most reduce the error on each score.
7. **Contradictions.** Two statements of a fact that disagree leave both values possible, so the distribution for that fact becomes wide. If the fact can change the band, a clarifying question then has the highest gain, so method D asks it. A statement is flagged as a contradiction only when it disagrees with most of the earlier clear statements of the same fact.
8. **Mismatch.** The engine flags a mismatch when the estimated scores are 2 or more bands apart and the chance of a mismatch is at least 60%.

## The professor's example

The person says that they like risk (willingness about 0.8). Their behavior answers are near the band 1/2 edge, and their capacity is high. Behavior decides the band. The engine asks the past-behavior question (BEH02) next. Its expected gain is 0.29 bits. Another willingness question has a gain of 0.00, because it cannot change the band. `test_belief.py` checks this case.

## LLM roles in method D

| Step | Done by | Calls |
|---|---|---|
| Choose the question, track beliefs, stop, flag | code (`belief.py`) | 0 |
| Word a new question | bank wording (`spoken`) | 0 |
| Turn the answer into evidence (fact ranges, scores, past or imagined, clear or vague) | LLM extractor | 1 per answer |
| Word a clarifying question when the engine re-asks a fact | LLM writer | 1 per re-ask |

## Methods

| Method | Chooses questions | Reads answers |
|---|---|---|
| A fixed form | fixed order | option number |
| B scripted interview | fixed order | LLM maps speech to an option |
| C adaptive form | belief engine | option number |
| D adaptive interviewer | belief engine, may re-ask facts | LLM extracts evidence from speech |
| C0 (earlier C) | hand-made rule | option number |
| D0 (earlier D) | the LLM, prompt v1 | the LLM |

A, B, C and D form the 2×2 design. C and D differ only in conversation. D0 against D shows what the engine adds over prompting alone.

## First check (Nov 11, 5 test users, budget 10, one run each)

| | avg error | band within 1 | system $ / profile | wait per turn |
|---|---|---|---|---|
| C, engine | 0.129 | 100% | $0 | 0 s |
| D, engine, run 1 | 0.174 | 100% | $0.011 | 2.1 s |
| D, engine, run 2 (contradiction flag fix) | 0.114 | 100% | $0.011 | 1.8 s |
| D0, LLM only (Nov 6 run) | 0.107 | 100% | $0.029 | 9.2 s |

These are 5 runs each. The two D runs differ by 0.06, so these numbers don't rank the methods. Run 2 raised 2 contradiction flags, against 8 in run 1, and still caught 2 of the 3 injected contradictions. Engine D costs 62% less than D0 and is 4 times faster per turn. One finding: for P3 ("talks big, panics"), the simulated user answered the willingness questions with panic, and engine D's extractor scored the answers as given (willingness error −0.60). C's forced-choice form kept the two scores apart.

## Generative AI parts in method D

The professor said that prompt chaining alone is not sufficient. In D, the LLM reads language and code makes the decisions. We added three parts to the reading step. Each part has its own measured test. The tests use the labeled answers of the 10 pilot users (`python pilot.py ...`). The labels come from the pilot users' true profiles, not from an LLM. Pilot users are never scored in the experiment.

| Part | Course topic | What it does | Method |
|---|---|---|---|
| Retrieval | Retrieval-augmented generation | Before GLM reads an answer, `retrieval.py` finds the 3 most similar labeled pilot answers about the same topic. GLM sees them as worked examples. | DR |
| Token probabilities | Next-token prediction, decoding, calibration | GLM picks the matching option with one letter. We read its probability for every option, correct the probabilities with one temperature value fitted on the pilot fact answers, and use them as soft evidence. | DP |
| Faithfulness test | Evaluating generative AI, hallucination tests | A judge model from another company checks each reading against the answer and quotes its support. Code checks that the quote is in the answer. | `check_extractor.py` |

**Calibration (DP).** GLM's raw option probabilities were too confident. On the 50 pilot fact answers (after the leak fix), it picked the right option 86% of the time, but its stated confidence was higher (calibration error 0.151). A temperature of 2.5 brought the calibration error down to 0.106, and the accuracy did not change. (Before the leak fix: 82% right, calibration error 0.176 → 0.045 with a temperature of 2.75.) We fitted the temperature on fact answers only, because only there the correct option is known exactly. Source: `pilot/calibration.json`.

**A scale error that the tests found.** The first extractor prompt put "holds calmly or buys more" at 1.0. The question bank and the test users put "holds" at about 0.7 and only "buys more" at about 0.9. So the extractor read "I held on" as 1.0. The faithfulness test showed many of these readings as unsupported. We gave the extractor five points of the scale (0.1, 0.3, 0.5, 0.7, 0.9). At first, these points used the test users' own band wording. That let the extractor decode the band from the words, so on Nov 11 we changed them to neutral wording with the same meaning. On the same day we removed the "20% in a month" leak from the test users' instructions and rebuilt all pilot answers. The scale fix did more than retrieval did:

| Reader, 290 labeled pilot answers | facts right | willingness error | behavior error | past or imagined right | $ per answer |
|---|---|---|---|---|---|
| D, old scale | 88% | 0.137 | 0.114 | 87% | $0.00092 |
| DR, old scale | 88% | 0.100 | 0.093 | 96% | $0.00121 |
| **D, fixed scale** | 88% | **0.120** | **0.087** | 91% | $0.00105 |
| **DR, fixed scale** | 86% | **0.104** | **0.093** | 97% | $0.00134 |
| DP, token probabilities | 82% | 0.125 | 0.131 | – | $0.00024 |
| **After the leak fix, neutral scale (current)** | | | | | |
| D | 90% | **0.115** | **0.085** | 94% | $0.00103 |
| DR, retrieval | 86% | 0.103 | 0.082 | 96% | $0.00131 |
| DP, token probabilities | 88% | 0.132 | 0.116 | – | $0.00023 |

With the old scale, retrieval cut the willingness error by 0.038 and the behavior error by 0.020. Most of that gain came from examples that showed the correct scale. Now, retrieval does not clearly help: willingness −0.012 (95% range −0.025 to 0.000), behavior −0.005 (−0.028 to +0.012). Token probabilities cost 78% less per answer than D, but their errors are higher: willingness +0.017 (0.004 to 0.031), behavior +0.027 (0.014 to 0.040). The neutral scale did not make D less accurate. DR never sees examples from the same pilot user. Source: `pilot/extract_eval.md`.

**End to end** (5 test users, budget 10, 2 runs each, old scale): D 0.168, DR 0.168, DP 0.178 avg error. DP costs $0.0042 per profile, D $0.0111 and DR $0.0143. At this size the three are tied on accuracy.

**The judge needs a check too.** We ran the judge (Nemotron 3.5 Super) on the same 150 readings two times with the same settings. The two runs agreed on only 85% of the readings. With thinking off, the judge marked 25% of the readings as unsupported, and most of these marks were wrong (for example, "I have no dependents" read as 0 dependents). With thinking on, it marked 11%, and many marks were still wrong. So the faithfulness numbers are not final. Before we report them, two team members must label 50 readings by hand, and we report how often the judge agrees with them. `check_extractor.py` now uses thinking by default. The hand-labeling sheet is `pilot/label_readings.csv`.

**First hand labels (Preyansh, Nov 12, 49 readings; `pilot/label_readings_preyansh.csv`).** The judge with thinking agreed with him on 84% of the readings. It was too lenient 6 times (it said "supported" where he said "no") and too strict 2 times. With thinking off, the judge agreed on only 69% to 71%, mostly because it was too strict. Half of the sheet comes from readings that the judge doubted, so 84% is not the judge's accuracy on all readings. Most of his "no" labels say the same thing as the judge's pattern below: the answer does not say what the person would actually do. Siya's labels will show how often two people agree.

**Both sets of hand labels (Nov 13).** Siya and Preyansh agreed with each other on 78% of 49 readings (Cohen's kappa 0.33, "fair"), so these readings are hard to judge even for people. On the 38 readings where both people agree, the judge with thinking gave the same answer on 37 (97%). It agreed with Siya on 88% and with Preyansh on 84%. With thinking off it agreed on only 76% of the 38, always by being too strict. So we use the judge with thinking, and its faithfulness results can be reported, with the human agreement as the limit. Files: `pilot/label_readings_preyansh.csv`, `pilot/label_readings_siya.csv`.

One pattern holds in every judge run. Behavior readings that the extractor takes from an answer to a different question ("volunteered") are the least supported: the judge doubted 36% (D) and 47% (DR) of them. Readings about the question's own topic look sound (1% for willingness, 6–10% for facts). A possible fix is to count volunteered readings as vague evidence. We test this only after the hand labels confirm the pattern.

## Changes after Preyansh's review (Nov 12)

Preyansh approved the engine (task P1) with these changes. The tests now number 12.

1. **More simulated futures for the stop rule: 400 instead of 100.** We took 12 states from the 100-user run where the band was close to the 5% stop line. We judged each state with 20 random seeds. With 100 futures, the stop decision changed with the seed in 11 of the 12 states. With 400, it changed in 8, and the noise of the estimate is half as large (about ±1 point at 5%). Close to a threshold, some seed effect always stays. A question choice now takes about 100 ms.
2. **D chooses questions with the same answer model that it updates with.** Before, D chose questions as if each spoken answer were a form answer, but it updated with the spoken settings. Now one formula (`spoken_likelihood`) does both, for a reading on a 0-to-1 grid of 21 points. A test checks that the update and the choice model give the same belief. Form answers keep the option model. With the fitted settings, one spoken reading puts 63% of the belief within ±0.1 of the reading, and one form answer 51%.
3. **"Settled" can reset.** Before, once the band was settled, the engine stayed in "sharpen" mode, even after a contradiction. Now it decides again before each question. `would_stop_at` still records the first stop point.
4. **Extractor.** "stable and high" is now an income answer. The extractor can record "never had a big loss", and a later loss story then counts as a contradiction (the U015 case). The answer options shown to the extractor now use the same 0.1-to-0.9 scale as its instructions.
5. **Spoken settings: starting values, with a new order.** Preyansh asked to use starting values for real people, because the fitted spoken values come from AI test users who are very consistent. The first starting guess made a past action the strongest spoken evidence (spread 0.15). With change 2, D then chose past-loss questions again and again, and its behavior error doubled (20-user check below). Both pilot fits show that past actions are not the strongest evidence. So the spoken starting values are now the fitted form values: stated 0.15, imagined 0.15, past 0.20, lapse 0.10. The refit did not adopt the fitted spoken values (left-out pilot users: D 0.083 with the starting values, 0.087 fitted). The experiment, the live chat and the classmate study all use these starting values. The form settings stay fitted.
6. **Pilot check after the changes.** The extractor's willingness error went from 0.115 to 0.106 and its behavior error from 0.085 to 0.083. Facts read correctly went from 90% to 86%: two answers like "pretty steady, I'm an engineer" are now read as "stable", not "very stable". These answers fit both levels.

7. **When D asks a question again.** A money-fact question can be asked again, up to 3 times in all; a second statement protects the estimate against a vague or false answer. The past-loss question (BEH02) is asked again only after a vague answer (once) or a flagged contradiction, because people repeat the same story, and the engine would count the repeat as new evidence.

D0 stays in the experiment as the main baseline. MAX_ASKS_PER_FACT = 3 stays.

**20-user checks of D after the review** (the same 20 test users, 4 per band, budget 10, one run each, about $0.25 each):

| D version | avg error | capacity | willingness | behavior | band exact | re-asks |
|---|---|---|---|---|---|---|
| before the review (Nov 11) | 0.115 | 0.132 | 0.119 | 0.094 | 45% | 33 |
| review changes, past = strongest spoken evidence | 0.145 | 0.139 | 0.109 | 0.186 | 60% | 51 (28 of BEH02) |
| + re-ask only when unclear | 0.171 | 0.193 | 0.133 | 0.186 | 45% | 18 |
| + new spoken starting values | 0.132 | 0.215 | 0.096 | 0.087 | 60% | 17 |
| + vague answers re-asked once | 0.131 | 0.208 | 0.093 | 0.092 | 55% | 15 |
| **+ money facts re-askable (final)** | **0.113** | 0.180 | **0.081** | **0.078** | 55% | 31 (0 of BEH02) |
| C, adaptive form (Nov 11) | 0.100 | 0.101 | 0.112 | 0.088 | 75% | – |

Final D against D before the review, paired on these 20 users: −0.002 (95% range −0.024 to +0.024). Two runs of nearly the same D differed by 0.035 per user on average, so 20 users can only show large changes. Re-scoring each run's recorded evidence with other settings changed the avg error by at most 0.015, so the differences between rows come from which questions D asked.

**Open problem: D's capacity.** D estimates willingness and behavior better than every other method on these 20 users, but its capacity error (0.180) is worse than C's (0.101). D's fact readings come from speech (86% to 90% read right on the pilot users), and only spoken methods get injected contradictions about facts. This is the first item for the failure analysis after the full run.

## Run on all 100 test users (Nov 11, budget 10, one run each)

This run used the fixed test-user wording (no leak), the fitted settings and no backstories. It cost $1.83. It is a preview: the full run has 3 repeats and budgets 5, 10 and 15. File: `results/experiment_100users_b10.jsonl` (not in git).

| Method | avg error | capacity | willingness | behavior | band exact | system $ | wait per turn |
|---|---|---|---|---|---|---|---|
| A fixed form | 0.122 | 0.169 | 0.098 | 0.097 | 47% | $0 | 0 s |
| B scripted interview | 0.129 | 0.186 | 0.106 | 0.094 | 45% | $0.0031 | 1.3 s |
| **C adaptive form** | **0.104** | **0.120** | 0.111 | **0.082** | **68%** | $0 | 0 s |
| D adaptive interviewer | 0.129 | 0.146 | 0.148 | 0.093 | 51% | $0.0113 | 2.0 s |

Paired against A on the same 100 users (`score.py` now prints this table):

| Method | avg error vs A | 95% range | band exact vs A |
|---|---|---|---|
| B | +0.007 | −0.002 to +0.016 | −2 points |
| **C** | **−0.017** | **−0.029 to −0.005** | **+21 points** |
| D | +0.007 | −0.010 to +0.026 | +4 points |

Findings:

- **The belief engine works with a form.** C is better than A, and the range excludes zero. Most of the gain is in capacity and in band 4 and 5 users (C 0.097 and 0.086, A 0.128 and 0.152).
- **The stop rule keeps its promise.** C's stop rule fired in 75 of 100 runs, at question 6.5 on average. After that point the final band changed in only 5% of the runs (D: 7%). The promise was "under 5%". Stopping there saves a third of the questions. The band was exactly right in 69% of these runs at the stop point and 72% at the end. The scores are less precise at the stop point (avg error 0.133 against 0.103), because the rule protects only the band.
- **D is only as good as A, because of willingness.** On clean test users, D equals C (0.084 against 0.083). D's willingness estimates are too low for users whose scores disagree: −0.19 for "says aggressive, would panic-sell" and −0.17 for "says aggressive, can't afford it". C has no such error for the same users. The cause has two parts. In conversation, these AI test users bring their behavior into attitude answers ("they'd say I talk a big game about being brave, but they've seen me panic"). The extractor then scores this as low willingness, although by our definition what the person says about their attitude is high. This is the professor's Milestone 1 question about separating willingness from behavior. A form forces the person to answer the attitude question alone.
- **The fitted settings did not cause this.** We scored D's recorded evidence again with the starting settings: the avg error stayed at 0.129.
- **Fix: the extractor scores what the person claims.** The willingness rule now says: score their stated attitude and how they describe themselves, even if they also say that they would act differently or cannot afford it; actions go to behavior, money limits to the facts. We checked the fix first on the pilot users. There it changed little and harmed nothing: willingness error 0.112 → 0.110, behavior error 0.085 → 0.076, and the low bias for panic-sell pilot users went from −0.053 to −0.041. Then we ran D again on the 100 test users (one run, $1.20):

| | D before fix | D after fix | C |
|---|---|---|---|
| avg error | 0.129 | **0.116** | 0.104 |
| willingness error | 0.148 | 0.131 | 0.111 |
| willingness bias, "says aggressive, would panic-sell" (13 users) | −0.191 | **−0.051** | +0.037 |
| willingness bias, "says aggressive, can't afford it" (12 users) | −0.169 | −0.121 | −0.024 |
| willingness bias, no mismatch (65 users) | −0.070 | −0.061 | +0.023 |
| band exact | 51% | 53% | 68% |

  Paired on the same users: D after the fix against D before, −0.013 (95% range −0.028 to +0.001); against A, −0.006 (−0.019 to +0.008); against C, +0.011 (−0.002 to +0.026). So D is now a little better than A and a little worse than C, and neither difference is clear yet. Part of the change can be run-to-run noise, because each method ran once. **Caution:** we found this failure on the 100 test users, and the full run uses the same users. We wrote this fix before the full run and changed nothing else after seeing these numbers. Report it this way in Milestone 3.
- **What is still open.** In conversation, D still reads willingness a little low for all users (−0.06), while C does not. For "can't afford it" users the bias is still −0.12: their answers mix money limits into their attitude. This is a fidelity question for the AI test users (persona check 2) and a reading question for D.
- **Heavy noise hurts the spoken methods more** (D 0.177, B 0.160, C 0.123, A 0.137). Only spoken methods get injected contradictions, so this comparison is not equal by design.

## First run on 10 of Siya's test users (Nov 11, 2 per band, budget 10, one run each)

| Method | avg error | capacity | willingness | behavior | system $ |
|---|---|---|---|---|---|
| A fixed form | 0.122 | 0.171 | 0.099 | 0.097 | $0 |
| B scripted interview | 0.134 | 0.185 | 0.113 | 0.105 | $0.0031 |
| C adaptive form | 0.121 | **0.070** | 0.123 | 0.168 | $0 |
| D adaptive interviewer | 0.147 | 0.127 | 0.122 | 0.191 | $0.0117 |

This run used the starting settings and the old test-user wording (before the leak fix). These are 10 runs per method, so they do not rank the methods. Two patterns are worth a check in the full run:

- The engine estimates capacity much better. At budget 10, A's fixed form never asks about debt or dependents, so these facts stay at the prior. C chooses the fact questions that matter for each person.
- C and D estimate behavior less well. In one case (U015, a user with heavy noise), D gave band 2 to a band 5 user. An injected contradiction made the user falsely say "I sold a lot at the bottom" in answer to a clarifying question. A past action is the strongest evidence, so this one false statement outweighed the honest answers. The honest "I would buy more" was hedged, so it counted as vague. Also, the user had said earlier that they never had a big loss. The extractor cannot record "never", so the engine did not flag the contradiction. Fitting the evidence strengths on the pilot users will test whether past actions should count less.

## Settings fitted on the pilot users

`python pilot.py fit` fits the evidence settings on the 10 pilot users and saves them in `pilot/fitted.json`. `belief.py` loads that file when it exists. Each result record stores the settings it used (`engine_settings`). The 100 test users are never used for fitting. A fitted part is adopted only if it lowered the error on pilot users that it was not fitted on (leave one out). Full table: `pilot/fit.md`.

These are the settings after Preyansh's review (Nov 12). The table shows the fit after the leak fix (Nov 11); the spoken row changed after the review, see the note below the table.

| Setting | Starting guess | Fitted | Left-out avg error, before → after | Decision |
|---|---|---|---|---|
| Form answers: spread for stated / imagined / past | 0.20 / 0.25 / 0.15 | 0.15 / 0.15 / 0.20 | C: 0.096 → 0.091; A: 0.100 → 0.099 | adopted |
| Form answers: lapse | 0.10 | 0.10 | (as above) | adopted |
| Spoken readings: spread for stated / imagined / past | 0.20 / 0.25 / 0.15 | 0.10 / 0.05 / 0.10 | D: 0.107 → 0.089 | adopted |
| Spoken readings: lapse | 0.10 | 0.20 | (as above) | adopted |
| Spoken fact readings that miss the true value | 0.10 | 0.104 | (as above) | adopted |

**After the review (Nov 12):** with D's new choice model, the refit gave spoken spreads 0.125 / 0.075 / 0.10 and lapse 0.10. They did no better on left-out pilot users (D 0.087 against 0.086 with the starting values), so they are **not adopted**. D now uses the starting spoken settings (0.20 / 0.25 / 0.15, lapse 0.10). The form settings are still adopted. Source: `pilot/fit.md`, `pilot/fitted.json`.
| Fixed-form questions for A and B, chosen on the pilot users | bank priority | see `pilot/fit.md` | A: 0.099 → 0.108 (worse) | not adopted |

Findings:

- **Past actions are not the strongest evidence in form answers.** Their fitted spread (0.20) is the widest of the three. A test user's past-loss story (held, sold, or none) is coarse and does not follow its behavior score closely. So the starting guess "a past action counts most" was wrong for our test users. This guess caused the U015 failure above. With the fitted settings, the professor's example asks BEH01 ("your investments drop 20% in one month") first instead of BEH02. It still asks about behavior, and another willingness question still has a value of zero.
- **The leak did not cause the choice of BEH01.** Before the leak fix the fitted spread for past actions was 0.325; after it, 0.20. The engine still prefers BEH01 after the fix.
- **Spoken readings fit very closely, and this is a limit of AI test users.** The fitted spread is 0.05 to 0.10, even with the neutral scale wording. The AI test users describe their behavior in words that follow their band closely. Real people are less consistent. The lapse (0.20) limits the risk, because one wrong reading cannot settle a score. Persona checks and the classmate study must test this.
- **Choosing the fixed-form questions on 9 users overfits.** The chosen forms did worse on the left-out user than the bank's default forms, before and after the leak fix. A and B keep the default forms.
- The fit uses noise-free spoken answers and form answers with form noise only. The pilot answers have no injected contradictions.
- Before the leak fix the fit gave similar decisions; the earlier report is in git history (`pilot/fit.md`, commit 54a2303).

## Limits

- The engine treats the three dimensions as independent. Willingness and behavior may be related.
- The answer model for bank options is a simple noisy-option model, not a calibrated item response model. We have no human response data to calibrate one. Choi and Swartz (2009) found that simple selection criteria work as well as complex ones for this type of item.
- The stop rule simulates the remaining questions as a fixed list (the current top items), not as a new adaptive choice at each step.

## Sources

- Stochastic curtailment: Finkelman (2008); Wouda and Eggen (2009), [Cito report](https://cito.nl/media/cf3jcirb/2009-computerized-classification-testing-in-more-than-two-categories-using-stochastic-curtailment.pdf).
- One-step value of information can stop too early: Heckerman, Horvitz and Middleton, [arXiv 1303.5720](https://arxiv.org/pdf/1303.5720).
- Information gain for adaptive elicitation of risk preferences: DOSE, Chapman et al., [NBER w25072](https://nber.org/system/files/working_papers/w25072/w25072.pdf); Toubia et al. (2013), [Management Science](https://econpapers.repec.org/RePEc:inm:ormnsc:v:59:y:2013:i:3:p:613-640); adaptive design optimization, Cavagnaro et al., [NeurIPS 2009](https://proceedings.neurips.cc/paper_files/paper/2009/file/6cd67d9b6f0150c77bda2eda01ae484c-Paper.pdf).
- LLM for language and a Bayesian model for choices: OPEN, Handa et al., [arXiv 2403.05534](https://arxiv.org/abs/2403.05534); BED-LLM, Choudhury et al., [arXiv 2508.21184](https://arxiv.org/abs/2508.21184).
- LLMs update beliefs poorly over many turns: Qiu et al., [arXiv 2503.17523](https://arxiv.org/abs/2503.17523).
- Item selection criteria for polytomous items: Choi and Swartz (2009), [PMC2791416](https://pmc.ncbi.nlm.nih.gov/articles/PMC2791416).
- Aberrant answers distort adaptive tests: [Zhang et al. (2022)](https://frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.841372/pdf).
