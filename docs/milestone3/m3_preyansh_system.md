# System implemented so far (Preyansh, Nov 18, 2026; updated Nov 22 for the final report)

Written for Milestone 3 and updated on Nov 22 for the two engine changes in `belief.py` (tests 9 and 10 in `ablations.md`). Sources: `BELIEF_ENGINE.md`, `p4_numbers.md`, `ablations.md`, `test_belief.py` (`test_professors_example`, `test_stop_rule`, `test_conflicting_fact_needs_a_majority`, `test_stop_needs_confidence`), `live_session.py`. Full-run numbers leave out U054, as in the other sections.

## System implemented so far

**Code decides, the AI model reads.** In Milestone 2 an AI model ran the whole interview (now method D0). AI models track evidence poorly over many turns, and the professor asked for more than prompt chaining. So in the new design, code holds the beliefs, chooses each question and decides when to stop. The AI model does only language work.

**The belief engine** (`belief.py`) keeps a probability distribution for willingness and for behavior on a 0 to 1 scale. For capacity it keeps one distribution per money fact, and it runs the capacity formula on 2,000 samples of the facts. So a fact that nobody asked about keeps capacity uncertain. Each answer narrows one distribution. A vague answer counts half, and a 10% lapse rate means that no single answer rules a value out. The three scores give a probability for each final band (lowest-of-three rule). Before each question, the engine:

1. asks the candidate question with the highest expected information about the final band (about 0.1 s, no AI call);
2. simulates 400 futures for the rest of the budget. The band is settled when it changes in fewer than 5% of them *and* the engine gives its most likely band at least 80% (`STOP_CONFIDENCE`, added Nov 22). In the experiment it records this stop point and keeps asking, so that all methods ask the same number of questions.

The 80% floor fixes a failure from the full run. With the 5% test alone, the engine was too sure of itself, and the band changed after the stop in 7% to 14% of runs. In 2,700 new interviews with the floor, it changed in 0% to 4.3% (C and D, every budget), and the stop still saves 1.0 to 3.9 questions per run at 10 and 15 questions.

When two clear statements of a money fact disagree, the fact counts as unknown until most statements agree (`CONFLICT_RULE = "majority"`, added Nov 22): one statement against one counts neither, and a third decides. The disputed fact keeps capacity uncertain, so a re-ask of it gets a high value. In new interviews this rule gave no clear gain (D's capacity error −0.001 at 10 and 15 questions). All methods score answers with this one engine. C and D also use it to choose questions.

**Method D, the adaptive interviewer.** The engine picks a question, and D asks it in the bank's spoken wording. The AI model (GLM 5.3) reads the free-text answer and returns evidence: fact values, scores on a fixed 0.1 to 0.9 scale, past action or imagined situation, and clear or vague. When the engine re-asks a fact (up to 3 times), the AI model words a neutral clarifying question.

| Step | Done by | AI calls |
|---|---|---|
| Choose the question, track beliefs, stop, flag a mismatch | code (`belief.py`) | 0 |
| Word a new question | question bank | 0 |
| Turn the answer into evidence | AI model (extractor) | 1 per answer |
| Word a clarifying question for a re-ask | AI model (writer) | 1 per re-ask |

At 10 questions, D makes 11.5 AI calls and costs $0.0126 per profile (list price), with a 1.24 s wait per turn. D0 costs $0.0272, with a 1.75 s wait. Three generative AI parts each have their own test:

- **Retrieval (DR):** the extractor sees the 3 most similar labeled pilot answers.
- **Token probabilities (DP):** we read the model's own probability for each option and calibrate it with a temperature.
- **Faithfulness test:** a judge model checks each reading against the answer. It agreed with our hand labels on 37 of 38 readings where both labelers agreed.

The settings for form evidence are fitted on 10 pilot users, never on the test users. Spoken evidence uses the starting settings.

**Live chat.** `live_session.py` and `web_app.py` run the same method D for real people. The web app is hosted with an access code for the classmate study. Each person does A and D, in an order set by their participant ID. Answers are saved privately under the ID only.

## The professor's example, with real numbers

The professor asked how the system picks the next question, and how it knows that another question will not change the band. The example is a person who says that they like risk but acts scared. `test_belief.py` builds this person:

- **Capacity:** high (25-year horizon, 12 months of savings, very stable income, no debt, no dependents).
- **Willingness answers:** "a friend would describe me as..." option 4 (0.75), and "I'm fine with some losing years" strongly agree (1.0).
- **Behavior answers:** moves some money to cash when a crash is in the news (0.33), and sells when friends sell (0.0).

What the engine does with 6 questions left:

| Engine settings | Next question | Expected information | Best willingness question | Most likely band | Mismatch chance |
|---|---|---|---|---|---|
| Starting | BEH02: last time your investments fell, what did you do? | 0.289 | 0.000 | 1 (51%) | 97% |
| Fitted (used in the run) | BEH01: your investments drop 20% in a month | 0.189 | 0.000 | 1 (56%) | 99% |

Behavior sets the band, because the band is the lowest of the three. So another willingness question is worth exactly zero, and the engine asks about behavior and flags the mismatch. With the starting settings it asks about a past action, as in the professor's example. With the fitted settings it asks a scenario question, because the pilot fit showed that past-loss stories are weaker evidence than we assumed. The stop rule, followed for the same person (fitted settings, the person gives the most scared answer each time):

| Point in the interview | Most likely band | Change chance | Stops? |
|---|---|---|---|
| Before BEH01 | 1 (56%) | 0.43 | No |
| After BEH01 ("sell everything") | 1 (81%) | 0.16 | No: change chance over 5% |
| After BEH03 ("check several times a day") | 1 (92%) | 0.03 | Yes |

So the engine asks two behavior questions and stops with 4 of its 6 questions unused. For comparison, a new user with nothing known has a change chance of 0.53.
