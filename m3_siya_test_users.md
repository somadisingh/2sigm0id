# Milestone 3 draft: test users and how we checked them (Siya, Nov 18, 2026)

Draft section for the combined Milestone 3 document. Sources: `mirofish/README.md`, `persona_checks/` (checks 1, 4 and 6, backstory rewrite, style swap), `mirofish/persona_checks_235.md` (checks 2, 3 and 5), and the classmate study responses (12 people currently).

## Test users

**How we made them.** We have 100 AI test users, 20 for each true final band, plus 10 separate pilot users that tune the system and are never scored. Each test user was built "truth first":

1. We set the true willingness and behavior scores first. Capacity comes from the user's money facts (years until they need the money, emergency savings, income stability, debt payments, dependents) through the same capacity formula the system uses. The final band is the lowest of the three bands.
2. Every true score is at least 0.03 from a band edge, so a tiny reading error cannot change the band.
3. 35 users have a mismatch: two of their bands are 2 or more apart. 13 say they are bold but would panic-sell, 12 say they are bold but cannot afford risk, and 10 can afford risk but prefer caution. These users are the hardest cases: someone who talks bold but would sell in a crash should get a low final band, so a good interviewer must look past what they say.
4. Each user has a talking style (length, vocabulary, hedging) and a noise plan: 35 clean, 33 moderate and 32 heavy. Noise means flipped answers, vague answers, false statements about a money fact, and corrections of an earlier statement. 13 users avoid exact numbers.
5. MiroFish (with DeepSeek V4 Flash) wrote a backstory for each user from seed documents. Its output described people as social-media accounts and some details contradicted the true profile, so we rewrote every backstory in English from the true data and kept only details that fit (jobs, hobbies, sayings). A check script flags 0 of 100 backstories for wrong numbers, wrong language or contradictions. On Nov 13 we rewrote the parts of each backstory about risk, market drops and past losses. The first versions reused a few fixed sentences for each band (for example, "panic" was in 14 stories), so the users sounded alike, and the interviewer could learn the sentence instead of reading the person. Each user now has their own concrete habit, such as "checks the app all day and sells when it turns red" ("panic" is now in 0 stories). The true scores did not change. To check that the new stories still describe the same person, an AI model that never sees the true scores (GLM 5.3) read each story and guessed the bands. It guessed willingness within 1 band for 100 of 100 users and behavior within 1 band for 94 of 100, about the same as with the old stories.

DeepSeek V4 Flash plays the test users in the experiment. It gets the user's facts, scores (as plain sentences, never numbers), backstory, style and, for each question, any planned noise.

## Checking the test users

The experiment is only as good as its test users: if an AI test user does not act like its true profile, a method can be marked wrong for reading the user correctly. So we ran six persona checks.

| Check | What we test | Result | Users that fail |
|---|---|---|---|
| 1. Facts | Asked directly with no noise, does the user state its 6 money facts correctly? | 92 of 100 state all 6 correctly | 0 have 2 or more wrong facts |
| 2. Profile | 8 new multiple-choice questions (not in our question bank, no noise). Is the average score in the true band or one away? | Exact band: willingness 74%, behavior 86% | 1 of 100 |
| 3. Repeat | Same 8 questions in a second, separate conversation. Same option on at least 5 of 8? | 90% of 800 answers are the same | 2 of 100 |
| 4. Noise | Does the planned noise really appear in the full run's answers? | False facts stated in 95% to 96% of planned turns (1% to 4% false alarms) | per turn, not per user |
| 5. Models | DeepSeek, Nemotron and Muse (10 users) play the same user. Within 1 band of each other? | All models give exactly the same two bands for 69% of users | 2 of 100 |
| 6. People read | Three of us read 20 of D's conversations without the true profile and guess the final band | Exact: 50% to 75%; within 1 band: 90% to 95% (method D: 60%, 100%) | per conversation |

**What we found.**

1. **The test users mostly behave as designed.** Only 1 user, U054, fails 2 or more checks. Its true willingness is band 5, but DeepSeek played it as band 3, while Nemotron played it as band 5. This user is very bold but knows little about investing, and DeepSeek seems to read low knowledge as caution. We leave U054 out of all scoring, as decided before the checks ran. This changes no method's average error by more than 0.001, and the order of the methods does not change.
2. **The hardest users pass.** All 12 "says aggressive, would panic-sell" users answered the willingness questions boldly and the behavior questions with fear, and all 12 pass check 2. This matters because an earlier version mixed the two: a test user told to talk bold and act scared gave scared willingness answers too.
3. **The noise works, with one exception.** Injected false facts and vague answers show up as planned. A "flip" note changes a form answer in only 27% of turns (3% on clean answers), so forms see less flip noise than spoken methods (49% in method D). The "agree with a hint" noise never shows, because our questions never hint at an answer.
4. **People can read the band from the answers, but not easily.** The readers agreed with each other on only 40% of conversations. All readers and method D missed the same 3 conversations, and none of these users fails checks 2, 3 or 5, so those are hard cases rather than broken users.
5. **Small problems from check 1.** Most wrong facts come from users with the income "stable and high", who just say "stable" when asked. The capacity formula treats these two labels differently, so the interviewer can read a capacity that is a little too low. One user also counted their spouse and themself as dependents.

## Does the way a person talks change the result?

