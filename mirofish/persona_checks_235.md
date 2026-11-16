# Persona checks 2, 3 and 5 (100 test users, backstories on)

Each test user answered 8 new multiple-choice questions (4 willingness, 4 behavior, none from `question_bank.json`) with no noise. Each option has a fixed score. Script: `mirofish/persona_checks.py`.

| check | rule | users that fail |
|---|---|---|
| 2. profile | average willingness and behavior score in the true band or one away | 1% of 100 |
| 3. repeat | same option on at least 5 of 8 in a second conversation | 2% of 100 |
| 5. models | DeepSeek, Nemotron (and Muse on 10 users) within one band on both | 2% of 100 |

**Users that fail 2 or more checks (left out of the scoring): 1**: U054-b5-match-moderate

- Check 2, willingness: exact band 74% of 100.
- Check 2, behavioral: exact band 86% of 100.
- Check 3: same option on 90% of 800 answers overall.
- Check 5: all models gave exactly the same two bands for 69% of 100 users.
- Unclear answers (no option could be read): 0 of 800.

**"says aggressive, would panic-sell" users (12).** They must talk bold and act scared.

- Willingness answers bold enough (true band or one away): 100% of 12
- Behavior answers scared enough (true band or one away): 100% of 12
- Willingness average higher than behavior average: 100% of 12
- Pass check 2: 100% of 12

Cost of this run: about $0.51.

## Per user

c5 bands: willingness,behavior band from each model, in the order DeepSeek / Nemotron / Muse.

