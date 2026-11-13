# Team plan to Milestone 3 (written Nov 11, 2026)

This file is for Preyansh and Siya. It tells you what is done, what Somaditya does now, and what each of you must do. Read all of it once. Then use sections 6 and 7 as your checklist.

The file uses simple, short sentences. Section 10 explains the words that we use. If something in this file is not clear, ask Somaditya. Do not guess.

## 1. Dates

| Date | What happens |
|---|---|
| Thu Nov 12 | Preyansh reviews the belief engine. Siya decides the corrections design. Siya and Somaditya set up the backstories together. |
| Fri Nov 13 | Somaditya starts the full experiment run. Preyansh sends the ablation plan. |
| Sat Nov 14 | Preyansh's live chat is ready. Siya can start the classmate study. |
| Mon Nov 16 | All results are ready for writing. |
| Tue Nov 17 | Each person sends a draft of their Milestone 3 sections. |
| Thu Nov 19 | Milestone 3 is due. |

## 2. What the project is now

The system finds a person's risk profile through a short conversation. The profile has three scores from 0 to 1:

- **Capacity**: how much loss the person can afford. It comes from five money facts: years until they need the money, emergency savings, income stability, debt payments and dependents. A fixed formula (`capacity.py`) turns the facts into the score.
- **Willingness**: how the person *says* they feel about risk.
- **Behavior**: what the person *does*, or would do, in a real loss.

Each score becomes a band from 1 (very careful) to 5 (very bold). The final band is the lowest of the three bands.

We compare four methods. Every method asks the same number of questions (5, 10 or 15):

| Method | How it chooses questions | How it reads answers |
|---|---|---|
| A, fixed form | Same questions, same order, for every person | The person picks an option number |
| B, scripted interview | Same as A | The person talks; an AI model picks the matching option |
| C, adaptive form | The belief engine chooses each question | The person picks an option number |
| D, adaptive interviewer (our system) | The belief engine chooses each question. It can ask again about a fact to clear up a conflict. | The person talks; an AI model turns the answer into evidence |

The "test users" are AI models that play a person with a known true profile. Siya's 100 test users are in `mirofish/personas_100_with_backstories.json`. The 10 pilot users are in `mirofish/personas_pilot.json`. We use the pilot users only to tune the system. We never score them.

## 3. The professor's Milestone 2 feedback, and our answer

The professor said that the technical details were not clear. The professor also said that a project that is mainly prompt chaining is not sufficient. "Prompt chaining" means that we only send instructions to an AI model, one after another, and the model does all the work. The professor asked three questions.

### Question 1: How does the system choose the next question? How does it know that another question will not change the band?

**Our answer: the belief engine** (`belief.py`, on `main` since Nov 12). It is normal code, not an AI model.

1. For each score, the engine keeps a range of possible values, with a probability for each value. A wide range means that the engine is not sure.
2. Each answer makes the range smaller. A real past action counts most. A stated feeling counts less. An answer about an imagined situation counts least. A vague answer counts half.
3. For capacity, the engine keeps a range for each money fact. It runs the capacity formula on 2,000 random samples of the facts. So a fact that nobody asked about keeps capacity uncertain.
4. From the three ranges, the engine calculates the probability of each final band.
5. For each possible question, the engine calculates how much the answer will probably tell us about the final band. It asks the question that tells us the most.
6. Before each question, the engine simulates 100 possible futures for the remaining questions. If the band changes in fewer than 5 of the 100 futures, another question is unlikely to change the band. That is the stop point. In the experiment, the engine records the stop point and continues, so that all methods ask the same number of questions.

The professor gave an example. A person says that they like risk, but their past behavior shows panic-selling. Our engine then asks the past-behavior question next. Another willingness question has a value of zero, because it cannot change the band. The file `test_belief.py` tests this example.

When two answers about the same fact do not agree, the engine keeps both values possible. The question about that fact then has the highest value, so method D asks it again in a neutral way. In a test, D caught a false statement, asked again two times, and ended with the correct band.

