# Backstory rewrite check

`rewrite_backstories.py` (Nov 13, 2026). Only the risk sentences changed; the true scores did not.

Stories: 100. With problems after 3 tries: 0.

## Blind read (GLM 5.3, does not see the true profile)

It should still recover the profile from the new stories, about as well as from the old ones.

| | old stories | new stories |
|---|---|---|
| willingness exact | 88/100 | 77/100 |
| willingness within 1 | 100/100 | 100/100 |
| behavior exact | 61/100 | 72/100 |
| behavior within 1 | 93/100 | 94/100 |
| past right | 100/100 | 100/100 |

## Sameness

| | old | new |
|---|---|---|
| 5-word phrases in 5+ stories | 414 | 295 |
| stories with "sleep" | 12 | 0 |
| stories with "panic" | 14 | 0 |

Most repeated 5-word phrases, new: "needing it in about years" (56); "payments take about of it" (51); "take about of it and" (50); "debt payments take about of" (50); "never been through a big" (45)

## Users the blind read missed by 2+ bands (new stories)

- S3-eager-cant-afford: behavior read 2, true 4
- U021-b4-match-moderate: behavior read 3, true 5
- U037-b5-match-heavy: behavior read 3, true 5
- U049-b5-match-moderate: behavior read 3, true 5
- U069-b4-match-heavy: behavior read 3, true 5
- U088-b4-match-clean: behavior read 2, true 5
