# Extraction check on the pilot pool (290 labeled answers, 2026-11-12)

| reader | fact right | fact missing | willingness error | willingness missing | behavior error | behavior missing | past/imagined right | calls | $ per answer |
|---|---|---|---|---|---|---|---|---|---|
| D | 0.860 | 0 | 0.106 | 0 | 0.083 | 1 | 0.916 | 1.000 | $0.00114 |
| DR | 0.860 | 0 | 0.100 | 0 | 0.078 | 0 | 0.958 | 1.000 | $0.00144 |
| DP | 0.860 | 0 | 0.130 | 2 | 0.124 | 7 | - | 1.000 | $0.00024 |

fact right: share of fact answers read as a range (D, DR) or top option (DP) that contains the true value. Errors: mean absolute difference from the true score. DP's score is the expected option score. Labels come from the true profiles, so a pilot user who answered off-profile counts against every reader equally.

Paired differences against D (negative = lower error than D), with 95% bootstrap ranges:

- DR willingness: -0.006 (-0.016 to +0.003), 120 answers
- DR behavioral: -0.004 (-0.016 to +0.007), 119 answers
- DP willingness: +0.026 (+0.013 to +0.039), 118 answers
- DP behavioral: +0.039 (+0.021 to +0.059), 113 answers