### Question 2: How do you show that the AI test users answer in line with their profiles?

**Our answer: six persona checks** (section 7 gives the details):

1. The test user states its money facts correctly when we ask directly. (Somaditya)
2. The test user answers new check questions in line with its true willingness and behavior. (Siya)
3. The same test user gives the same answers in two separate runs. (Siya)
4. The planned noise really occurs. For example, when we tell the test user to contradict itself, the wrong value appears in the answer. (Somaditya)
5. Three AI models from three companies play the same test user, and their answers agree. (Siya)
6. People read 20 conversations without the true profile and guess the band. (Siya, with Preyansh and Somaditya as readers)

**Results of checks 1 and 4 (Nov 11, backstories off).** The code is `check_personas.py`. The full tables are in `persona_checks/`.

- Check 1: 89 of the 100 test users state all six facts correctly. No user has two or more wrong facts.
- Check 1 found two small problems:
  - 16 users have the income "stable and high". When we ask, they say "stable". The capacity formula counts "stable and high" as "very stable". So these users can get a capacity that is too low.
  - 2 users say "three" dependents when the true number is 2.
- Check 4: an injected contradiction states the planned wrong value in 91% to 93% of the cases. On clean answers, the judge found the wrong value in only 0% to 8%. So this noise works.
- Check 4: a "flip" note changes the spoken answer in 57% of the cases. It changes a form answer in only 21%.
- Check 4: a "vague" note makes a form answer pick a middle option in 74% of the cases (clean answers: 40%).
- Check 4: the "acquiescence" note has no effect. Our questions never suggest an answer, so the test user has nothing to agree with.

### Question 3: Compare the methods on cost and speed too, not only on the number of questions.

**Our answer: done** (on `main`). The scorer (`score.py`) shows four values for each completed profile: the number of AI calls, the tokens, the cost in dollars, and the wait time per question. It also saves a chart of error against cost. Results from a small test: A and C cost $0. B costs about $0.003. Old D cost $0.029 and made the person wait 9.2 seconds per question. New D costs $0.011 and makes the person wait 1.8 seconds per question.

### The "more generative AI" concern

The AI model now does the language work, and code makes the decisions. Research shows that AI models do not track evidence well over many turns, so this split is intentional. Somaditya is adding three generative AI parts. Each part has its own measured test:

1. **Retrieval** (course topic: retrieval-augmented generation). Before the AI model reads an answer, the system finds 3 similar answers from the pilot users with their correct readings. It gives them to the model as examples.
2. **Token probabilities** (course topics: next-token prediction, decoding). The model picks the matching option, and we read the model's own probability for every option. We then correct these probabilities on the pilot users. The model's raw probabilities were too confident: it was right 82% of the time, but it said it was much more sure than that. After the correction, the confidence matched the accuracy (calibration error went from 0.18 to 0.05).
3. **Faithfulness test** (course topic: evaluating generative AI, hallucination tests). This test finds facts that the model reads from an answer but that the person never said.

First results (Nov 11, on 290 labeled answers from the pilot users):

- The tests found an error in the reading step. The model read "I held on" as the highest behavior score. We fixed the scale. This fix made the readings more accurate than retrieval did.
- After the fix, retrieval does not clearly make the readings more accurate.
- Token probabilities cost 78% less per answer, but the readings are a little less accurate.
- The judge model of the faithfulness test is not reliable yet. It gave a different result for 15% of the same readings when we ran it again. So we need people to label 50 readings by hand (task L1 in section 8).

## 4. What is done (up to Nov 11)

