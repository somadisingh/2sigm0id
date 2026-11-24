---
title: "2sigmoid: Adaptive Risk Profiler — Milestone 3: Results, Failures and Iteration"
subtitle: "Somaditya Singh, Preyansh Agrawal, Siya Jain · Code: github.com/somadisingh/2sigm0id"
---

**The task.** A beginner investor answers questions, and the system estimates three risk scores (0 to 1): **capacity** (how much loss they can afford), **willingness** (what they say) and **behavior** (what they do in a drop). The final band (1 to 5) is the lowest of the three. We compare an adaptive AI interviewer with forms on 100 AI test users with known true profiles, and on 12 classmates.

**Answers to the Milestone 2 feedback.** (1) *Prompt chaining is not enough:* we no longer chain prompts. Each AI model has one narrow job with a fixed output, and code makes every decision. We also tested pure prompt chaining (method D0); it fails (section 3). (2) *How questions are chosen and when to stop:* section 1, with the professor's example in real numbers. (3) *Persona validation:* six checks, section 2. (4) *Calls, tokens, time and cost per profile:* Table 1.

## 1. Current system

**Generative AI reads and writes language; code tracks the evidence and decides.** In Milestone 2, one AI model ran the whole interview (now method D0). AI models lose track of evidence over many turns. So we split the work:

| Generative AI part | What it does | How we test it |
|---|---|---|
| **Extractor** (GLM 5.3) | Turns each free-text answer into structured evidence: money-fact ranges, scores on a fixed scale, evidence type (past action, imagined case, stated preference), clear or vague | Faithfulness test: a judge model agrees with our hand labels on 37 of 38 clear readings; 97% of no-noise fact readings hold the true value |
| **Clarifying-question writer** | Words a neutral re-ask when two statements of a fact conflict | Ablation D vs DN (D without re-asks) |
| **Retrieval (DR)** | Shows the extractor the 3 most similar labeled pilot answers | Ablation DR vs D |
| **Token probabilities (DP)** | Reads the model's own probability for each answer option, calibrated with a temperature | Ablation DP vs D |
| **AI test users** | MiroFish (multi-agent) wrote backstories; DeepSeek V4 Flash plays each user with a planned style and noise | Six persona checks |
| **AI judges** | Check readings and check that planned noise appears | Hand labels; false-alarm controls |

**The belief engine** (`belief.py`, plain code) keeps a probability distribution for willingness and behavior, and one for each money fact. Capacity comes from a formula run on 2,000 samples of the facts, so an unasked fact keeps capacity uncertain. Before each question, the engine picks the bank question with the most expected information about the final band (0.1 s, no AI call). It then simulates 400 futures for the rest of the budget. If the band changes in fewer than 5%, the band is settled and a real system would stop. In the experiment it records this stop point and keeps asking, so all methods ask the same number of questions.

**The professor's example.** A user with high capacity says they like risk (willingness answers 0.75 and 1.0) but acts scared (behavior answers 0.33 and 0.0). The engine gives band 1 a 56% chance and flags a mismatch (99%). The best behavior question has an expected information of 0.189. Any willingness question has 0.000, because behavior sets the lowest band. So the engine asks a behavior question (BEH01: "your investments drop 20% in one month"). Once behavior is clearly band 1, the chance that more questions change the band falls from 0.53 to 0.00, and it stops.

**Methods compared** (same question bank, same test users, same planned noise): A fixed form (baseline), B scripted interview, C adaptive form (engine, no AI), D adaptive interviewer (engine + extractor + writer), DR, DP, DN (D variants), D0 (AI model only, Milestone 2 design). A live web app runs A and D for real people.

## 2. Baseline and current results

**Experiment.** 8 methods × 99 test users × 5, 10 and 15 questions × 3 repeats = 7,128 interviews (one user left out after the persona checks). Avg error is the mean distance between estimated and true scores (lower is better). Differences use the same user and repeat, with 95% bootstrap ranges.

