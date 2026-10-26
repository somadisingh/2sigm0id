# Bake-off runs, Oct 26 2026

Raw results (`.jsonl`, one interview per line) and the tables `score.py` made from them (`_summary.md`, `_summary.csv`). All runs used the 5 placeholder test users in `personas.json` and a 10-question budget. Total spend was $4.08 across these files, plus a few cents for model and settings checks.

| File | What ran | Main result |
|---|---|---|
| `stage1` | 6 interviewers, each interviewing gpt-oss-120b playing the 5 users | Kimi K3 (0.107), GLM 5.3 (0.110) and Beam (0.110) tied for lowest avg error. GLM 5.3 picked on cost and speed. |
| `stage2` | GLM 5.3 interviewing 4 simulated-user candidates, thinking off and low | DeepSeek V4 Flash 0731 (off) picked: 100% persona checks, follows each persona's speaking style, cheapest. |
| `prompts_oldnoise` | Prompt v1 vs v2, 3 repeats, old contradiction notes | Contradiction catch rates looked low (13% vs 31%), but many injected "contradictions" never actually contradicted anything. |
| `prompts` | Prompt v1, v2 and v3, 3 repeats, contradictions that name an already-stated fact | v1 caught 10 of 11, v3 10 of 11, v2 10 of 13. v1 had the lowest avg error. |
| `prompts_v1_rerun` | Fresh rerun of v1 with the same seeds | Avg error 0.149 vs 0.114 the first time, so run-to-run noise is about as large as the gaps between prompts. v1 kept. |

Notes:
- Stage 1 and 2 used the old contradiction notes, so their "contradiction caught" columns understate every model. That doesn't change which models were picked.
- Beam's first 5 stage 1 interviews failed (Baseten wanted its reasoning sent back) and were rerun after the `allow_missing_thinking` fix. Only the successful runs are in `stage1.jsonl`.
- To re-score a file from the repo root: `python score.py old_runs/2026-10-26-bakeoff/stage1.jsonl`.
