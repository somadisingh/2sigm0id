# Adaptive Risk-profiler

Picks which Baseten models to use for the interviewer and for the simulated users, using evidence instead of guesses.

**Stage 1: which interviewer?** Six interviewers (GLM 5.3, DeepSeek V4.1 Flash, Nemotron Ultra, Muse Spark Open, Beam, Kimi K3) each interview the same 5 test users, 10 questions each. The test users are played by OpenAI's gpt-oss-120b, which comes from a different company than all six interviewers, so no interviewer gets an unfair "same model" advantage.

**Stage 2: which simulated user?** The stage 1 winner interviews the 5 test users again, played by each simulated-user candidate with thinking **off** and **low**. After each interview, four quick check questions test whether the fake user stayed true to its persona. Candidates from the same company as the interviewer are skipped automatically.

Every interviewer faces the same noise schedule (vague, contradictory, flipped answers) for each test user, so the comparison is fair.

## Setup (once)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then paste your Baseten API key into .env
```

`.env` is listed in `.gitignore`. Never commit it or paste the key into chat.

## Run

1. **Fix the model IDs.** Only `openai/gpt-oss-120b` is confirmed. The rest of the IDs in `config.py` are guesses.
   ```bash
   python run_bakeoff.py list-models
   ```
   This prints every model on your account and flags each ID in `config.py` as OK or MISSING, with the closest matches. Copy the right IDs into `config.py`.

2. **Check the thinking switches** (a few cents):
   ```bash
   python run_bakeoff.py check
   ```
   If a model shows thinking tokens under `off`, it ignores the off switch. Note it, because its off and low results will then be the same thing.

3. **Stage 1** (about 30 min; gpt-oss's 15 requests/min limit is the bottleneck):
   ```bash
   python run_bakeoff.py stage1
   python score.py results/stage1.jsonl
   ```

4. **Pick the winner.** Lowest avg error wins. If two models' 95% ranges overlap, treat them as tied and choose on valid-JSON rate, cost and full-run time. A model capped at 15 requests/min needs about a day for the full experiment.

5. **Stage 2** (about 10 min):
   ```bash
   python run_bakeoff.py stage2 --interviewer glm-5.3     # use your winner's key
   python score.py results/stage2.jsonl
   ```
   Pick the simulated user with the best persona checks and length adherence at an acceptable cost. A low avg error alone isn't the goal here: a fake user that's too easy to read is the bias the professor warned about.

6. **Compare interviewer prompt versions** (optional, about 10 min):
   ```bash
   python run_bakeoff.py prompts --interviewer glm-5.3 --user deepseek-v4-flash-0731 --user-setting off
   python score.py results/prompts.jsonl
   ```
   Add `--out <file>.jsonl` to rerun the same jobs fresh and see run-to-run noise.

**Decisions so far (Oct 26):** interviewer GLM 5.3, simulated user DeepSeek V4 Flash 0731 with thinking off, interviewer prompt v1 (`INTERVIEWER_PROMPT` in `prompts.py`). v1 caught 22 of 23 targeted contradictions over two runs. v2 and v3 didn't beat it: two v1 runs differed by 0.034 avg error, about as much as any prompt did.

If a run stops partway, rerun the same command and it picks up where it left off. Delete the results file to start fresh. Add `--mock` to any stage to test without a key or cost.

**Expected cost:** both stages should come to roughly $5–15. That's an estimate; `score.py` prints the actual spend.

## What the columns mean

| Column | Meaning |
|---|---|
| avg error | How far the final profile is from the truth, averaged over the 3 dimensions (0–1 scale). Lower is better. This is our main measure. |
| 95% range | Bootstrap range for avg error. Overlapping ranges mean "can't tell apart yet". |
| band exact / within 1 | Final band (lowest of the three) right, or off by one. |
| valid JSON | Share of interviewer replies in the required format on the first try. |
| mismatch caught | For test users whose dimensions disagree (P2, P3), did the interviewer flag it? |
| contradiction caught | After an injected contradiction, did the interviewer flag it on the next turn? |
| false contra/interview | Contradiction flags raised on test users who never contradict themselves. |
| persona checks (stage 2) | Share of the 4 check questions the fake user answered in line with its persona. |
| length ok (stage 2) | Share of answers within the persona's word limit; long, polished answers are the "too articulate" bias. |
| full run $ / time | Projected for the main experiment (1,800 interviews; 36,000 fake-user answers). |

## Files

- `config.py`: models, prices, rate limits, stage settings. Edit here to add or remove models.
- `personas.json`: 5 hand-written test users that follow the shared-contract schema. These are placeholders until the MiroFish personas are ready.
- `prompts.py`: interviewer prompts (v1 in use; v2 and v3 kept for the record), persona prompt, noise notes, check questions. Contradiction notes name a wrong value for a fact the user already stated, so every injected contradiction can be caught.
- `run_bakeoff.py`: runs the stages. `llm.py` handles API calls, rate limits and retries.
- `score.py`: turns results into tables, a CSV and a Markdown summary.

## Limits to keep in mind

- With 5 test users and one run each, this is a screening test, not a final answer. Use `--repeats 2` for more confidence.
- Kimi K3 only offers maximum thinking, so it's included as a quality ceiling, not a realistic pick.
- The interviewer prompt is version 1. If every model does badly, the prompt may be the problem, and that's worth reporting too.