| Method | Avg error at 5 / 10 / 15 questions | Exact band at 10 | AI calls at 10 | Input tokens at 10 | $ per profile at 10 | Wait per turn |
|---|---|---|---|---|---|---|
| A fixed form (baseline) | **0.125** / 0.113 / 0.090 | 50% | 0 | 0 | $0 | 0 s |
| B scripted interview | 0.150 / 0.130 / 0.113 | 42% | 10.0 | 1,826 | $0.003 | 0.86 s |
| **C adaptive form** | 0.130 / **0.103** / **0.086** | **71%** | 0 | 0 | $0 | 0.1 s |
| **D adaptive interviewer** | 0.138 / 0.116 / 0.107 | 60% | 11.5 | 7,380 | $0.013 | 1.24 s |
| DR (D + retrieval) | 0.134 / 0.115 / 0.109 | 62% | 11.6 | 9,737 | $0.016 | 1.24 s |
| DP (D + token probabilities) | 0.180 / 0.140 / 0.123 | 53% | 10.7 | 1,777 | $0.003 | 0.99 s |
| DN (D without re-asks) | 0.140 / 0.122 / 0.123 | 58% | 10.0 | 7,182 | $0.012 | 1.07 s |
| D0 (AI model only) | 0.128 / 0.138 / 0.161 | 54% | 11.7 | 14,829 | $0.027 | 1.75 s |

*Table 1. Full run. Dollar figures are list prices. The full run is $77.33 at list price; the provider billed $46.10 for it and all other runs, so real costs are at most about 60% of these.*

**Against the baseline (A).** At 10 questions, C has a clearly lower error (−0.010, range −0.017 to −0.003) and 21 points more exact bands. D has the same error as A (+0.003, range −0.006 to +0.011) and 10 points more exact bands (range +3 to +17). At 5 and 15 questions, D is clearly worse than A.

**Are the test users valid?** Only 1 of 100 fails 2 or more of six checks; leaving it out changes no error by more than 0.001. 92 state all their money facts correctly. Other AI models play the same users within 1 band. Planned false facts appear in 95% to 96% of planned turns (1% to 4% false alarms). Three of us read 20 of D's conversations blind and got the exact band in 50% to 75% (D: 60%). Changing only the talking style of 20 users changes D's error by at most 0.012 (not clear).

**Real people (12 classmates, each did A and D).** A and D gave the same band to 10 of 12. Both fit well (average 4.1 of 5 for A, 3.9 for D). 8 of 12 called D's result "about right", against 6 of 12 for A. Of 5 people who said they were unsure or contradicted themselves, 4 said D noticed; the fixed form cannot notice (0 of 5).

## 3. What worked and what failed

**Worked.**

- **Code that keeps the evidence beats prompt chaining.** D is clearly better than D0 at 10 and 15 questions (−0.022 and −0.054), costs 54% to 62% less and answers faster. D0's error grows with every extra question (0.128 → 0.161). It drifts toward caution: its capacity bias goes from −0.06 to −0.13, and it underestimates bold (band 5) users by about 0.2 per score. Code weighs each answer by the same rule, so D improves with more questions.
- **The extractor reads clear speech very well.** On clean test users, D and DR are the best methods (error 0.062 at 15 questions; C 0.077, A 0.083).
- **Re-asks help.** D is clearly better than DN at 15 questions (−0.016, 9 points more exact bands).
- **The engine helps forms too.** C is the best method overall.

**Failed.**

