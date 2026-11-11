# Pilot fit (2026-11-11)

Fitted on the 10 pilot users only. The 100 test users were not used. A fitted part is adopted only if it lowered the error on pilot users it was not fitted on.

## Evidence settings

| setting | starting guess | fitted |
|---|---|---|
| form spread, stated | 0.2 | 0.175 |
| form spread, hypothetical | 0.25 | 0.25 |
| form spread, past | 0.15 | 0.325 |
| form lapse | 0.1 | 0.05 |
| spoken spread, stated (106 readings) | 0.2 | 0.1 |
| spoken spread, hypothetical (93 readings) | 0.25 | 0.05 |
| spoken spread, past (12 readings) | 0.15 | 0.075 |
| spoken lapse | 0.1 | 0.3 |
| spoken fact miss rate | 0.1 | 0.12 |

A smaller spread means stronger evidence. Form answers: log-likelihood -256.8 with the starting guesses, -251.6 fitted (higher is better).

- Form settings: **adopted**.
- Spoken settings: **adopted**.
- Chosen fixed-form questions: **not adopted**.

## Leave-one-out check (fit on 9 pilot users, score the 10th, 10 times)

| method | budget 5 | budget 10 | budget 15 | mean |
|---|---|---|---|---|
| A, default form, starting settings | 0.125 (50%) | 0.110 (50%) | 0.082 (70%) | 0.105 |
| A, default form, fitted settings | 0.126 (60%) | 0.103 (60%) | 0.076 (80%) | 0.101 |
| A, chosen form, fitted settings | 0.112 (50%) | 0.131 (30%) | 0.104 (60%) | 0.116 |
| C, starting settings | 0.169 (30%) | 0.104 (70%) | 0.086 (70%) | 0.120 |
| C, fitted settings | 0.125 (50%) | 0.095 (70%) | 0.084 (70%) | 0.101 |
| D, starting settings | 0.138 (50%) | 0.114 (50%) | 0.096 (50%) | 0.116 |
| D, fitted settings | 0.124 (50%) | 0.110 (50%) | 0.090 (50%) | 0.108 |

Avg error over the three scores (band exact in brackets), from recorded answers, with no new API calls. D here reads the recorded spoken answers without clarifying questions. The pilot answers have no injected contradictions. 10 users: treat differences under about 0.02 as noise.

## Fixed-form questions (A and B)

| budget | default | chosen on the pilot users |
|---|---|---|
| 5 | CAP01, CAP02, WIL02, WIL03, BEH01 | CAP04, CAP02, WIL06, WIL11, BEH01 |
| 10 | CAP01, CAP02, CAP03, WIL02, WIL03, WIL10, WIL06, BEH01, BEH02, BEH06 | CAP04, CAP02, CAP03, WIL06, WIL11, WIL08, WIL01, BEH01, BEH06, BEH04 |
| 15 | CAP01, CAP02, CAP03, CAP04, CAP05, WIL02, WIL03, WIL10, WIL06, WIL01, BEH01, BEH02, BEH06, BEH05, BEH04 | CAP04, CAP02, CAP03, CAP01, CAP05, WIL06, WIL11, WIL08, WIL01, WIL05, BEH01, BEH06, BEH04, BEH02, BEH05 |
