# Final report: conclusions (draft, Nov 24)

Draft by Somaditya. Numbers come from `ablations.md` (tests 9–16) and `results/`. Part A uses only synthetic test users. Part B uses only real people. Part C lists what neither part shows.

## A. Conclusions from synthetic test users

**Setup.** 99 AI test users with known true profiles (one user was left out after the persona checks). Budgets of 5, 10 and 15 questions, 3 repeats each. Every method sees the same test users and the same planned noise. Differences are paired on test user, budget and repeat. The 95% ranges resample whole test users. "Clear" means the range does not include zero.

### A1. The method we present: CWF (hybrid, money facts first)

CWF asks the five money facts first, on a form. After that, the AI asks about willingness and behavior in conversation, and it writes each question from the conversation so far. One belief engine (plain code) picks every question and calculates the profile.

| Avg error (lower is better) | 5 questions | 10 questions | 15 questions | System cost per interview |
|---|---|---|---|---|
| A fixed form (baseline) | 0.125 | 0.114 | 0.085 | $0 |
| C adaptive form | 0.135 | 0.106 | 0.088 | $0 |
| D adaptive AI interviewer | 0.136 | 0.114 | 0.106 | $0.013 |
| DW interviewer, AI-written questions (writer v2) | 0.134 | 0.115 | 0.101 | $0.018 |
| CF adaptive form, money facts first | 0.123 | 0.088 | 0.086 | $0 |
| **CWF hybrid, money facts first** | **0.118** | **0.085** | **0.082** | **$0.011** |

*System cost counts only the system's own AI calls at list price, not the AI test users' calls (test 12 in `ablations.md` also counts those, so its figures are higher: D $0.0139, DW $0.0197). All rows come from the reruns of Nov 22–26, with the engine of Nov 22 and the same test users and noise (A was rerun on Nov 25; its full-run values were 0.125, 0.113 and 0.090).*

- CWF has the lowest error at every budget.
- **Against the baseline A, CWF is clearly better only at 10 questions:** −0.029 avg error and 19 points more exact bands (both clear). At 5 questions (−0.007) and 15 questions (−0.003) the difference is not clear. So the main success criterion (more accurate than a fixed form with the same number of questions) is met at 10 questions only. At 15 questions no method is clearly better than A, and D is clearly worse (+0.020).
- CWF is clearly better than C at 5 and 10 questions (−0.016 and −0.021). At 15 questions it is better by −0.006, which is not clear.
- CWF is clearly better than D and DW at every budget (−0.018 to −0.029 against D; −0.015, −0.030 and −0.019 against DW v2).
- All of CWF's gain over C is in capacity (−0.043, −0.050, −0.020). On willingness and behavior, CWF and C are tied.
- CWF and C pick the exact band equally often (+6.4, −3.4 and +1.0 points; not clear at any budget).

### A2. Where natural language helps

1. **People who answer clearly.** For clean test users, conversation reads willingness and behavior better than a form. With the same question rule, CWF − CF on attitudes is −0.020 at 10 questions and −0.021 at 15 (clear). A free answer carries more information than one ticked box.
2. **Contradictions (method D).** The AI interviewer D flags 86–92% of planted contradictions, and 2–3% of interviews that contain no false fact. A form cannot notice a contradiction. Almost all planted contradictions are false money facts (351 of 355), so this is a strength of D, not of CWF: CWF takes the money facts from the form, and in 891 interviews it raised no contradiction flag. CWF can only flag a contradiction about a past loss. A disagreement between willingness and behavior is a mismatch flag, which every method raises, forms included.
3. **Follow-up questions.** Asking a fact again when two statements conflict lowers capacity error by 0.030 at 10 questions and 0.040 at 15 (D − DN, clear). On these re-ask turns, the final band went from wrong to right more often than from right to wrong (38 against 28 at 10 questions).

### A3. Where natural language does not help

1. **Money facts heard in conversation.** Spoken money facts can be false: the test user says a wrong value and sometimes repeats it. Hearing the facts in conversation instead of on a form costs 0.018 capacity error at 10 questions and 0.031 at 15 (CW − DW, clear). For this reason CWF asks the money facts on a form.
2. **People whose answers have heavy noise.** For these test users, conversation is not better on attitudes, and sometimes it is worse: CW − C is +0.023 at 15 questions (clear). Some noise is stronger in conversation: a planned flip changes 49% of spoken answers but only 27% of form answers (persona check 4).
3. **AI-written questions that restate earlier answers.** The first version of the AI-written questions restated an earlier answer in 12% of questions, which can lead the person. Version 2 forbids this. It restates in 0% and is no less accurate.

### A4. The controlled comparison (fairness)

The Milestone 3 feedback said that D − C mixes two effects: the AI interviewer, and harder input (only spoken methods hear false money facts). We separated the two with three methods built for this test:

| Comparison | What changes | Result |
|---|---|---|
| CW − DW | Money facts on a form instead of in conversation | Capacity −0.018 at 10, −0.031 at 15 (clear). **Most of D's gap to C is this input difference.** |
| CF − C | Money facts asked first, all on the form, no AI | Avg error −0.012 at 5, −0.018 at 10 (clear), −0.003 at 15 (not clear) |
| CWF − CF | Only how attitudes are asked: conversation or form | Avg error −0.005, −0.003, −0.004 (**not clear at any budget**) |

**Conclusion:** with the same input and the same question rule, the AI conversation ties the form overall. Most of CWF's gain over C comes from asking the money facts first, a rule that a form can also use. The AI adds a clear gain for clean answerers and no gain for people with heavy noise in their answers.

### A5. Is the AI worth its cost?

