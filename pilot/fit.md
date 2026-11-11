# Pilot fit (2026-11-11)

Fitted on the 10 pilot users only. The 100 test users were not used. A fitted part is adopted only if it lowered the error on pilot users it was not fitted on.

## Evidence settings

| setting | starting guess | fitted |
|---|---|---|
| form spread, stated | 0.2 | 0.15 |
| form spread, hypothetical | 0.25 | 0.15 |
| form spread, past | 0.15 | 0.2 |
| form lapse | 0.1 | 0.1 |
| spoken spread, stated (105 readings) | 0.2 | 0.1 |
| spoken spread, hypothetical (91 readings) | 0.25 | 0.05 |
| spoken spread, past (11 readings) | 0.15 | 0.1 |
| spoken lapse | 0.1 | 0.2 |
| spoken fact miss rate | 0.1 | 0.104 |

A smaller spread means stronger evidence. Form answers: log-likelihood -242.4 with the starting guesses, -235.0 fitted (higher is better).

- Form settings: **adopted**.
- Spoken settings: **adopted**.
- Chosen fixed-form questions: **not adopted**.

## Leave-one-out check (fit on 9 pilot users, score the 10th, 10 times)

| method | budget 5 | budget 10 | budget 15 | mean |
|---|---|---|---|---|
| A, default form, starting settings | 0.126 (50%) | 0.095 (70%) | 0.080 (70%) | 0.100 |
| A, default form, fitted settings | 0.123 (60%) | 0.095 (70%) | 0.080 (70%) | 0.099 |
| A, chosen form, fitted settings | 0.118 (50%) | 0.111 (50%) | 0.094 (70%) | 0.108 |
| C, starting settings | 0.126 (50%) | 0.090 (70%) | 0.073 (80%) | 0.096 |
| C, fitted settings | 0.115 (50%) | 0.078 (80%) | 0.079 (60%) | 0.091 |
| D, starting settings | 0.119 (70%) | 0.111 (70%) | 0.091 (80%) | 0.107 |
| D, fitted settings | 0.124 (50%) | 0.087 (60%) | 0.057 (80%) | 0.089 |

Avg error over the three scores (band exact in brackets), from recorded answers, with no new API calls. D here reads the recorded spoken answers without clarifying questions. The pilot answers have no injected contradictions. 10 users: treat differences under about 0.02 as noise.

## Fixed-form questions (A and B)

| budget | default | chosen on the pilot users |
|---|---|---|
| 5 | CAP01, CAP02, WIL02, WIL03, BEH01 | CAP04, CAP02, WIL01, WIL06, BEH01 |
| 10 | CAP01, CAP02, CAP03, WIL02, WIL03, WIL10, WIL06, BEH01, BEH02, BEH06 | CAP04, CAP02, CAP01, WIL01, WIL06, WIL03, WIL11, BEH01, BEH10, BEH02 |
| 15 | CAP01, CAP02, CAP03, CAP04, CAP05, WIL02, WIL03, WIL10, WIL06, WIL01, BEH01, BEH02, BEH06, BEH05, BEH04 | CAP04, CAP02, CAP01, CAP03, CAP05, WIL01, WIL06, WIL03, WIL11, WIL08, BEH01, BEH10, BEH02, BEH04, BEH09 |
