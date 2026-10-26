# Shared Contract: Risk Profile, Test Users, Question Budgets

Updated Oct 26 after the model bake-off · Somaditya Singh, Preyansh Agrawal, Siya Jain · Project name: 2sigmoid: Adaptive Risk Profiler

Every Milestone 2 section uses these terms exactly as written. If we change one, we change it here first.

## 1. What a risk profile is

Three separate dimensions, each scored 0 to 1 and mapped to 5 bands (1 = very conservative, 5 = very aggressive):

- **Capacity:** what the person can afford to lose. Facts only: time horizon, emergency fund, income stability, debts, dependents.
- **Willingness:** how the person says they feel about risk.
- **Behavioral tolerance:** what they would likely do in a real loss, probed with scenarios such as "your portfolio drops 20% in a month."

**Final band = the lowest of the three,** not the average, because an average can hide one very low score. If any two dimensions are 2 or more bands apart, the interviewer flags it and asks a follow-up.

Two things we treat as open, not settled: the research says behavioral tolerance and willingness may not be truly separate, so we test a 2-dimension version against our 3-dimension version. Also, 5 bands is our choice (common tools use 5 to 7), not a validated number.

**Capacity comes from a formula, not a guess (decided Oct 26).** Each fact becomes a 0 to 1 score, the scores are combined with fixed weights, and three red flags cap the result. The same formula sets every test user's true capacity, and we compare an interviewer that judges capacity itself against one that only collects these facts and lets the formula score them. The code is `capacity.py` in the repo.

| Fact | How it scores (0 to 1) | Weight |
| --- | --- | --- |
| Years until the money is needed | years ÷ 20, full marks at 20+ | 30% |
| Emergency savings | months ÷ 12, full marks at 12+ | 25% |
| Income stability | unstable 0, commission-based 0.33, stable 0.67, very stable 1 | 20% |
| Debt payments | 1 − (share of income ÷ 0.40), zero at 40%+ | 15% |
| People who depend on them | 1 − 0.25 per dependent | 10% |

Red flags cap capacity whatever the rest says: needing the money within 3 years (at most 0.20), under 1 month of emergency savings (at most 0.35), debt payments of 40% of income or more (at most 0.35). The weights and caps are our judgment, written down so they can be argued with. Without the caps, a long horizon hid P2's empty emergency fund.

## 2. What a test user looks like

We pick the true profile first, then an LLM plays that person. Each synthetic user has:

| Group | Fields |
| --- | --- |
| Identity | id, seed, simulator model |
| Ground truth | capacity (from the formula), willingness, behavioral (each 0 to 1 plus band), final band, mismatch type (e.g. "says aggressive, would panic-sell") |
| Demographics | age, occupation, household |
| Finances | horizon in years, emergency fund in months, income stability, debt-to-income, dependents, investable amount, goal |
| Experience | financial literacy, past reaction to a loss (none, sold, held) |
| Speaking style | verbosity, vocabulary, hedging |
| Noise | flip probability, vague-answer rate, contradiction rate, agreeing-with-anything tendency, refuses to give numbers |

Rules for running them:

- The simulated users run on a different model family from the interviewer.
- Accuracy is scored by rules against the true profile, not by an LLM judge.
- Controls for LLM-vs-LLM bias: a non-LLM template answerer, and a style-swap test (same true profile, different speaking style).
- MiroFish personas only carry social-media fields, so we extend them with the finance fields above.
- Every true score sits at least 0.03 away from a band edge (0.2, 0.4, 0.6, 0.8), so a tiny difference can't flip the band.
- Mismatch type is filled in whenever two dimensions are 2 or more bands apart, and is "none" otherwise. The scripts check this.
- Locked by the bake-off: the interviewer runs on GLM 5.3; simulated users run on DeepSeek V4 Flash 0731 with thinking off.

## 3. Question budgets

We compare four methods, each limited to the same number of questions:

- **A.** Standard fixed questionnaire
- **B.** Fixed scripted conversational interview
- **C.** Classical adaptive form (picks the next form question)
- **D.** Our adaptive conversational interviewer

**Budgets: 5, 10 and 15 questions.**

- Methods A, B and C draw from one shared bank of 35 questions: 11 capacity, 12 willingness, 12 behavior (question\_bank.json in the repo). Method D writes its own questions.
- Fixed forms split each budget across the dimensions: 2/2/1, 3/4/3 and 5/5/5 for capacity, willingness and behavioral.
- We pick the form items using a small set of pilot users kept separate from the test set, and write the choice down before testing.
- Every follow-up or clarification counts toward the budget. A question with two parts counts as two.
