# Classmate Study: Final Results

2sigmoid · Nov 25, 2026 · Siya Jain

## Summary

With 21 classmates, the fixed form (method A) and the adaptive interviewer (method D) gave the same final band to 17 people, and the other 4 were 1 band apart. People rated both results as a good fit (about 4 of 5). D's result was "about right" more often (14 of 21, against 12 for A), and its length was right for 20 of 21.

The outside measure did not help. The lottery task put almost everyone near the same mild caution, whatever their band, so it cannot tell which method is closer to the truth. With 21 people, this is a description, not a statistical result.

## Why and how

Our main experiment uses 100 AI test users with known true profiles. This study asks whether the two methods behave the same way with real people. Real people have no known true band, so we compare the two methods on the same person, ask each person whether the result fits them, and add one outside measure of risk taking.

Each classmate filled in one Google Form under a participant code and used our web app (Streamlit) for the two interviews:

1. **About me:** age range, investing experience, self-rated knowledge (1 to 5) and three short financial-literacy questions.
2. **Finances:** when they might need the money, months of savings, income steadiness, debt payments, dependents, goal, and their past loss and what they did.
3. **Imaginary bets:** a 9-row lottery task. In each row the person picks a safe bet (A: $40 or $32) or a risky bet (B: $77 or $2), while the chance of the high payout rises from 10% to 90%. A person who only cares about the average picks A in the first 4 rows, so more A picks means more caution. The section ends with: "Your investments dropped 20% in one month. What would you most likely do?"
4. **Interview 1:** the app reads the participant code. Odd codes get method A first and even codes get method D first, so the order effect cancels out. The app shows a band, and the person answers questions about it in the form.
5. **Interview 2:** the other method, with the same questions afterwards.

After each interview the person reports the band and rates "Does this profile sound like you?" (1 to 5), the fit of each part (capacity, willingness, behavior), whether the result was more aggressive or more cautious than expected, and the interview itself. Answers are linked only to the participant code, never to a name. Responses were collected Nov 15 to Nov 24, 2026.

## Participants

21 classmates finished both interviews: 11 started with A and 10 with D. Most are young graduate students with some investing experience and short time horizons.

|  | Count (of 21) |
| --- | --- |
| Age 23 to 26 (others: 18 to 22: 3, 27 to 30: 3, 31+: 1) | 14 |
| Invest regularly / a few times / never | 9 / 11 / 1 |
| No income (full-time student) | 8 |
| Need the money within 5 years | 11 |
| Less than 6 months of savings | 16 |
| No dependents | 18 |
| All 3 financial-literacy questions right | 19 |
| Past loss: held or bought more / sold / never had one / never invested | 12 / 4 / 4 / 1 |

Self-rated knowledge had a median of 3 of 5. One person had never invested.

## Results

A and D gave the same final band to 17 of 21 people. The other 4 were 1 band apart, 2 in each direction, so neither method is bolder overall. Both methods gave exactly the same spread of bands: band 1: 2 people, band 2: 11, band 3: 7, band 4: 1, band 5: none.

| Measure (of 21 people) | Method A (fixed form) | Method D (adaptive interviewer) |
| --- | --- | --- |
| "Does this profile sound like you?" (1 to 5), average | 4.1 | 3.9 |
| Rated the profile 4 or 5 | 17 | 17 |
| Fit of each part (1 to 5): capacity / willingness / behavior | 3.5 / 3.6 / 3.4 | 3.7 / 3.6 / 3.4 |
| Result "about right" | 12 | 14 |
| Result more cautious / more aggressive than expected | 6 / 3 | 6 / 1 |
| Questions easy to understand (agree) | 21 | 20 |
| Some questions felt repetitive (agree) | 12 | 11 |
| The assistant followed up sensibly (agree) | 14 | 14 |
| Length "about right" | 18 | 20 |

**Fit.** 17 people rated each method 4 or 5, but not the same 17: 14 rated both that high. Comparing each person's two ratings, 10 rated both the same, 7 rated A higher and 4 rated D higher. The lowest ratings were 2 of 5: twice for D and once for A, each from a different person.

**Surprise.** D's result was "about right" for 14 people, against 12 for A. When a result missed, it was mostly more cautious than expected (6 people for each method). A was more aggressive than expected for 3 people, D for 1.

**Noticing uncertainty.** 10 people said they had been unsure or contradicted themselves in D; 6 of them said D noticed, 4 were not sure, and none said no. In A, 11 people said so; 3 said A noticed, 2 said no and 6 were not sure. The fixed form has no follow-up questions, so the 3 "yes" answers for A suggest some people answered about the app in general rather than the form.

**Order.** People who started with A agreed across methods more often (same band for 10 of 11) than people who started with D (7 of 10). The average fit was 4.0 for the first interview and 4.0 for the second, so doing an interview first did not change how well people liked the result.