| Done | Where |
|---|---|
| Model choice: GLM 5.3 reads answers; DeepSeek V4 Flash 0731 plays the test users | `config.py`, `old_runs/` |
| Interviewer prompt v1 locked (for the old D) | `prompts.py` |
| Capacity formula | `capacity.py` |
| 35-question bank | `question_bank.json` |
| Cost and speed logging, cost chart | `score.py` (on `main`) |
| Every method uses its full question budget | `run_bakeoff.py` (on `main`) |
| Siya's 100 test users and 10 pilot users, checked and merged | `mirofish/` (on `main`) |
| Belief engine, methods C and D on the engine, tests, design note | `belief.py`, `methods.py`, `test_belief.py`, `BELIEF_ENGINE.md` |
| Leak fix, and the belief engine fitted on the pilot users | `prompts.py`, `pilot/fitted.json`, `pilot/fit.md` |
| Labeled answers from the 10 pilot users, retrieval (DR), token probabilities (DP), faithfulness test | `pilot.py`, `retrieval.py`, `check_extractor.py`, `pilot/`. Results: `BELIEF_ENGINE.md`, section "Generative AI parts in method D". |

Two findings so far:

- **Willingness mixed with behavior.** One test user is told to *talk* bold but to *act* scared. That user answered the willingness questions with scared answers. So the AI test user mixes the two scores. Persona check 2 must test for this.
- **Old leak (fixed Nov 11).** The test-user instructions described behavior with the words "20% in a month". Bank question BEH01 uses the same words. Somaditya changed the test-user wording. All pilot answers were then made again.
- **Past actions are weak evidence for our test users.** We fitted the belief engine on the pilot users. Past-action questions told us the least about the behavior score, not the most. The test users' past-loss story (held, sold or none) does not follow their behavior score closely. The engine now uses the fitted values (`pilot/fitted.json`, explained in `pilot/fit.md`).

### First run on all 100 test users (Nov 11, budget 10, one run each, $1.83)

This is a preview, not the full run. Details: `BELIEF_ENGINE.md`, section "Run on all 100 test users".

| Method | avg error | final band exactly right |
|---|---|---|
| A, fixed form | 0.122 | 47% |
| B, scripted interview | 0.129 | 45% |
| C, adaptive form (belief engine) | **0.104** | **68%** |
| D, adaptive interviewer (belief engine + conversation) | 0.129 (0.116 after the fix below) | 51% (53%) |

- **C is better than A.** The difference is clear, not noise. So the belief engine works.
- **The stop rule keeps its promise.** After the stop point, the band changed in only 5% of the runs.
- **D was only as good as A.** The problem was willingness. Some test users say that they like risk but would panic or cannot afford it. In conversation, these users talk about their panic when we ask about their attitude. Then the AI model read their willingness as too low. On a form, the same users tick the bold answers. This is the professor's question about how to keep willingness apart from behavior.
- **Fix (Nov 11).** The AI model now scores what the person claims about their attitude, and puts actions under behavior. After the fix, D's avg error went from 0.129 to 0.116. For "says aggressive, would panic-sell" users, the willingness error went from −0.19 to −0.05. D is now a little better than A and a little worse than C, but these differences are not clear yet. We found the problem on the same 100 users that the full run uses, so Milestone 3 must say this.
- Siya's persona check 2 (task S3) and Preyansh's review (task P1) must look at this. "Can't afford it" users still get a willingness that is too low (−0.12).

### After Preyansh's review (Nov 12)

We made all review changes and checked D on 20 test users. D's avg error is the same as before the review (0.113 against 0.115). D now reads willingness and behavior better than every other method on these 20 users. But **D's capacity is worse than C's** (0.180 against 0.101). D reads money facts from speech, and only the spoken methods get false facts injected. This is the first problem for the failure analysis after the full run.

## 5. What Somaditya does now

### Phase 1: Nov 11 to Nov 13 (before the full run)

