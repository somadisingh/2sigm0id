# Extraction check on the pilot pool (290 labeled answers, 2026-11-11)

| reader | fact right | fact missing | willingness error | willingness missing | behavior error | behavior missing | past/imagined right | calls | $ per answer |
|---|---|---|---|---|---|---|---|---|---|
| D | 0.880 | 0 | 0.120 | 0 | 0.087 | 2 | 0.907 | 1.000 | $0.00105 |
| DR | 0.860 | 0 | 0.104 | 0 | 0.093 | 1 | 0.966 | 1.000 | $0.00134 |
| DP | 0.820 | 0 | 0.125 | 0 | 0.131 | 6 | - | 1.000 | $0.00024 |

fact right: share of fact answers read as a range (D, DR) or top option (DP) that contains the true value. Errors: mean absolute difference from the true score. DP's score is the expected option score. Labels come from the true profiles, so a pilot user who answered off-profile counts against every reader equally.

Paired differences against D (negative = lower error than D), with 95% bootstrap ranges:

- DR willingness: -0.017 (-0.029 to -0.005), 120 answers
- DR behavioral: +0.005 (-0.006 to +0.017), 118 answers
- DP willingness: +0.005 (-0.011 to +0.022), 120 answers
- DP behavioral: +0.044 (+0.020 to +0.070), 114 answers