We copied 20 test users, 4 per band, and changed only their talking style: all three of length, vocabulary and hedging (for example, short, plain and confident became long, technical and hesitant). Everything else stayed the same: true profile, facts, backstory, noise and random seed. Somaditya ran the copies with method D at 5, 10 and 15 questions, 3 times each (180 interviews, $2.58), and compared each with its original.

| Questions | Avg error, original | Avg error, style swap | Difference (95% range) |
|---|---|---|---|
| 5 | 0.138 | 0.150 | +0.012 (−0.003 to +0.027) |
| 10 | 0.113 | 0.117 | +0.004 (−0.015 to +0.021) |
| 15 | 0.103 | 0.098 | −0.005 (−0.021 to +0.009) |

**No clear effect.** At every budget the range includes 0, and the largest difference is about a tenth of D's error. The final band changes in 32% to 48% of pairs, about as often as it changes between two repeats of the same original user (30% to 45%). The largest single gap, exact band at 10 questions (72% to 60%), goes the other way at 15 questions, so we do not claim it.

**Limits.** 20 users can only show a large effect. Most copies became technical and hesitant, because most original users were plain and confident, so the other directions have few runs.

## Classmate study

**Why.** All results above come from AI test users. The classmate study asks whether the methods behave the same with real people. Real people have no known true profile, so we compare the two methods on the same person, ask each person whether the result fits them, and add one outside measure of risk taking.

**How.** Each classmate fills in one Google Form with their participant code. The form has three background sections first:

1. **About me:** age range, investing experience, self-rated knowledge, and three short financial-literacy questions.
2. **Finances:** when they might need the money, months of savings, income steadiness, debt payments, dependents and goal, plus their past loss and what they did.
3. **Imaginary bets:** a 9-row lottery task. In each row the person picks a safe bet (A: $40 or $32) or a risky bet (B: $77 or $2). The chance of the high payout rises from 10% to 90%. A person who only cares about the average picks A in the first 4 rows, so more A choices means more caution. The section ends with one question: "Your investments dropped 20% in one month. What would you most likely do?"

Then the person opens our web app (Streamlit), which reads their participant code. Interview 1 is method A (fixed form) for odd codes and method D (adaptive interviewer) for even codes, so the order effect cancels out. After interview 1, the app shows a band, and the person answers questions about it in the Google Form: the band, "Does this profile sound like you?" (1 to 5), how well each of the three parts fits (1 to 5), whether the result was more aggressive or more cautious than expected, and questions about the interview itself. Interview 2 uses the other method, with the same questions afterwards. Answers are linked only to the participant code, never to a name.

**Responses so far.** 12 classmates finished both interviews: 7 started with A and 5 with D. 9 are 23 to 26 years old. 6 invest regularly, 5 have invested a few times and 1 never has. 5 have no income (full-time students).

| | Method A (fixed form) | Method D (adaptive interviewer) |
|---|---|---|
| Final band given | band 1: 1, band 2: 7, band 3: 4 | band 1: 1, band 2: 7, band 3: 4 |
| "Does this profile sound like you?" (1 to 5), average | 4.1 | 3.9 |
| Fit of each part (1 to 5): capacity / willingness / behavior | 3.5 / 3.7 / 3.6 | 3.7 / 3.5 / 3.4 |
| Result "about right" (not more aggressive or cautious than expected) | 6 of 12 | 8 of 12 |
| Interview length "about right" | 10 of 12 | 12 of 12 |
| "Did the assistant notice when you were unsure or contradicted yourself?" Yes, of those who say they were unsure | 0 of 5 | 4 of 5 |

**What we found.**

1. **A and D agree.** They gave the same final band to 10 of 12 people. The other 2 differ by 1 band, once in each direction.
2. **Both methods mostly fit.** The average fit is about 4 of 5 for both. The lowest ratings were 2 of 5, once for D and once for A, from different people.
3. **D's results surprised people less.** 8 of 12 called D's result "about right", against 6 of 12 for A. When a result missed, it was mostly more cautious than the person expected (4 of 12 for each method).
4. **D notices uncertainty; the fixed form cannot.** In each method, 5 people said they had been unsure or contradicted themselves. With D, 4 of these 5 said the assistant noticed. With A, none did (2 said no, 3 were not sure). This is what D is built for: a form cannot ask again.
5. **Nobody got a band above 3.** Most classmates gave short time horizons (7 of 12 need the money within 5 years) and few months of savings, and the final band is the lowest of the three. This fits the "more cautious than expected" answers: the cautious result comes from capacity, not from attitude.
6. **The lottery task does not separate the bands.** 9 of 12 people switched from A to B once, as expected. All 9 picked 3 to 5 safe options, close to the 4 of a person who only cares about the average, and this did not differ between band 2 and band 3. One person picked the risky option in the first 4 rows and the safe one after, the reverse of the expected pattern, and 2 people switched back and forth. Small bets with a few dollars measure caution only roughly, so we report this but draw no conclusion.
7. **Repetition.** 7 of 12 agreed that some questions felt repetitive in each method. One person wrote that the Google Form and the interviews asked the same questions. This is expected, because the background sections ask the same facts as the interviews.

**Limits.** With 12 people this is a description, not a statistical result. Most are 23 to 26 years old, and many are students with no income, so they are not typical beginner investors. They know the project and may answer more carefully than real users. Each person rated a band right after seeing it, so the fit ratings measure whether the result feels right, not whether it is correct.