1. Finish the three generative AI parts in section 3 and test each one on the pilot users.
2. With Siya: add the backstories to the test-user instructions (section 7, task S1). (Done Nov 13: on, with the risk sentences rewritten.)
3. Remove the "20% in a month" leak. (Done Nov 11.)
4. Build persona checks 1 and 4. (Done Nov 11. Check 1 run again on Nov 13 with the backstories on: 92 of 100. Check 4 runs again on the full-run results.)
5. Fit the evidence strengths of the belief engine on the pilot users. Choose the fixed-form questions on the pilot users. (Done Nov 11. The fitted evidence strengths are in use. The fixed-form questions chosen on the pilot users were worse for a left-out pilot user, so A and B keep the default questions.)
6. Add injected corrections, after Siya's decision (task S2).
7. Run a quick check of Muse Spark Open as a test-user model. Then rotate three test-user models across the three repeats.
8. Merge the belief engine into `main`, after Preyansh's review (task P1). (Done Nov 12: the engine is on `main`.)

### Waiting to-dos (decided Nov 13, after the full run starts)

These two generative AI parts are agreed but wait until the main work is done. Both get a dated entry in `ablations.md` before their results are reported.

- **The AI model writes each question.** The belief engine still chooses what to ask. The AI model words the question from the conversation so far, so the interview feels like a conversation. We compare it with D (bank wording) on the same users. We also check if the written questions hint at an answer, which the "acquiescence" noise would then show.
- **Embedding retrieval.** Replace the keyword search in `retrieval.py` with an embedding model (a model that turns text into numbers that capture its meaning). Test it on the 290 labeled pilot answers, with no new interviews. This needs a model download (a few hundred MB).

### Phase 2: Nov 13 to Nov 14

9. Run the full experiment: 100 test users, the methods in Preyansh's ablation plan, budgets 5, 10 and 15, three repeats. Estimated cost: $70 to $100.
10. Give Siya 20 conversations for persona check 6. (Done Nov 11: `persona_checks/human_read/`.)

### Phase 3: Nov 14 to Nov 17

11. Score the results and make the charts.
12. Write the Milestone 3 sections on results, cost and speed, and failure analysis.

## 6. Work for Preyansh

### P1. Review the belief engine (Thu Nov 12, first priority) — DONE

**Done Nov 12.** Preyansh approved the engine with six changes. Somaditya made all of them. The engine is on `main` since Nov 12. Details: `BELIEF_ENGINE.md`, section "Changes after Preyansh's review". The evidence values in use now:

| Evidence | Form answer | Spoken answer (method D) |
|---|---|---|
| Stated feeling (willingness) | 0.15 | 0.15 |
| Imagined situation (behavior) | 0.15 | 0.15 |
| Past action (behavior) | 0.20 | 0.20 |
| Chance that an answer is off | 0.10 | 0.10 |

A smaller number means stronger evidence. The form values are fitted on the pilot users. The spoken values are the starting values. They are the same for the experiment, the live chat and the classmate study. The fitted spoken values (0.075 to 0.125) come from AI test users that are too consistent, so we do not use them. Past actions are the weakest evidence for our test users, not the strongest.

The steps below were the review steps.

The full run cannot start before this review.

1. Open the changes: https://github.com/somadisingh/2sigm0id/compare/main...belief-engine
2. Read `BELIEF_ENGINE.md` first. Then read `belief.py`.
3. Run the tests (no API key is necessary):
   ```bash
   git fetch origin
   git switch belief-engine
   python test_belief.py
   ```
4. Answer these questions in a message to Somaditya:
   - Are the evidence strengths sensible? (`SIGMA` in `belief.py`: past action 0.15, stated feeling 0.20, imagined situation 0.25. A smaller number means stronger evidence.)
   - Is the stop rule sensible? (Stop when fewer than 5% of simulated futures change the band.)
   - Is the AI model's reading step correct? (`EXTRACT_SYSTEM` in `methods.py`.)
   - Is it correct that method D can ask about the same fact up to 3 times? (`MAX_ASKS_PER_FACT`.)
   - Do you agree that the old D (now called D0) stays in the experiment, to show what the engine adds?
5. Write "approved" or give a list of changes.

**Done when:** Somaditya has your approval or your list of changes.
**You need:** nothing from others.

### P2. Write the ablation plan (Fri Nov 13)

An ablation is a test that removes or changes one part of the system to measure its effect. We must write the plan before the full run, so that we cannot choose the tests after we see the results.

