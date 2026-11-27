# Numbers for P4, the Milestone 3 system section (for Preyansh, Nov 16, 2026)

All numbers are from `main`. The full-run numbers leave out U054, the one user that fails 2 or more of Siya's persona checks (this changes no avg error by more than 0.001).

## 1. The professor's example (`test_belief.py`, `test_professors_example`)

The test user: capacity high (horizon 25 years, 12 months of savings, very stable income, no debt, no dependents). Says they like risk: WIL01 "How would a close friend describe you when it comes to taking risks with money?" option 4 (0.75), and WIL09 "I'm fine with some losing years..." strongly agree (1.0). But acts scared: BEH05 "The news says a big crash might be coming" moves some to cash (0.33), BEH11 "During a crash, your friends are selling" sells too (0.0).

What the engine does next (6 questions left):

| Engine settings | Next question | Its value (expected information about the final band) | Best willingness question | Most likely final band | Mismatch chance |
|---|---|---|---|---|---|
| Starting guesses (past actions strongest) | BEH02 "Think of the last time your investments fell a lot. What did you actually do?" | 0.289 | 0.000 | band 1 (51%) | 97% |
| Fitted settings, as used in the run | BEH01 "Your investments drop 20% in one month. What do you actually do?" | 0.189 | 0.000 | band 1 (56%) | 99% |

So: behavior decides the band (lowest of three), another willingness question is worth nothing, and the engine flags the mismatch. With the starting settings it asks about a past action, as the professor's example says. With the fitted settings it asks a behavior question too, but a scenario one: the fit on the pilot users made past-action answers weaker evidence (spread 0.15 to 0.20) and scenario answers stronger (0.25 to 0.15) (`pilot/fitted.json`).

Stop rule (`test_stop_rule`): the chance that the rest of the budget changes the final band is 0.53 for a new user, and 0.00 once behavior is clearly band 1, so the engine stops (limit 0.05).

## 2. Cost and speed per completed profile, 10 questions (full run)

| Method | AI calls | Input tokens | System $ (list price) | Wait per turn | Avg error | Band exact |
|---|---|---|---|---|---|---|
| A fixed form | 0 | 0 | $0 | 0 s | 0.113 | 50% |
| C adaptive form (belief engine) | 0 | 0 | $0 | 0 s | 0.103 | 71% |
| B scripted interview | 10.0 | 1,826 | $0.0031 | 0.86 s | 0.130 | 42% |
| D adaptive interviewer (belief engine) | 11.5 | 7,380 | $0.0126 | 1.24 s | 0.116 | 60% |
| DR = D + retrieval | 11.6 | 9,737 | $0.0157 | 1.24 s | 0.115 | 62% |
| DP = D + token probabilities | 10.7 | 1,777 | $0.0029 | 0.99 s | 0.140 | 53% |
| DN = D without re-asks | 10.0 | 7,182 | $0.0121 | 1.07 s | 0.122 | 58% |
| D0 old LLM-only interviewer | 11.7 | 14,829 | $0.0272 | 1.75 s | 0.138 | 54% |

The belief engine itself takes about 0.1 s per question (`engine_secs`), with no AI call. Dollar figures are list prices and are upper bounds (the real bill was lower; see `failure_D_capacity.md`, "Note on cost").

## 3. Where the details are

- Full results and the ablation tests: `plan.md` section 5a, `ablations.md`.
- Failure analysis: `failure_D_capacity.md` (part 1), `failure_analysis_2to4.md` (parts 2 to 4).
- AI model roles table: `BELIEF_ENGINE.md`.
