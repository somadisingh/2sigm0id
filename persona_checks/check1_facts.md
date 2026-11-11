# Persona check 1: facts (100 test users, backstories off)

Each test user answers six direct questions about its facts, in a fresh conversation with no noise. Code compares the answer with the true fact.

| fact | right, all users | right, users told to avoid numbers |
|---|---|---|
| emergency_fund_months | 100% of 87 | 92% of 13 |
| horizon_yrs | 100% of 87 | 100% of 13 |
| dependents | 98% of 87 | 100% of 13 |
| past_loss_reaction | 100% of 87 | 92% of 13 |
| debt_to_income | 100% of 87 | 92% of 13 |
| income_stability | 93% of 87 | 100% of 13 |

Users with all six facts right: 89 of 100.
Users (not told to avoid numbers) with 2 or more wrong facts: 0.

Wrong answers (first 15):

- U018-b5-match-heavy, income_stability: true stable and high, said "Stable."
- U020-b3-cautious-heavy, income_stability: true stable and high, said "Stable."
- U034-b1-cautious-clean, income_stability: true stable and high, said "Stable."
- U039-b2-match-heavy, dependents: true 2, said "Three, I guess—my wife and my kid count too."
- U069-b4-match-heavy, income_stability: true stable and high, said "Stable."
- U071-b2-match-clean, dependents: true 2, said "Three, counting my wife and our son."
- U084-b2-cautious-clean, income_stability: true stable and high, said "Stable."
- U095-b5-match-heavy, income_stability: true stable and high, said "Stable."
