# Persona check 1: facts (100 test users, backstories on)

Each test user answers six direct questions about its facts, in a fresh conversation with no noise. Code compares the answer with the true fact.

| fact | right, all users | right, users told to avoid numbers |
|---|---|---|
| emergency_fund_months | 100% of 87 | 92% of 13 |
| horizon_yrs | 100% of 87 | 100% of 13 |
| dependents | 99% of 87 | 100% of 13 |
| past_loss_reaction | 99% of 87 | 100% of 13 |
| debt_to_income | 100% of 87 | 92% of 13 |
| income_stability | 95% of 87 | 100% of 13 |

Users with all six facts right: 92 of 100.
Users (not told to avoid numbers) with 2 or more wrong facts: 0.

Wrong answers (first 15):

- S3-eager-cant-afford, dependents: true 2, said "Four. Me, my wife, and my two kids."
- U019-b5-match-moderate, income_stability: true stable and high, said "Stable."
- U020-b3-cautious-heavy, income_stability: true stable and high, said "Stable."
- U034-b1-cautious-clean, income_stability: true stable and high, said "Stable."
- U043-b5-match-clean, income_stability: true stable and high, said "Stable."
- U073-b3-panic-heavy, past_loss_reaction: true none, said "Held."
