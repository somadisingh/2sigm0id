# Extraction check on the pilot pool (290 labeled answers, 2026-11-11)

| reader | fact right | fact missing | willingness error | willingness missing | behavior error | behavior missing | past/imagined right | calls | $ per answer |
|---|---|---|---|---|---|---|---|---|---|
| D | 0.900 | 0 | 0.115 | 0 | 0.085 | 4 | 0.940 | 1.000 | $0.00103 |
| DR | 0.860 | 0 | 0.103 | 0 | 0.082 | 1 | 0.958 | 1.000 | $0.00131 |
| DP | 0.880 | 0 | 0.132 | 0 | 0.116 | 8 | - | 1.000 | $0.00023 |

fact right: share of fact answers read as a range (D, DR) or top option (DP) that contains the true value. Errors: mean absolute difference from the true score. DP's score is the expected option score. Labels come from the true profiles, so a pilot user who answered off-profile counts against every reader equally.

Paired differences against D (negative = lower error than D), with 95% bootstrap ranges:

- DR willingness: -0.012 (-0.025 to +0.000), 120 answers
- DR behavioral: -0.005 (-0.028 to +0.012), 116 answers
- DP willingness: +0.017 (+0.004 to +0.031), 120 answers
- DP behavioral: +0.027 (+0.014 to +0.040), 110 answers