1. Create the file `ablations.md` in the repo.
2. For each test, write: the question, the two methods to compare, the measure, and your prediction. Use these tests as a start:
   - New D against old D0: what the belief engine adds.
   - D against C: what conversation adds when both use the same engine.
   - D with and without the repeat questions about a fact: what the clarifying questions add.
   - D against DR (with retrieval) and DP (with token probabilities): what each generative AI part adds.
   - The profile at the stop point against the profile at the end of the budget, for C and for D: how much accuracy the stop rule loses.
   - Capacity from the formula against the old D0's own capacity estimate.
3. Send the file to Somaditya. He sets the full run from it.

**Done when:** `ablations.md` is on `main`.
**You need:** P1 done.

### P3. Build the live chat for real people (Sat Nov 14)

Siya needs this for the classmate study. We also need it for the final demo.

1. Make a simple program in which a real person types answers to method D's questions. A text window in the terminal is sufficient.
2. Use the same steps as method D in `run_form` in `methods.py`. Replace the call to the AI test user with the person's typed answer.
3. At the end, show the three scores, the final band and the band probabilities. Do not give investment advice.
4. Save each conversation to a file. The classmate study uses these files.
5. Test it with Somaditya before Nov 14.

How to use the engine (all on `main`; method D's loop in `run_form` in `methods.py` shows every step):

- `belief.Belief(channel="spoken")` holds the person's profile.
- `methods.engine_pool(methods.load_bank())` gives the questions. Before each question, `belief.choose(candidates, questions_left, seed=k)` returns the question to ask and its stop information.
- Ask `item["spoken"]`. To ask a fact again, `methods.clarify(...)` words the question.
- Read the typed answer with `methods.extract(llm, "glm-5.3", "low", question, item, answer)`. Then call `methods.apply_evidence(belief, evidence, k)`, which returns contradiction flags, and `methods.update_unclear(...)`.
- At the end: `belief.profile()` gives the three scores, and `belief.final_pmf(belief.band_pmfs())` gives the band probabilities.
- The spoken settings in use are the starting values you asked for. You do not need to change them.
- For the standard form (method A), use `methods.short_form(bank, budget)` and `belief.observe_option(item, option_number)` with a `belief.Belief()` (form channel).

**Done when:** Siya can run it with a classmate.
**You need:** P1 done (the engine is on `main`). You need an API key for the AI model. Ask Somaditya. Never put the key in the repo.

### P2b. Update `ablations.md` after the review (when you can, before the full run)

Your plan rule says to record changes in the "Changes" section. Three tests were written before the review changes:

- Test 5 predicts that D's stop rule stops too early because it uses the weaker form model. D now uses its own spoken model.
- Test 7 assumes that the fitted spoken values are in use. They are not: D uses the starting values (0.15, 0.15, 0.20). The test now compares fitted and starting values for the form answers only.
- Test 8 is not needed: `N_ROLLOUTS` is 400.

Method DN (D without re-asks) for test 3 is on `main`.

### P4. Write the Milestone 3 system section (Tue Nov 17)

1. Describe the system: the belief engine, the role of the AI model, and method D's steps.
2. Explain the professor's example (section 3) with the real numbers from `test_belief.py`.
3. Include the table of AI model roles from `BELIEF_ENGINE.md`.

**You need:** results from Somaditya by Nov 16 for any numbers.

**Not in scope:** the portfolio part and the market data check. Do no work on them before Milestone 3.

## 7. Work for Siya

### S1. Set up the backstories with Somaditya (Thu Nov 12) — DONE

**Done Nov 13. Somaditya made the decision. The backstories are on (`USE_BACKSTORIES = True` in `config.py`).** Reason: a person's money situation (debt, dependents, job) shapes how they invest, and the backstories make the test users sound like real people.

What changed in `mirofish/personas_100_with_backstories.json` (Siya, please read):
- **The risk sentences in all 100 backstories are rewritten.** The old stories used a few fixed sentences for each band. For example, "gets out fast and loses sleep" was in almost every behavior-band-1 story, "sees a bargain and adds more" was in 17 band-5 stories, and "wants maximum growth and insists losses don't scare" was in 23 stories. The users sounded alike, and a fixed sentence for each band is a clue that the extractor can learn. `rewrite_backstories.py` asked GLM 5.3 to rewrite only the parts about risk, market drops, past losses and investing knowledge. Each user got a different concrete habit (for example, "moved everything to a savings account", "checks the app all day and sells when it turns red", "raises the monthly contribution when prices fall"). Mismatch users got a short reason (for example, coworkers who talk big, or "at my age, I would rather keep what I have"). Users with no past loss say only what they *would* do.
- **The old story of each user is kept** in `profile.backstory_v1`. The true scores did not change.
- **U042 has a new mismatch label:** "says moderate, would panic-sell" (was "says aggressive, would panic-sell"). Her willingness is 0.52 (band 3), and her story says she is in the middle. The scores are still 2 bands apart, so she is still a mismatch user.

Checks (`persona_checks/backstory_rewrite.md`, `persona_checks/check1_facts.md`):

| | old stories | new stories |
|---|---|---|
| Persona check 1: users with all six facts right (backstories on) | 88 of 100 | 92 of 100 |
| A blind reader (GLM 5.3) finds the behavior band exactly | 61 of 100 | 72 of 100 |
| ... finds the willingness band within 1 | 100 of 100 | 100 of 100 |
| 5-word phrases that are in 5 or more stories | 414 | 295 |
| Stories with "sleep" / "panic" | 12 / 14 | 0 / 0 |

With backstories off, persona check 1 was 89 of 100. The first rewrite made users with no past loss say "held" (81 of 100), because their stories told of small past dips. The second rewrite fixed this.

Still open: the test-user instructions in `prompts.py` (`BEHAVIORAL_TEXT`) still say "you panic … and lose sleep over it" for behavior band 1. These instructions win over the backstory. Somaditya decides before the full run if this sentence changes.

The original steps:

1. Meet with Somaditya (call or chat).
2. Decide where the backstory goes in the test-user instructions. The proposal: after the money facts, with the rule "If the backstory and the facts disagree, the facts are correct".
3. Somaditya makes the change. You check the result on 5 users.

**Done when:** the test users use the backstories, and you agree with the wording.
**You need:** nothing from others.

### S2. Decide the injected corrections (Thu Nov 12) — DONE

**Done Nov 13.** Siya chose a `correction_rate` in each user's noise block: 0 for clean, 0.05 for moderate and 0.10 for heavy users. Somaditya built it: the test user gives a wrong value the first time a fact comes up and corrects it on the next turn. The scorer reports "correction accepted" next to "contradiction caught". In a check on 20 users, the test users made the planned mistake and then corrected it clearly ("Oh wait, I messed up earlier…").

Now every injected contradiction is a false statement. A real person also corrects earlier mistakes. In an "injected correction", the test user first gives a wrong value and later gives the true value.

1. Decide what share of the questions get a correction for each noise level (clean, moderate, heavy). A proposal: 0%, 5% and 10%.
2. Decide if the rate goes into the `noise` block of each test user, or into one global setting.
3. Send your decision to Somaditya.

**Done when:** Somaditya has your decision.
**You need:** nothing from others.

### S3. Build persona checks 2, 3 and 5 (Fri Nov 13 to Sun Nov 15)

Do these checks after S1, because the backstories change how the test users answer.

How to build them:
- `prompts.build_user_system(persona)` gives the instructions for one test user.
- `run_bakeoff.make_llm(False)` gives the connection to the AI models.
- `llm.chat(model, messages, "off", 1500, 0.9)` sends a conversation and returns the answer in `["text"]`.
- `prompts.PROBES` shows how the existing fact checks ask questions.
- Write your code in a new file, for example `mirofish/persona_checks.py`. Save the result tables in `mirofish/`.
- To test without cost, use `make_llm(True)`. It gives random fake answers.

**Check 2: profile check questions.** For each test user:
1. Ask 4 new questions about willingness and 4 about behavior. Use questions that are NOT in `question_bank.json`.
2. Ask the questions with no noise.
3. Score each answer from 0 to 1 with a fixed rule or a fixed option list.
4. Check that the average score is in the same band as the true score, or one band away.
5. Report the result separately for the users of type "says aggressive, would panic-sell". These users must answer the *willingness* questions boldly and the *behavior* questions with fear. Section 4 tells why.

**Check 3: repeat.** Ask the same test user the same 8 questions in two separate conversations. Report how often the two answers give the same option.

**Check 5: three models agree.** Ask the 8 questions to each test user with three models: `deepseek-v4-flash-0731`, `nemotron-3.5-super` and `muse-spark-open`. Report how often the three models give the same band. Muse costs about 15 times more per word, so first run it on 10 users.

**Done when:** you have one table with the result of each check and the share of users that fail it. Mark each user that fails 2 or more checks. We then fix or remove those users.
**You need:** S1 done. An API key (ask Somaditya). Estimated cost: $2 to $3.

**Also look at these results from checks 1 and 4 (section 3):** 16 users with the income "stable and high" say "stable", and "flip" notes rarely change form answers. Decide with Somaditya if the income label and the flip note need new wording.

### S4. Run persona check 6: people read conversations (by Mon Nov 16)

The 20 conversations are ready (Nov 11). They are real runs of method D with 20 of the 100 test users, 4 for each true final band. We removed the true profiles.

1. Open the reading sheet: https://github.com/somadisingh/2sigm0id/blob/main/persona_checks/human_read/conversations.md
2. Read the instructions at the top of the sheet. Reading all 20 takes about 45 to 60 minutes.
3. Copy `persona_checks/human_read/guesses.csv` into a shared Google Sheet. Give Preyansh and Somaditya edit access.
4. Each of the three readers writes a final band (1 to 5) for each conversation in their own column. Work alone. Do not talk about the guesses before all three finish.
5. Nobody opens `persona_checks/human_read/key_DO_NOT_OPEN.json`.
6. When all three columns are full, download the sheet as `guesses.csv` and put it back in `persona_checks/human_read/`.
7. Run `python check_personas.py human-read score`. It writes `persona_checks/check6_human_read.md`: how often each reader and method D got the band right, and how often the readers agreed.

**You need:** nothing from others.

### S5. Run the classmate study (Sat Nov 14 to Mon Nov 16)

1. Find 10 to 15 classmates.
2. Each classmate does two things: the fixed form (method A) and the live chat (method D). Half of the classmates start with A. The other half start with D.
3. After both, each classmate does a short lottery-choice task. Then they answer: "Does this band feel correct? (1 to 5)".
4. Collect the answers in your Google Form.
5. Report: how often A and D agree, and how each one matches the lottery task and the 1-to-5 answer.

**Done when:** the results table is ready.
**You need:** the live chat from Preyansh (P3, Nov 14). The fixed form can be your Google Form with the questions from `question_bank.md`.

### S6. Make the style-swap test users (Sun Nov 15)

1. Choose 20 test users.
2. Make a copy of each user. Change only the `style` block (for example, short and plain becomes long and technical). Keep the true profile the same.
3. Save them in `mirofish/personas_style_swap.json` with new IDs.
4. Send the file to Somaditya. He runs them with method D.

This test shows if the way a person talks changes their result.

**You need:** nothing from others.

### S7. Write the Milestone 3 test-user section (Tue Nov 17)

1. Describe how the test users were made and checked.
2. Include the persona check table, the classmate study and the style-swap result.

## 8. Work for all three

1. If the reply email to Professor Gashami is not sent yet, give Somaditya your OK today. The email can now point to the belief engine.

### L1. Label 50 readings by hand (Preyansh and Siya, each person alone, by Fri Nov 13, about 20 minutes)

**Done (Preyansh Nov 12, Siya Nov 13).** Siya and Preyansh agree with each other on 78% of the readings. On the readings where they both agree, the judge model (with thinking) gives the same answer in 37 of 38 cases. So we can trust the judge on clear cases.

A judge model checks if the AI model reads answers correctly. We must know if we can trust this judge. So we compare the judge with people. Each of you labels the same 50 readings without help, so that we can also see how often two people agree.

1. Open the file: https://github.com/somadisingh/2sigm0id/blob/main/pilot/label_readings.csv
2. Download it, or copy it into a Google Sheet.
3. For each row, read the question, the answer and the reading.
4. In your column, write "yes" if the answer supports the reading. Write "no" if it does not.
   - A number range is supported if the answer gives a value in the range, or words that clearly mean such a value.
   - A score is supported if the answer says something about that topic. The score must also be near the point on the scale that fits the answer (about 0.2 or less). The reading text shows the points of the scale.
5. If you are not sure, write your best answer and add a note in the "notes" column.
6. Do not open `pilot/label_readings_key.jsonl`. It contains the judge's answers.
7. Do not talk about the labels with the other person before you both finish.
8. Send your file to Somaditya.
2. Send your Milestone 3 draft sections by Tue Nov 17. Somaditya combines them.
3. Do not change files that another person owns without asking. Do not commit the `.env` file or any API key.

## 9. Who waits for whom

| Who waits | For what | From | Needed by |
|---|---|---|---|
| Somaditya: merge the engine, start the full run | Engine review (P1) | Preyansh | done (Nov 12) |
| Somaditya: add corrections | Corrections decision (S2) | Siya | done (Nov 13) |
| Siya: persona checks 2, 3, 5 | Backstories set up (S1) | Siya and Somaditya | done (Nov 13) |
| Somaditya: final list of methods for the full run | Ablation plan (P2) | Preyansh | Nov 13 |
| Somaditya: report the faithfulness test | 50 hand labels (L1) | Preyansh and Siya | Nov 13 |
| Siya: classmate study | Live chat (P3) | Preyansh | Nov 14 |
| Siya: persona check 6 | 20 conversations | Somaditya | done (Nov 11) |
| Everyone: Milestone 3 numbers | Full-run results | Somaditya | Nov 16 |

## 10. Words we use

| Word | Meaning |
|---|---|
| Test user | An AI model that plays a person with a known true profile |
| Pilot user | A test user that we use only to tune the system. We never score it. |
| Question budget | The number of questions that a method can ask: 5, 10 or 15 |
| Band | A score group from 1 (very careful) to 5 (very bold) |
| Belief engine | The code in `belief.py` that keeps the score ranges, chooses questions and finds the stop point |
| Evidence | The information from one answer, for example "horizon: 6 to 8 years" or "willingness: 0.7" |
| Extractor | The AI model step that turns a spoken answer into evidence |
| Clarifying question | A question that asks again about a fact when two answers do not agree |
| Stop point | The question after which more questions are unlikely to change the band |
| Noise | Planned bad answers from a test user: vague, flipped, contradicting or agreeing too easily |
| Correction | Planned noise in which the test user first gives a wrong value and later gives the true value |
| C0, D0 | The old versions of C and D, before the belief engine. We keep them for comparison. |
| DR, DP | Method D with retrieval (DR) or with token probabilities (DP) |
| Ablation | A test that removes or changes one part to measure its effect |
| Run-to-run noise | Results change a little each time we run the same test. It is about 0.03 in average error, so smaller differences do not show which method is better. |

## 11. How to run the code

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python test_belief.py                       # engine tests, no key needed
python run_bakeoff.py experiment --mock --methods A B C D --budgets 5 --repeats 1   # fake answers, no cost
python score.py results/experiment_mock.jsonl
```

For real AI calls, you need the Baseten API key in a file named `.env` (see `.env.example`). Ask Somaditya. Never commit this file.

`README.md` tells how to run each part. `BELIEF_ENGINE.md` explains the engine and its sources.
