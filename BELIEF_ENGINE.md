# Belief engine

The belief engine (`belief.py`) answers the professor's first Milestone 2 question: how the system chooses the next question, how it measures uncertainty, and how it decides that another question is unlikely to change the final band.

Code holds the beliefs, chooses each question and decides when to stop. The LLM does only language work: it turns spoken answers into evidence and writes clarifying questions. Methods C and D share the engine, and methods A and B use it to score their answers. So all methods turn answers into a profile with one rule.

## How it works

1. **Beliefs.** Willingness and behavior are each a probability distribution over the 0–1 scale. A wide distribution means the engine is unsure. Every method starts from the same flat prior.
2. **Capacity.** Each money fact (horizon, emergency savings, income, debt, dependents) has its own distribution. The engine draws 2,000 samples of the five facts and runs the capacity formula (`capacity.py`) on each sample. Facts that nobody asked about stay uncertain, so capacity stays uncertain too.
3. **Evidence strength.** Each answer narrows one distribution. A past action is the strongest evidence, a stated feeling is weaker, and an answer about an imagined situation is the weakest. A vague answer counts half as much. A fixed lapse rate (10%) means that one answer can never rule a value out completely.
4. **Final band.** The engine combines the three distributions with the lowest-of-three rule. The result is a probability for each band, for example "band 2: 70%, band 1: 25%".
5. **Next question.** For each candidate question, the engine simulates the possible answers and calculates how much each answer would reduce the uncertainty about the final band (expected information gain). It asks the question with the highest gain.
6. **Stop rule.** Before each question, the engine simulates 100 possible futures. Each future draws a "true" person from the current belief, simulates the remaining questions and checks the final band. If the band changes in fewer than 5% of the futures, the band is settled. This rule is called stochastic curtailment. In the main experiment the engine keeps asking: it logs the stop point as `would_stop_at` and then asks the questions that most reduce the error on each score.
7. **Contradictions.** Two statements of a fact that disagree leave both values possible, so the distribution for that fact becomes wide. If the fact can change the band, a clarifying question then has the highest gain, so method D asks it. A statement is flagged as a contradiction only when it disagrees with most of the earlier clear statements of the same fact.
8. **Mismatch.** The engine flags a mismatch when the estimated scores are 2 or more bands apart and the chance of a mismatch is at least 60%.

## The professor's example

The person says that they like risk (willingness about 0.8). Their behavior answers are near the band 1/2 edge, and their capacity is high. Behavior decides the band. The engine asks the past-behavior question (BEH02) next. Its expected gain is 0.29 bits. Another willingness question has a gain of 0.00, because it cannot change the band. `test_belief.py` checks this case.

## LLM roles in method D

| Step | Done by | Calls |
|---|---|---|
| Choose the question, track beliefs, stop, flag | code (`belief.py`) | 0 |
| Word a new question | bank wording (`spoken`) | 0 |
| Turn the answer into evidence (fact ranges, scores, past or imagined, clear or vague) | LLM extractor | 1 per answer |
| Word a clarifying question when the engine re-asks a fact | LLM writer | 1 per re-ask |

## Methods

| Method | Chooses questions | Reads answers |
|---|---|---|
| A fixed form | fixed order | option number |
| B scripted interview | fixed order | LLM maps speech to an option |
| C adaptive form | belief engine | option number |
| D adaptive interviewer | belief engine, may re-ask facts | LLM extracts evidence from speech |
| C0 (earlier C) | hand-made rule | option number |
| D0 (earlier D) | the LLM, prompt v1 | the LLM |

A, B, C and D form the 2×2 design. C and D differ only in conversation. D0 against D shows what the engine adds over prompting alone.

## First check (Nov 11, 5 test users, budget 10, one run each)

| | avg error | band within 1 | system $ / profile | wait per turn |
|---|---|---|---|---|
| C, engine | 0.129 | 100% | $0 | 0 s |
| D, engine, run 1 | 0.174 | 100% | $0.011 | 2.1 s |
| D, engine, run 2 (contradiction flag fix) | 0.114 | 100% | $0.011 | 1.8 s |
| D0, LLM only (Nov 6 run) | 0.107 | 100% | $0.029 | 9.2 s |

These are 5 runs each. The two D runs differ by 0.06, so these numbers don't rank the methods. Run 2 raised 2 contradiction flags, against 8 in run 1, and still caught 2 of the 3 injected contradictions. Engine D costs 62% less than D0 and is 4 times faster per turn. One finding: for P3 ("talks big, panics"), the simulated user answered the willingness questions with panic, and engine D's extractor scored the answers as given (willingness error −0.60). C's forced-choice form kept the two scores apart.

## Values to fit

`SIGMA` (evidence strength by type), `LAPSE`, `STOP_CHANCE` and the flat priors are starting values. Fit them on the 10 pilot users (`mirofish/personas_pilot.json`), never on the 100 test users. Report how much the results change when they change.

## Limits

- The engine treats the three dimensions as independent. Willingness and behavior may be related.
- The answer model for bank options is a simple noisy-option model, not a calibrated item response model. We have no human response data to calibrate one. Choi and Swartz (2009) found that simple selection criteria work as well as complex ones for this type of item.
- The stop rule simulates the remaining questions as a fixed list (the current top items), not as a new adaptive choice at each step.

## Sources

- Stochastic curtailment: Finkelman (2008); Wouda and Eggen (2009), [Cito report](https://cito.nl/media/cf3jcirb/2009-computerized-classification-testing-in-more-than-two-categories-using-stochastic-curtailment.pdf).
- One-step value of information can stop too early: Heckerman, Horvitz and Middleton, [arXiv 1303.5720](https://arxiv.org/pdf/1303.5720).
- Information gain for adaptive elicitation of risk preferences: DOSE, Chapman et al., [NBER w25072](https://nber.org/system/files/working_papers/w25072/w25072.pdf); Toubia et al. (2013), [Management Science](https://econpapers.repec.org/RePEc:inm:ormnsc:v:59:y:2013:i:3:p:613-640); adaptive design optimization, Cavagnaro et al., [NeurIPS 2009](https://proceedings.neurips.cc/paper_files/paper/2009/file/6cd67d9b6f0150c77bda2eda01ae484c-Paper.pdf).
- LLM for language and a Bayesian model for choices: OPEN, Handa et al., [arXiv 2403.05534](https://arxiv.org/abs/2403.05534); BED-LLM, Choudhury et al., [arXiv 2508.21184](https://arxiv.org/abs/2508.21184).
- LLMs update beliefs poorly over many turns: Qiu et al., [arXiv 2503.17523](https://arxiv.org/abs/2503.17523).
- Item selection criteria for polytomous items: Choi and Swartz (2009), [PMC2791416](https://pmc.ncbi.nlm.nih.gov/articles/PMC2791416).
- Aberrant answers distort adaptive tests: [Zhang et al. (2022)](https://frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.841372/pdf).