| id | final_band | mismatch_type | true_will_band | c2_will_band | true_beh_band | c2_beh_band | check2 | c3_same_of_8 | check3 | c5_bands | check5 | fails | exclude |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| U054-b5-match-moderate | 5 | none | 5 | 3 | 5 | 5 | FAIL | 6 | pass | 3,5 / 5,5 | FAIL | 2 | **yes** |
| U017-b3-panic-clean | 3 | says aggressive, would panic-sell | 5 | 5 | 3 | 4 | pass | 4 | FAIL | 5,4 / 4,3 | pass | 1 |  |
| U021-b4-match-moderate | 4 | none | 4 | 5 | 5 | 5 | pass | 7 | pass | 5,5 / 3,5 / 5,5 | FAIL | 1 |  |
| U036-b2-panic-moderate | 2 | says aggressive, would panic-sell | 4 | 5 | 2 | 2 | pass | 3 | FAIL | 5,2 / 4,2 | pass | 1 |  |
| S1-clean-moderate | 3 | none | 3 | 3 | 3 | 4 | pass | 8 | pass | 3,4 / 3,3 / 3,3 | pass | 0 |  |
| S2-says-aggressive-panics | 2 | says aggressive, would panic-sell | 5 | 5 | 2 | 2 | pass | 8 | pass | 5,2 / 5,2 | pass | 0 |  |
| S3-eager-cant-afford | 2 | says aggressive, can't afford it | 4 | 5 | 4 | 4 | pass | 7 | pass | 5,4 / 5,4 | pass | 0 |  |
| S4-able-but-cautious | 1 | can afford risk, prefers caution | 1 | 1 | 2 | 2 | pass | 8 | pass | 1,2 / 1,2 | pass | 0 |  |
| S5-vague-contradictory | 2 | none | 3 | 3 | 3 | 4 | pass | 7 | pass | 3,4 / 3,3 | pass | 0 |  |
| U006-b5-match-clean | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U007-b4-match-clean | 4 | none | 4 | 5 | 5 | 5 | pass | 7 | pass | 5,5 / 5,5 | pass | 0 |  |
| U008-b3-panic-heavy | 3 | says aggressive, would panic-sell | 5 | 5 | 3 | 3 | pass | 7 | pass | 5,3 / 4,3 | pass | 0 |  |
| U009-b2-match-moderate | 2 | none | 2 | 2 | 2 | 2 | pass | 8 | pass | 2,2 / 2,2 | pass | 0 |  |
| U010-b3-panic-heavy | 3 | says aggressive, would panic-sell | 5 | 5 | 3 | 3 | pass | 6 | pass | 5,3 / 5,3 | pass | 0 |  |
| U011-b2-match-clean | 2 | none | 2 | 3 | 3 | 4 | pass | 8 | pass | 3,4 / 3,3 / 2,3 | pass | 0 |  |
| U012-b1-match-heavy | 1 | none | 1 | 1 | 1 | 2 | pass | 6 | pass | 1,2 / 1,1 | pass | 0 |  |
| U013-b1-match-clean | 1 | none | 2 | 1 | 1 | 2 | pass | 5 | pass | 1,2 / 2,2 | pass | 0 |  |
| U014-b3-cantafford-heavy | 3 | says aggressive, can't afford it | 5 | 5 | 4 | 4 | pass | 7 | pass | 5,4 / 5,4 | pass | 0 |  |
| U015-b5-match-moderate | 5 | none | 5 | 5 | 5 | 5 | pass | 7 | pass | 5,5 / 5,5 | pass | 0 |  |
| U016-b3-cautious-moderate | 3 | can afford risk, prefers caution | 3 | 3 | 5 | 5 | pass | 8 | pass | 3,5 / 4,5 | pass | 0 |  |
| U018-b5-match-heavy | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U019-b5-match-moderate | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U020-b3-cautious-heavy | 3 | can afford risk, prefers caution | 3 | 3 | 5 | 5 | pass | 7 | pass | 3,5 / 3,5 | pass | 0 |  |
| U022-b1-panic-moderate | 1 | says aggressive, would panic-sell | 4 | 5 | 1 | 1 | pass | 6 | pass | 5,1 / 4,1 | pass | 0 |  |
| U023-b1-panic-clean | 1 | says aggressive, would panic-sell | 4 | 4 | 1 | 1 | pass | 6 | pass | 4,1 / 5,1 | pass | 0 |  |
| U024-b5-match-moderate | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U025-b4-match-heavy | 4 | none | 4 | 4 | 4 | 4 | pass | 6 | pass | 4,4 / 4,4 | pass | 0 |  |
| U026-b3-cantafford-heavy | 3 | says aggressive, can't afford it | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U027-b1-cantafford-moderate | 1 | says aggressive, can't afford it | 5 | 5 | 2 | 2 | pass | 7 | pass | 5,2 / 5,2 | pass | 0 |  |
| U028-b2-cantafford-moderate | 2 | says aggressive, can't afford it | 5 | 5 | 4 | 4 | pass | 5 | pass | 5,4 / 5,4 | pass | 0 |  |
| U029-b3-match-moderate | 3 | none | 3 | 3 | 3 | 3 | pass | 7 | pass | 3,3 / 3,3 | pass | 0 |  |
| U030-b4-match-clean | 4 | none | 5 | 5 | 4 | 4 | pass | 6 | pass | 5,4 / 5,4 | pass | 0 |  |
| U031-b4-match-clean | 4 | none | 4 | 5 | 4 | 4 | pass | 7 | pass | 5,4 / 4,4 / 5,4 | pass | 0 |  |
| U032-b5-match-clean | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U033-b3-match-moderate | 3 | none | 4 | 5 | 3 | 3 | pass | 8 | pass | 5,3 / 5,3 | pass | 0 |  |
| U034-b1-cautious-clean | 1 | can afford risk, prefers caution | 1 | 1 | 2 | 2 | pass | 8 | pass | 1,2 / 1,2 | pass | 0 |  |
| U035-b4-match-heavy | 4 | none | 4 | 5 | 4 | 4 | pass | 7 | pass | 5,4 / 4,4 | pass | 0 |  |
| U037-b5-match-heavy | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U038-b3-cantafford-heavy | 3 | says aggressive, can't afford it | 5 | 5 | 4 | 4 | pass | 8 | pass | 5,4 / 5,4 | pass | 0 |  |
| U039-b2-match-heavy | 2 | none | 2 | 2 | 3 | 3 | pass | 7 | pass | 2,3 / 3,3 | pass | 0 |  |
| U040-b4-match-clean | 4 | none | 5 | 5 | 4 | 5 | pass | 6 | pass | 5,5 / 5,4 | pass | 0 |  |
| U041-b5-match-moderate | 5 | none | 5 | 4 | 5 | 5 | pass | 7 | pass | 4,5 / 5,5 / 5,5 | pass | 0 |  |
| U042-b1-panic-heavy | 1 | says moderate, would panic-sell | 3 | 3 | 1 | 2 | pass | 6 | pass | 3,2 / 3,1 | pass | 0 |  |
| U043-b5-match-clean | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U044-b5-match-heavy | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U045-b4-match-heavy | 4 | none | 4 | 5 | 4 | 4 | pass | 6 | pass | 5,4 / 4,4 | pass | 0 |  |
| U046-b2-panic-heavy | 2 | says aggressive, would panic-sell | 5 | 5 | 2 | 2 | pass | 8 | pass | 5,2 / 5,2 | pass | 0 |  |
| U047-b3-cautious-moderate | 3 | can afford risk, prefers caution | 3 | 3 | 3 | 3 | pass | 8 | pass | 3,3 / 3,3 | pass | 0 |  |
| U048-b4-match-moderate | 4 | none | 4 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U049-b5-match-moderate | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U050-b1-cantafford-heavy | 1 | says aggressive, can't afford it | 5 | 5 | 3 | 3 | pass | 6 | pass | 5,3 / 5,3 | pass | 0 |  |
| U051-b1-match-heavy | 1 | none | 1 | 1 | 1 | 1 | pass | 8 | pass | 1,1 / 1,1 / 1,1 | pass | 0 |  |
| U052-b1-match-moderate | 1 | none | 2 | 2 | 1 | 1 | pass | 8 | pass | 2,1 / 2,2 | pass | 0 |  |
| U053-b5-match-heavy | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U055-b3-match-moderate | 3 | none | 3 | 3 | 3 | 3 | pass | 8 | pass | 3,3 / 3,3 | pass | 0 |  |
| U056-b3-match-clean | 3 | none | 4 | 5 | 4 | 4 | pass | 7 | pass | 5,4 / 5,4 | pass | 0 |  |
| U057-b4-match-heavy | 4 | none | 4 | 4 | 4 | 4 | pass | 7 | pass | 4,4 / 4,4 | pass | 0 |  |
| U058-b1-cantafford-moderate | 1 | says aggressive, can't afford it | 4 | 4 | 3 | 3 | pass | 6 | pass | 4,3 / 4,3 | pass | 0 |  |
| U059-b2-cantafford-clean | 2 | says aggressive, can't afford it | 5 | 5 | 3 | 3 | pass | 7 | pass | 5,3 / 5,3 | pass | 0 |  |
| U060-b2-match-heavy | 2 | none | 2 | 2 | 2 | 2 | pass | 8 | pass | 2,2 / 3,2 | pass | 0 |  |
| U061-b4-match-clean | 4 | none | 5 | 5 | 4 | 4 | pass | 8 | pass | 5,4 / 5,4 / 5,4 | pass | 0 |  |
| U062-b5-match-moderate | 5 | none | 5 | 5 | 5 | 5 | pass | 7 | pass | 5,5 / 5,5 | pass | 0 |  |
| U063-b1-match-clean | 1 | none | 2 | 2 | 1 | 2 | pass | 8 | pass | 2,2 / 3,2 | pass | 0 |  |
| U064-b2-match-moderate | 2 | none | 2 | 2 | 2 | 2 | pass | 8 | pass | 2,2 / 2,2 | pass | 0 |  |
| U065-b1-match-clean | 1 | none | 1 | 2 | 2 | 2 | pass | 7 | pass | 2,2 / 2,2 | pass | 0 |  |
| U066-b2-cautious-clean | 2 | can afford risk, prefers caution | 2 | 3 | 4 | 4 | pass | 7 | pass | 3,4 / 3,4 | pass | 0 |  |
| U067-b3-match-clean | 3 | none | 3 | 3 | 3 | 4 | pass | 8 | pass | 3,4 / 3,3 | pass | 0 |  |
| U068-b4-match-clean | 4 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U069-b4-match-heavy | 4 | none | 4 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U070-b4-match-heavy | 4 | none | 5 | 5 | 4 | 4 | pass | 8 | pass | 5,4 / 5,4 | pass | 0 |  |
| U071-b2-match-clean | 2 | none | 2 | 2 | 2 | 2 | pass | 8 | pass | 2,2 / 2,2 / 2,2 | pass | 0 |  |
| U072-b2-panic-clean | 2 | says aggressive, would panic-sell | 5 | 5 | 2 | 2 | pass | 8 | pass | 5,2 / 5,2 | pass | 0 |  |
| U073-b3-panic-heavy | 3 | says aggressive, would panic-sell | 5 | 5 | 3 | 3 | pass | 8 | pass | 5,3 / 5,3 | pass | 0 |  |
| U074-b5-match-clean | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U075-b3-cantafford-clean | 3 | says aggressive, can't afford it | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U076-b5-match-clean | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U077-b1-panic-moderate | 1 | says aggressive, would panic-sell | 5 | 5 | 1 | 1 | pass | 7 | pass | 5,1 / 5,1 | pass | 0 |  |
| U078-b3-match-moderate | 3 | none | 3 | 3 | 4 | 4 | pass | 7 | pass | 3,4 / 3,4 | pass | 0 |  |
| U079-b4-match-clean | 4 | none | 4 | 5 | 4 | 4 | pass | 8 | pass | 5,4 / 5,4 | pass | 0 |  |
| U080-b3-match-heavy | 3 | none | 4 | 4 | 3 | 3 | pass | 6 | pass | 4,3 / 4,3 | pass | 0 |  |
| U081-b2-match-moderate | 2 | none | 2 | 3 | 3 | 4 | pass | 7 | pass | 3,4 / 3,3 / 3,3 | pass | 0 |  |
| U082-b3-match-heavy | 3 | none | 3 | 3 | 3 | 4 | pass | 8 | pass | 3,4 / 3,3 | pass | 0 |  |
| U083-b2-cautious-moderate | 2 | can afford risk, prefers caution | 2 | 3 | 4 | 4 | pass | 6 | pass | 3,4 / 4,4 | pass | 0 |  |
| U084-b2-cautious-clean | 2 | can afford risk, prefers caution | 2 | 3 | 4 | 4 | pass | 6 | pass | 3,4 / 3,4 | pass | 0 |  |
| U085-b1-match-clean | 1 | none | 2 | 2 | 1 | 2 | pass | 7 | pass | 2,2 / 2,1 | pass | 0 |  |
| U086-b4-match-heavy | 4 | none | 4 | 5 | 4 | 4 | pass | 8 | pass | 5,4 / 5,4 | pass | 0 |  |
| U087-b2-panic-clean | 2 | says aggressive, would panic-sell | 4 | 5 | 2 | 2 | pass | 7 | pass | 5,2 / 4,2 | pass | 0 |  |
| U088-b4-match-clean | 4 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U089-b5-match-moderate | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U090-b1-match-moderate | 1 | none | 1 | 1 | 1 | 1 | pass | 7 | pass | 1,1 / 1,1 | pass | 0 |  |
| U091-b1-cantafford-heavy | 1 | says aggressive, can't afford it | 5 | 5 | 2 | 2 | pass | 6 | pass | 5,2 / 5,2 / 5,2 | pass | 0 |  |
| U092-b5-match-clean | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U093-b4-match-moderate | 4 | none | 4 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U094-b2-cantafford-moderate | 2 | says aggressive, can't afford it | 5 | 5 | 2 | 2 | pass | 8 | pass | 5,2 / 5,2 | pass | 0 |  |
| U095-b5-match-heavy | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U096-b4-match-heavy | 4 | none | 4 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U097-b1-cautious-clean | 1 | can afford risk, prefers caution | 1 | 1 | 1 | 1 | pass | 6 | pass | 1,1 / 2,1 | pass | 0 |  |
| U098-b4-match-heavy | 4 | none | 5 | 5 | 4 | 4 | pass | 7 | pass | 5,4 / 5,4 | pass | 0 |  |
| U099-b5-match-moderate | 5 | none | 5 | 5 | 5 | 5 | pass | 8 | pass | 5,5 / 5,5 | pass | 0 |  |
| U100-b1-cautious-moderate | 1 | can afford risk, prefers caution | 1 | 1 | 1 | 2 | pass | 7 | pass | 1,2 / 1,1 | pass | 0 |  |