- **D's capacity error, caused by false facts.** Only spoken methods receive false money facts (a form has no follow-up turn). D runs with a false fact have a capacity error of 0.23; without one, 0.14 at 10 and 0.09 at 15 questions (C: 0.12 and 0.10). One clear statement is strong evidence, the weakest-link caps in the capacity formula turn a 50/50 belief into a large drop, and the AI test user repeats its false value in a third of re-asks.
- **Heavy-noise users.** D and DR are the worst engine methods on them (0.168 and 0.175 at 15 questions; C 0.098). 54% to 74% of these runs contain a false fact, and each extra spoken question is another chance for one.
- **The stop rule breaks its promise.** It saves a third to a half of the questions, but the band changes after the stop in 7% to 14% of runs, not under 5%. Causes: the engine is too sure (it gives its top band 76% to 80%, but that band is correct in 56% to 71%); it stops when no question can help even when unsure; and for D the engine and the score used different band rules.
- **Retrieval adds cost and no accuracy** (DR vs D: no clear difference, +25% cost). **Token probabilities lose accuracy** (DP vs D: clearly worse at every budget, but 77% cheaper).
- **Our predictions written before the run** said D would beat the forms and lead most at 5 questions. Both failed.

## 4. Iterations and improvements

| Change (date) | Why | Effect |
|---|---|---|
| Belief engine replaces the AI-run interview (Nov 10–12) | Professor's feedback; D0 lost track of evidence | D beats D0 by 0.022 to 0.054 at 10 and 15 questions, at half the cost |
| Extractor scores claims as willingness and actions as behavior (Nov 11) | It mixed the two for "talks bold, sells in a crash" users | D's error 0.129 → 0.116; their willingness bias −0.19 → −0.05 |
| Removed a wording leak ("20% in a month") from test-user prompts (Nov 11) | The test users repeated a bank question's words | All pilot answers made again |
| Evidence strengths fitted on 10 pilot users, never on test users (Nov 11–12) | The first values were guesses | Form fit adopted. Spoken fit not adopted: no gain on left-out users |
| Past actions no longer the strongest spoken evidence (Nov 12) | D asked the same past-loss question again and again | Behavior error 0.186 → 0.078 on 20 users |
| Backstories rewritten (Nov 13) | Users reused fixed sentences ("panic" in 14 stories) | 0 repeats; bands still readable from the stories |
| Final band = lowest of three in the live app (Nov 14) | App and score disagreed in 19 of 40 test sessions | 0 of 40 |
| Weaker fact evidence; median capacity (tested on recorded answers) | Try to soften false facts | Negative: weaker evidence is worse (0.183); median helps C more and does not fix false-fact runs |

Robustness: with other evidence strengths, no method's error changes by more than 0.006, and the order of methods at 10 questions stays the same.

## 5. Remaining gaps

- **Main success criterion** (more accurate than a static form with the same or fewer questions): met by C at 10 questions. **Not met by D**, which only ties A at 10 and is worse at 5 and 15.
- **False facts** still break D's capacity estimate. The engine averages a false and a true statement instead of resolving them.
- **The stop rule** is not calibrated (7% to 14% instead of under 5%), so we cannot yet claim fewer questions.
- **Real-user evidence is small** (12 classmates, mostly 23 to 26 years old). AI test users may repeat their own false statements more than real people.
- **Portfolio fit** (our secondary goal) is not started.

## 6. Next steps (final two weeks, in priority order)

1. **Resolve conflicting facts before scoring them** (fix for the main failure). Leave a disputed fact out of capacity until a re-ask settles it. Rerun D, DR and DN (about $40 at list price, less in practice).
2. **Fix the stop rule.** Stop only when the change chance is under 5% *and* the engine is at least 85% sure; use one band rule everywhere. Check on recorded runs first, then in the rerun.
3. **AI-written questions (new generative AI part).** The engine still chooses what to ask; the AI model words it from the conversation, so it feels natural. Compare with D, and check that the wording does not hint at answers (our "acquiescence" noise will show it).
4. **Embedding retrieval.** Replace keyword retrieval with an embedding model and test it on 290 hand-labeled answers.
5. **Final report.** All changes are logged with dates in `ablations.md` before their results. Portfolio fit only if time remains.
