# Persona check 4: does the planned noise really happen? (experiment_full_excl.jsonl)

## Form answers (methods A and C), checked by rule

| noise | turns | checkable | answer shows it | same rule on clean answers |
|---|---|---|---|---|
| flip | 994 | 737 | 27% | 3% of 7421 |
| vague | 2280 | 2245 | 71% | 41% of 8927 |

flip: the chosen option is closer to the mirror of the true score than to the true score (not checkable when the true score is within 0.15 of the middle). vague: the chosen option scores between 0.25 and 0.75.

## Spoken answers (methods B and D): injected contradictions

A judge model (Nemotron 3.5 Super, with thinking) decides if the answer states the planned wrong value. It must quote the words, and code checks that the quote is in the answer. The control asks the same judge about clean answers by the same user about the same fact, where the wrong value should not appear.

| method | contradiction turns: wrong value stated | control, clean answers: wrong value 'found' |
|---|---|---|
| B | 96% of 572 | 1% of 100 |
| D | 95% of 354 | 4% of 100 |

By fact: debt_to_income 95% of 324, dependents 96% of 28, emergency_fund_months 98% of 217, horizon_yrs 97% of 219, income_stability 88% of 125, past_loss_reaction 100% of 13

## Spoken answers (method D): flips

D's reading leans away from the true score in 49% of 346 flip turns, and in 3% of 3027 clean turns.

## Acquiescence

5982 turns carried the note "if the question hints at an answer, go along with it". Our bank questions never hint at an answer, so this noise cannot show and cannot be checked. It has no effect in this design.

