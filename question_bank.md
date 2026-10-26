# Question bank v1 (2026-10-26)

Shared question bank for the three form-based methods: A (standard questionnaire), B (scripted interview, using the 'spoken' wording) and C (adaptive form). Method D, the adaptive interviewer, writes its own questions. All wording is original, written in the style of published risk questionnaires; no item is copied from one.

Generated from `question_bank.json` by `check_question_bank.py --write-md`; edit the JSON, not this file.

**Scoring:** each answer scores 0 (lowest risk) to 1 (highest); a dimension is the average of its answered items; the final band is the lowest of the three. Short-form columns mark which items the default 5-, 10- and 15-question forms use.

## Capacity (what they can afford to lose)

| # | ID | Question | Answers (score) | In forms |
|---|---|---|---|---|
| 1 | CAP01 | When do you expect to need most of this money? *(fact: horizon_yrs)* | Within 3 years (0); In 3 to 5 years (0.25); In 6 to 10 years (0.5); In 11 to 20 years (0.75); More than 20 years from now (1) | 5, 10, 15 |
| 2 | CAP02 | If your income stopped, how many months of essential expenses could your emergency savings cover? *(fact: emergency_fund_months)* | Less than 1 month (0); 1 to 2 months (0.25); 3 to 5 months (0.5); 6 to 11 months (0.75); 12 months or more (1) | 5, 10, 15 |
| 3 | CAP03 | How steady is your household income? *(fact: income_stability)* | Very unpredictable (0); It changes a lot from month to month (0.33); Mostly steady (0.67); Very steady and secure (1) | 10, 15 |
| 4 | CAP04 | Roughly what share of your monthly income goes to debt payments (loans, credit cards, mortgage)? *(fact: debt_to_income)* | More than 40% (0); 25% to 40% (0.25); 10% to 24% (0.5); Under 10% (0.75); I have no debt payments (1) | 15 |
| 5 | CAP05 | How many people depend on your income? *(fact: dependents)* | 3 or more (0); 2 (0.33); 1 (0.67); None (1) | 15 |
| 6 | CAP06 | About what share of your total savings would this investment be? | Almost all of it (0); More than half (0.33); A quarter to half (0.67); Less than a quarter (1) | - |
| 7 | CAP07 | Is there a big expense in the next 3 years (a home, tuition, a wedding) that this money might need to cover? | Yes, almost certainly (0); Maybe (0.5); No (1) | - |
| 8 | CAP11 | If you suddenly had to take this money out within a year, how much trouble would that cause? | Serious trouble (0); Some trouble (0.5); Hardly any (1) | - |
| 9 | CAP08 | Besides your own pay, does your household have other reliable income (a partner's salary, a pension, rent)? | No (0); Some, but not enough to live on (0.5); Yes, enough to cover the basics (1) | - |
| 10 | CAP09 | How secure does your job or main income feel over the next two years? | I'm worried I could lose it (0); Not sure (0.5); Quite secure (1) | - |
| 11 | CAP10 | After your regular bills, how much can you keep adding to your investments? | Nothing right now (0); A little, now and then (0.5); A set amount every month (1) | - |

## Willingness (how they say they feel about risk)

| # | ID | Question | Answers (score) | In forms |
|---|---|---|---|---|
| 1 | WIL02 | On a scale from 0 to 10, how willing are you to take risks with your investments? (0 = avoid risk completely, 10 = fully prepared to take risks) | 0 (0); 1 (0.1); 2 (0.2); 3 (0.3); 4 (0.4); 5 (0.5); 6 (0.6); 7 (0.7); 8 (0.8); 9 (0.9); 10 (1) | 5, 10, 15 |
| 2 | WIL03 | Imagine investing $10,000 for one year. Which range of possible results would you pick? | Between $9,900 and $10,300 (0); Between $9,500 and $10,800 (0.33); Between $8,500 and $11,800 (0.67); Between $7,000 and $13,500 (1) | 5, 10, 15 |
| 3 | WIL10 | To aim for higher long-term growth, how big a drop in a bad year could you accept? | None (0); Up to 5% (0.25); Up to 15% (0.5); Up to 30% (0.75); More than 30% (1) | 10, 15 |
| 4 | WIL06 | For this money, what matters more to you? | Protecting what I have (0); Mostly protecting, a little growth (0.25); Both equally (0.5); Mostly growth, some protection (0.75); Growing it as much as possible (1) | 10, 15 |
| 5 | WIL01 | How would a close friend describe you when it comes to taking risks with money? | Very cautious (0); Cautious (0.25); Balanced (0.5); Willing to take chances (0.75); A real risk-taker (1) | 15 |
| 6 | WIL07 | What share of this money would you be comfortable putting into stocks? | Under 20% (0); 20% to 40% (0.25); 40% to 60% (0.5); 60% to 80% (0.75); Over 80% (1) | - |
| 7 | WIL09 | "I'm fine with some losing years if it means more growth over the long run." How much do you agree? | Strongly disagree (0); Disagree (0.25); Neutral (0.5); Agree (0.75); Strongly agree (1) | - |
| 8 | WIL04 | Which would you choose? | A sure $1,000 (0); Hard to say (0.5); A 50% chance of $2,500 and a 50% chance of nothing (1) | - |
| 9 | WIL05 | Which word comes to mind first when you hear 'investment risk'? | Loss (0); Uncertainty (0.33); Opportunity (0.67); Excitement (1) | - |
| 10 | WIL11 | Compared with most people your age, how willing are you to take financial risks? | Much less (0); A bit less (0.25); About the same (0.5); A bit more (0.75); Much more (1) | - |
| 11 | WIL12 | Which would bother you more: losing a lot, or missing out on a big gain? | Losing a lot, by far (0); Losing a lot, a bit more (0.33); Missing a big gain, a bit more (0.67); Missing a big gain, by far (1) | - |
| 12 | WIL08 | A friend tells you they made big gains on a risky investment. What's your reaction? | I wouldn't consider it (0); Curious, but I'd stay out (0.33); I might try a small amount (0.67); I'd want to get in (1) | - |

## Behavior (what they would actually do in a loss)

| # | ID | Question | Answers (score) | In forms |
|---|---|---|---|---|
| 1 | BEH01 | Your investments drop 20% in one month. What do you actually do? | Sell everything (0); Sell some (0.33); Do nothing and wait (0.67); Buy more while prices are low (1) | 5, 10, 15 |
| 2 | BEH02 | Think of the last time your investments fell a lot. What did you actually do? *(fact: past_loss_reaction)* | Sold most of it (0); Sold some (0.33); Held on (0.67); Bought more (1); It's never happened to me (skip) | 10, 15 |
| 3 | BEH06 | Six months after a drop, your investments are still down 15%. What do you do? | Give up and sell (0); Sell about half (0.33); Keep holding (0.67); Add more (1) | 10, 15 |
| 4 | BEH05 | The news says a big crash might be coming. What do you do? | Move everything to cash (0); Move some to cash (0.33); Wait and see (0.67); Get ready to buy if prices fall (1) | 15 |
| 5 | BEH04 | If your investments fell 25% and stayed down for a year, how would you feel day to day? | Constantly worried, losing sleep (0); Often worried (0.33); Sometimes uneasy (0.67); Mostly fine (1) | 15 |
| 6 | BEH07 | You invested $10,000. Two weeks later it's worth $7,000. What do you do? | Sell everything (0); Sell part of it (0.33); Hold (0.67); Buy more (1) | - |
| 7 | BEH08 | You're down 20% and an advisor you trust says to hold. Do you follow the advice? | No, I'd sell anyway (0); I'd probably sell some (0.33); Yes, I'd hold (0.67); Yes, and I'd add more (1) | - |
| 8 | BEH09 | An investment rose 30%, then lost 20% of its value. What do you do? | Sell to lock in what's left (0); Sell some (0.33); Hold (0.67); Buy more (1) | - |
| 9 | BEH10 | When something you bought loses value, how quickly do you usually sell? | Right away (0); After a little while (0.33); Only after a long time (0.67); I rarely sell at a loss (1) | - |
| 10 | BEH11 | During a crash, your friends are selling. What do you do? | Sell too (0); Think hard about selling (0.33); Ignore it (0.67); Buy (1) | - |
| 11 | BEH03 | During a market slump, how often would you check your account? | Several times a day (0); Every day (0.33); About once a week (0.67); Rarely (1) | - |
| 12 | BEH12 | Pick the one rule you'd actually follow in a market crash. | Get out to protect what's left (0); Reduce a bit (0.33); Stay the course (0.67); Invest more while prices are low (1) | - |

## Notes for review

- Default short forms take the highest-priority items in each dimension. The contract says to choose the most informative items using pilot personas kept apart from the test set; replace these defaults once that pilot is run, and write the choice down before testing.
- Items with a 'fact' field ask about a persona fact (personas.json). Once the team fixes the capacity formula, scoring capacity from those facts should follow that formula instead of a plain average.
- Behavior items ask people to predict what they would do. That is still self-report, so BEH02 (past behavior) is the strongest behavior item when the person has lived through a drop.