- CWF costs $0.011 per interview at list price and takes 1.1 s per question. CF costs $0 and takes 0.1 s.
- For that cost, CWF gives about 0.02 lower attitude error for clean answerers, and natural questions. It does not check the money facts: a false money fact goes onto the form unchecked, as in C. Only a contradiction about a past loss can be flagged.
- It also has two weaker points. Its overall gain over CF is too small to show. At 10 questions it picks the exact band less often than CF (−7.4 points, clear).
- **Our answer:** the AI is worth about one cent per interview when people can explain themselves. When catching false money facts matters most, D does that and CWF does not; D costs about the same ($0.013) but has higher error. Where cost or speed matters most, CF is the alternative with the same error and no AI.

### A6. Other synthetic-user findings

- **Code that keeps the evidence beats prompt chaining.** D is clearly better than D0, the single-AI design of Milestone 2, at 10 and 15 questions (−0.022 and −0.054), for about half the cost. D0's error grows with each extra question.
- **The stop rule is now safe.** With the confidence floor and one band rule, the band changes after the stop in 0–3% of runs for C and D (it was 7–14% at Milestone 3). It saves up to about 3.6 questions per run at 15 questions. CWF was run with the old band rule, where the band changed after the stop in 6.2% of runs at 10 questions (2 of 32 stops). A replay of CWF's recorded answers with the new band rule gives 0.0%, 0.0% and 0.9% at 5, 10 and 15 questions. It saves 0.03, 0.14 and 1.25 questions per run. CWF stops less often than C, because its first questions are fixed as money facts.
- **Three AI parts did not help:**
  - Retrieval of similar labeled answers: no accuracy gain, 25% more cost.
  - Token probabilities: clearly less accurate.
  - Embedding search instead of keyword search: no gain.

## B. Conclusions from real people (classmate study)

Source: `classmate_study_report.md` (Siya, Nov 25).

**Setup.** 21 classmates did the fixed form (A) and the AI interviewer (D), 10 questions each. Odd participant codes started with A and even codes with D (11 started with A, 10 with D). The study did not test C, CF, CW or CWF. Real people have no known true profile, so these results show agreement and how the result feels to the person, not accuracy. With 21 people we report counts, not significance tests.

| Measure (of 21 people) | A fixed form | D AI interviewer |
|---|---|---|
| Same final band as the other method (app logs) | 14 (the other 7 differ by 1 band: D lower for 4, higher for 3) | |
| "Does this profile sound like you?" (1 to 5), average | 4.1 | 3.9 |
| Rated the profile 4 or 5 | 17 | 17 |
| Result "about right" | 12 | 14 |
| Length "about right" | 18 | 20 |
| Of the people who said they were unsure or contradicted themselves: "it noticed" | 3 of 11 | 6 of 10 (none said no) |

- **D agrees with the form on real people.** It gave the same band to 14 of 21, and was never more than 1 band away. The spread of bands is almost the same, and neither method is bolder. (People typed 17 of 21 as the same band, because 3 of 42 typed bands were the band of their other interview; we use the app's logs.) D does not give strange results with real speech.
- **D feels as right as the form, not more right.** The average fit is 3.9 against 4.1. D's lower average comes from the 11 people who had invested only a few times (3.7 against 4.2). People who invest regularly rated both 4.2. D's result was "about right" a little more often (14 against 12).
- **D notices uncertainty.** 6 of the 10 people who were unsure said D noticed; none said it missed. A form cannot follow up. 3 people said A noticed, which suggests that some answered about the app in general.
- **Capacity makes the results cautious.** 16 of 21 have less than 6 months of savings and 11 need the money within 5 years. Because the final band is the lowest of the three, no one got band 5, and most misses were "more cautious than expected" (6 people for each method).
- **The outside measure did not separate the bands.** In the lottery task, people in band 2 and band 3 picked the same number of safe bets. So the study cannot say which method is closer to the truth.

**What this supports:** with real people, the conversation notices unsure or contradictory answers. It agrees with the form and feels about as right. This matches the synthetic findings for D in A2: D notices contradictions, and the overall result ties the form. It does not carry over to CWF, which takes the money facts from the form and so cannot notice a false one.

**What this does not support:** any claim about the accuracy of D, or any claim about CWF or CF on real people.

## C. What we cannot conclude

- **CWF and CF were tested only on synthetic test users.**
  - The real-user evidence for CWF is indirect: it comes from D, which uses the same kind of conversation for attitudes.
- **The noise in the test users is our design.**
  - Real people may make fewer false statements, or different ones.
  - AI test users repeat their own false values more than people probably do. When the test users correct a slip on a follow-up question, D's capacity error falls (test 10).
- **The differences are small.** CWF − C is −0.016 to −0.021 on a 0-to-1 scale. CWF − CF is not clear at any budget.
- **One model family plays all test users** (DeepSeek V4 Flash). In persona check 5, two other models played the same users (Nemotron all 100, Muse 10) and agreed within one band for 98 of 100, but other models may answer differently.
- **The real-user group is small and not typical.** It is 21 classmates: 14 are 23 to 26 years old, 8 have no income, and 19 of 21 answered all three literacy questions right. They know the project, and they typed in the band themselves; 39 of 42 typed bands match the app's logs, and we use the app's bands.

## D. Answers to the Milestone 3 feedback

| Feedback | Where we answer it |
|---|---|
| Find where natural language helps, and whether it is worth the cost | A2, A3, A5 |
| Make the comparison fair: spoken methods hear false facts that forms never see | A4 (CW, CF and CWF isolate the input from the AI) |
| Keep synthetic-user and real-user conclusions apart | Parts A and B; part C lists the limits |
