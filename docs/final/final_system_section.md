# Final report: system (draft, Preyansh, Nov 25, 2026)

Task P6 in `plan.md`. Numbers come from `ablations.md` (tests 9 to 16 and the CWF stop-rule replay) and `final_conclusions.md` (A1 to A6). Results are from synthetic test users only; the classmate study tested A and D, not CWF.

## System

**What it does.** A beginner investor answers 5 to 15 questions. The system estimates three risk scores from 0 to 1: capacity (how much loss they can afford, from five money facts), willingness (the risk they say they like) and behavior (what they do in a loss). Each score has a band from 1 to 5, and the final band is the lowest of the three.

**Who does what.** Code keeps the evidence and makes every decision. The AI model only reads and writes language. In Milestone 2 one AI model ran the whole interview (method D0). It lost track of evidence over many turns, and its error grew with each extra question (0.128 at 5 questions, 0.161 at 15). The design where code keeps the evidence (D) is clearly better than D0 at 10 and 15 questions, for about half the cost.

### The method we present: CWF (money facts first, then conversation)

One interview of 10 questions runs like this:

1. **Money facts, on a form.** The first min(5, budget // 2) questions are money-fact questions (time until the money is needed, emergency savings, income stability, debt payments, dependents). The person picks one option for each. The engine picks which fact to ask and in what order. A form question is never asked again.
2. **Willingness and behavior, in conversation.** The engine picks each remaining question from the bank. The AI writes it naturally from the conversation so far (the form questions are not shown to it), and the person answers in their own words.
3. **Reading each answer.** The AI extractor turns the answer into evidence: a score, whether it describes a past action, an imagined situation or a stated feeling, and whether it is clear or vague. Money facts that it hears in conversation are dropped, because they come only from the form.
4. **Re-asks.** If an answer is vague or contradicts an earlier one, the engine can ask about it again, and the AI words a neutral clarifying question.
5. **Result.** The three scores, the final band and how sure the engine is, with any contradiction or mismatch it noticed. It is a risk profile for a study, not investment advice.

**Why the money facts are on the form.** Money facts said in conversation can be false, and a person (or a test user) may repeat a wrong value. With everything else the same, hearing the facts in conversation instead of on a form costs 0.018 more capacity error at 10 questions and 0.031 at 15 (CW − DW, clear). Asking the facts first also matters: the adaptive form C asks only 1.65, 3.24 and 4.12 fact questions at 5, 10 and 15, and all of CWF's gain over C is in capacity.

### The belief engine (`belief.py`, plain code)

- It keeps a probability distribution for willingness, behavior and each money fact. Capacity is the capacity formula run on 2,000 samples of the facts, so a fact nobody asked about keeps capacity uncertain.
- Before each question it picks the bank question with the most expected information about the final band (about 0.1 s, no AI call).
- **Conflicting facts need a majority.** When two clear statements of a fact disagree, the fact counts as unknown until most statements agree.
- **Stop rule.** It simulates 400 futures for the questions left. The band is settled when it changes in under 5% of them and the engine gives the reported band (the lowest of the three bands, as the person sees it) at least 80%. In the experiment it records this point and keeps asking, so every method asks the same number of questions. With this rule the band changes after the stop in 0 to 3% of runs for C and D. For CWF, a replay of its recorded answers gives 0.0%, 0.0% and 0.9% at 5, 10 and 15 questions.

### Generative AI parts

| Part | What it does | Evidence | Kept? |
|---|---|---|---|
| Extractor (GLM 5.3) | Turns each free answer into evidence | A judge model agrees with our hand labels on 37 of 38 clear readings | Kept |
| Clarifying-question writer | Words a neutral re-ask of a vague or conflicting fact | Re-asks lower capacity error by 0.030 at 10 questions and 0.040 at 15 (D − DN, clear) | Kept |
| Question writer, version 2 | Words each conversation question from the conversation so far | Version 1 restated an earlier answer in 12.4% of questions, which can lead the person. Version 2 forbids this: 0.0% restated, avg error within 0.01 of D, and 5.1 points more exact bands at 10 questions | Kept |
| Retrieval (DR) | Shows the extractor the 3 most similar labeled pilot answers | No accuracy gain, 25% more cost | Dropped |
| Token probabilities (DP) | Reads the model's own probability for each answer option | Clearly less accurate than D | Dropped |
| Embedding search | Replaces keyword search (BM25) in retrieval | Not better than BM25 at finding similar answers; no difference in extraction | Dropped |

### The controlled comparison

The Milestone 3 feedback noted that D − C mixes two effects: the AI interviewer, and harder input (only spoken methods hear false money facts). Three methods each change one thing:

| Comparison | What changes | Result (avg error unless stated) |
|---|---|---|
| CW − DW | Money facts on a form instead of in conversation | Capacity −0.018 at 10, −0.031 at 15 (clear) |
| CF − C | Money facts asked first, everything on the form, no AI | −0.012 at 5, −0.018 at 10 (clear); −0.003 at 15 (not clear) |
| CWF − CF | Only how willingness and behavior are asked: conversation or form | −0.005, −0.003, −0.004 (not clear at any budget) |

So most of CWF's gain over C comes from asking the money facts first, a rule a form can also use (CF). With the same input and question rule, conversation ties the form overall. It reads attitudes better for clean answerers (−0.020 at 10 questions, −0.021 at 15, clear), and it can notice contradictions, which a form cannot. One result goes the other way: at 10 questions CWF picks the exact band 7.4 points less often than CF (clear).

### Cost and time

| Method | System cost per interview (list price) | System time per question |
|---|---|---|
| CWF (presented) | $0.011 | 1.1 s |
| CF (no AI alternative) | $0 | 0.1 s |
| D (AI interviewer, classmate study) | $0.013 | 1.4 s |

The test users' own AI calls are not counted. CWF is cheaper than D because its form questions make no AI calls.

### Live app

`web_app.py` runs the classmate study (A and D, order set by the participant code) and a CWF demo (`?demo=CWF`). Answers are saved after every turn, under the participant code only, to a private repository.