**Experience.** People who invest regularly (9) rated both methods 4.2. People who had invested only a few times (11) rated A 4.2 and D 3.7, so D's lower average comes from this group.

**Comments.** One person wrote that the questions were a little repetitive: "Same questions in the google form and the survey." No one named a question as confusing or pushy.

## Outside checks

The lottery task does not separate the bands, so it cannot say which method is closer to the truth. 14 of 21 people switched from the safe to the risky bet once, as expected, and all 14 picked 3 to 6 safe bets, close to the 4 of a person who only cares about the average. Band 2 people (by D) picked 3 to 5 safe bets and band 3 people picked 3 to 6, so the two groups overlap completely.

The other 7 answers are hard to read:

- 5 people switched back and forth between safe and risky (2 to 5 switches).
- 1 person picked risky in the first 4 rows and safe after, the reverse of the expected pattern.
- 1 person picked the safe bet in all 9 rows, even when the risky one paid $77 with a 90% chance. This person got band 4, the boldest band in the study, from both methods: a long horizon, 12 months or more of savings and a steady salary give a high capacity.

The drop question gives little spread either: 18 of 21 would "wait it out" after a 20% drop, 2 would buy more and 1 would sell some. Both outside checks measure risk taking with small or imagined stakes, and almost everyone answered them the same way.

## What this means for the project

1. **D agrees with the form on real people.** Same band for 17 of 21 and never more than 1 band apart. This matches the AI test users, where D and A tie on error at 10 questions. D does not produce strange results with real speech.
2. **D feels as right as the form, but not better.** Fit is about 4 of 5 for both. D's results surprised people a little less ("about right" 14 against 12), but the average fit is slightly lower (3.9 against 4.1), mostly among people with little investing experience.
3. **D's interview experience is good.** Its length was right for 20 of 21 people and its questions were easy for 20 of 21. A conversation did not feel longer than a form of the same length.
4. **D's main advantage shows up.** D noticed uncertainty for 6 of the 10 people who were unsure, and none said it missed. A form cannot follow up, which is the reason for an adaptive interviewer.
5. **Capacity drives the cautious results.** Most classmates need their money within 5 years (11 of 21) or have less than 6 months of savings (16 of 21), and the final band is the lowest of the three. That is why no one got band 5 and why misses were mostly "more cautious than expected". The system is doing what it should here, but the results may feel cautious to users who think only of their attitude to risk.
6. **The study cannot pick a winner.** With no true band for real people and a lottery task that does not separate the bands, the classmate study shows that both methods are acceptable to real users. Accuracy comes from the AI test users.

## Limits

- **Small sample.** 21 people can show large differences only, so we report counts, not significance tests.
- **Not typical beginners.** Most are 23 to 26, many are students with no income, and 19 of 21 answered all three literacy questions right.
- **They know the project.** Classmates may answer more carefully or more kindly than real users.
- **Fit is not accuracy.** Each person rated a band right after seeing it, so the ratings show whether a result feels right, not whether it is correct.
- **Order is not perfectly balanced.** 11 started with A and 10 with D, because participation depended on which codes were used.
- **Repeated questions.** The background sections ask some of the same facts as the interviews, which may make the second interview easier and the questions feel repetitive.
- **Self-reported bands.** Each person typed the band the app showed; we did not match these with the app's logs.

## Appendix: questions asked

**Consent and code.** Consent (18 or older, answers linked only to the participant code). Participant code.

**About me**

1. Age range
2. Have you ever invested money (stocks, funds, crypto, retirement account)?
3. How would you rate your knowledge of investing? (1 to 5)
4. You put $100 in an account earning 2% a year and leave it for 5 years. Afterward you'll have:
5. Your savings earn 1% a year while prices rise 2% a year. In a year, your money will buy:
6. Which is usually riskier?

**Finances**

1. If you invested money today, when might you need it back?
2. How many months of expenses could you cover from savings if your income stopped?
3. How steady is your income?
4. Roughly what share of your monthly income goes to debt payments?
5. How many people depend on your income?
6. What's the main goal for this money?
7. Have you ever lost money on an investment, and what did you do?

**Imaginary bets**

1. Nine rows: A: X% chance of $40, otherwise $32, or B: X% chance of $77, otherwise $2, with X from 10% to 90%.
2. Imagine your investments dropped 20% in one month. What would you most likely do?

**After each interview (asked twice)**

1. What band did the assistant give you?
2. Overall, does this profile sound like you? (1 to 5)
3. How well does each part fit you? What you can afford to lose / How you feel about risk / What you'd actually do in a downturn (1 to 5)
4. Was the result more aggressive or more cautious than you expected?
5. How much do you agree? The questions were easy to understand / Some questions felt repetitive / The assistant followed up sensibly on what I said
6. Did the assistant notice when you were unsure or contradicted yourself?
7. The length of the interview was: (too short to know me / about right / too long)
8. Did any question feel off, confusing or pushy? Which one?
