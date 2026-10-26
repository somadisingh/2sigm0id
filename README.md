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

## Main experiment (methods A–D)

Runs all four methods on the same test users, with the same noise schedule and the same question budget:

| Method | What it does |
|---|---|
| A, fixed form | The default short form from `question_bank.json`, in order. The person picks an option number. |
| B, scripted interview | The same questions in their spoken wording. The person answers in their own words, and the interviewer model maps each answer to an option, or to none if the answer is too vague. |
| C, adaptive form | Picks each next question from the whole bank, aiming at the dimension it's least sure about: few answers, answers that disagree, an estimate near a band edge, or the dimension that decides the final band. No calibration data exists for a classic test model, so this rule is ours. |
| D, adaptive interviewer | Our system: GLM 5.3 with prompt v1. |

```bash
python run_bakeoff.py experiment                        # all methods, budgets 5/10/15, 3 repeats
python run_bakeoff.py experiment --methods A D --budgets 10 --repeats 1   # a quick smoke test
python score.py results/experiment.jsonl --by-persona
```

Models and thinking settings come from the `EXPERIMENT_*` lines in `config.py`. Contradictions are injected only in the spoken methods (B and D), since a form has no follow-ups.

**Estimated cost:** about $2 and 30 minutes with the 5 placeholder test users. With 100 test users it's about $60–75 and 5 hours; B's answer mapping adds roughly $15 to the earlier projection. These are estimates; `score.py` prints the actual spend.

**score.py options:** `--by-persona` adds an error table per test user, and `--truth formula` re-scores older runs with capacity from `capacity.py`. Recovery shows how often the final estimate came back after a contradiction pulled it off course.

## Question bank

`question_bank.json` holds the 35 shared questions for methods A, B and C: 11 on capacity, 12 on willingness, 12 on behavior. `question_bank.md` is a readable copy. Run `python check_question_bank.py --write-md` after editing the JSON; it checks the format and regenerates the readable copy. The default short forms are placeholders until a pilot picks the most informative questions.

## Capacity formula

`capacity.py` turns a person's money facts into a capacity score: time horizon 30%, emergency savings 25%, income stability 20%, debt payments 15%, dependents 10%. It then applies three red-flag caps: needing the money within 3 years (at most 0.20), under 1 month of savings (at most 0.35), and debt payments of 40% or more of income (at most 0.35). It sets every test user's true capacity, and `run_bakeoff.py` refuses to run if a persona's capacity doesn't match it. Run `python capacity.py` to see each test user's breakdown. The weights are our judgment and are recorded in the shared contract.

Re-scoring the Oct 26 runs with the formula cut P1's capacity error from +0.27 to +0.05, so that "mistake" was mostly our hand-set label.

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
- `personas.json`: 5 hand-written test users that follow the shared-contract schema, with capacity from the formula and every true score at least 0.03 from a band edge. These are placeholders until the MiroFish personas are ready.
- `capacity.py`: the capacity formula.
- `question_bank.json` / `question_bank.md`: the 35 shared questions; `check_question_bank.py` checks them.
- `methods.py`: methods A, B and C for the main experiment.
- `prompts.py`: interviewer prompts (v1 in use; v2 and v3 kept for the record), persona prompt, noise notes, check questions. Contradiction notes name a wrong value for a fact the user already stated, so every injected contradiction can be caught.
- `run_bakeoff.py`: runs the stages. `llm.py` handles API calls, rate limits and retries.
- `score.py`: turns results into tables, a CSV and a Markdown summary.

## Limits to keep in mind

- With 5 test users and one run each, this is a screening test, not a final answer. Use `--repeats 2` for more confidence.
- Kimi K3 only offers maximum thinking, so it's included as a quality ceiling, not a realistic pick.
- The interviewer prompt is version 1. If every model does badly, the prompt may be the problem, and that's worth reporting too.
