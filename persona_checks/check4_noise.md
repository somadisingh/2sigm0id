# Persona check 4: does the planned noise really happen? (experiment_100users_b10.jsonl)

## Form answers (methods A and C), checked by rule

| noise | turns | checkable | answer shows it | same rule on clean answers |
|---|---|---|---|---|
| flip | 113 | 75 | 21% | 3% of 807 |
| vague | 282 | 275 | 74% | 40% of 973 |

flip: the chosen option is closer to the mirror of the true score than to the true score (not checkable when the true score is within 0.15 of the middle). vague: the chosen option scores between 0.25 and 0.75.

## Spoken answers (methods B and D): injected contradictions

A judge model (Nemotron 3.5 Super, with thinking) decides if the answer states the planned wrong value. It must quote the words, and code checks that the quote is in the answer. The control asks the same judge about clean answers by the same user about the same fact, where the wrong value should not appear.

| method | contradiction turns: wrong value stated | control, clean answers: wrong value 'found' |
|---|---|---|
| B | 93% of 61 | 0% of 48 |
| D | 91% of 35 | 8% of 37 |

By fact: debt_to_income 89% of 28, emergency_fund_months 100% of 29, horizon_yrs 95% of 22, income_stability 81% of 16, past_loss_reaction 100% of 1

## Spoken answers (method D): flips

D's reading leans away from the true score in 57% of 40 flip turns, and in 5% of 308 clean turns.

## Acquiescence

208 turns carried the note "if the question hints at an answer, go along with it". Our bank questions never hint at an answer, so this noise cannot show and cannot be checked. It has no effect in this design.

