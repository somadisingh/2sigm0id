"""The methods for the main experiment.

  A   fixed form          the default short form from question_bank.json, in order
  B   scripted interview  the same questions in their 'spoken' wording; the person answers
                          in their own words and a mapper model picks the matching option
  C   adaptive form       the belief engine (belief.py) picks each next question from the bank
  D   adaptive interviewer  the belief engine picks each question and may re-ask a fact to
                          clarify it; the person answers in their own words; an LLM turns each
                          answer into evidence and words the clarifying questions
  DR  D, with retrieval: the extractor also sees similar labeled pilot answers (retrieval.py)
  DP  D, reading answers with token probabilities: GLM picks the matching option, and its
      calibrated probability for every option is the evidence (soft evidence)
  C0  the earlier adaptive form: a hand-made rule picks the questions
  D0  the earlier adaptive interviewer: the LLM does everything (run_interview in run_bakeoff.py)

A, B, C, C0 and D all turn answers into a profile with the belief engine, so they differ
only in how they choose questions and how they read answers. Every method uses the same
simulated user, the same noise schedule and the same budget.
"""

import json
import math
import random
import re
import time
import zlib
from pathlib import Path

import belief as BE
import config as C
import prompts as P
from capacity import INCOME_SCORE
from llm import extract_json, strip_think

HERE = Path(__file__).resolve().parent
DIMS = ("capacity", "willingness", "behavioral")
INT_RE = re.compile(r"\b(\d{1,2})\b")

FORM_PROMPT = ("Here is a question from a sign-up form. Pick the answer that fits you best.\n\n"
               "{question}\n{options}\n\nReply with just the number of your answer.")
FORM_RETRY = "Please reply with just one number from 1 to {n}."
FORM_NOISE = {  # how persona noise shows up when ticking a box instead of talking
    "vague": "You're not sure about this one. Pick without thinking too hard; a middle answer is fine.",
    "flip": P.NOISE_NOTES["flip"],
}
MAPPER_SYSTEM = (
    "You turn a person's spoken answer into one option from a multiple-choice question. "
    "Pick the option that best matches what they said. If the answer doesn't give enough "
    "information to choose, use null. Reply with ONE JSON object and nothing else: "
    '{"option": <option number or null>}')
MAPPER_MESSAGE = "Question: {question}\nOptions:\n{options}\n\nTheir answer: \"{answer}\""

# Method D: the LLM only does language. It turns each answer into evidence for the belief
# engine, and words a clarifying question when the engine decides to re-ask a fact.
EXTRACT_SYSTEM = """You turn one answer from a risk-profile interview into evidence. \
Use only what the person said. Never guess.

Money facts. Include one only if the answer states or clearly implies it:
- horizon_yrs: years until they need most of this money
- emergency_fund_months: months of essential expenses their savings could cover
- income_stability: one of "unstable", "partly commission-based", "stable", "very stable", \
"stable and high"
- debt_to_income: share of monthly income that goes to debt payments, from 0 to 1
- dependents: number of people who depend on their income
Give each number as a range [low, high] that covers what they said: "about 5 years" -> [4, 6], \
"a few months" -> [2, 4], "no debt" -> [0, 0].

Scores from 0 to 1. Include one only if the answer shows it. Use these points of the scale:
- willingness: how bold or careful they SAY they are about risk: their stated attitude and \
how they describe themselves. Score what they claim, even if they also say that in practice \
they would act differently or cannot afford it. What they would actually do belongs under \
behavioral, and money limits belong under the facts. 0.1 = wants to avoid any loss, even with \
very low growth. 0.3 = accepts only small ups and downs. 0.5 = accepts moderate risk for \
moderate growth. 0.7 = accepts large swings for higher growth. 0.9 = wants the highest \
growth and accepts big losses.
- behavioral: what they DO, or would do, in a real loss. 0.1 = sells all or almost all. \
0.3 = sells a large part. 0.5 = sells a small part and keeps the rest. 0.7 = keeps \
everything and waits. 0.9 = invests more. kind: "past" if it describes something that \
actually happened, "hypothetical" if it is what they think they would do.
If the question lists answer options with scores, use them as anchors.
past_loss: "none" if they say they have never had a big investment loss. Leave it out otherwise.

clear: false if the answer is vague, hedged or noncommittal on that point.

Reply with ONE JSON object and nothing else, leaving out anything the answer doesn't show:
{"facts": {"horizon_yrs": {"range": [low, high], "clear": true}, \
"income_stability": {"value": "stable", "clear": true}},
 "willingness": {"score": 0.6, "clear": true},
 "behavioral": {"score": 0.3, "kind": "past", "clear": true},
 "past_loss": "none"}"""
EXTRACT_MESSAGE = "{examples}Question: {question}\n{anchors}Their answer: \"{answer}\""
# Method DP: GLM picks the option that matches the answer; we read its token probabilities.
OPTION_SYSTEM = ("You read a person's spoken answer to a question and pick the multiple-choice "
                 "option that best matches what they said. Reply with just the option's letter.")
OPTION_MESSAGE = ("Question: {question}\nOptions:\n{options}\n\nTheir answer: \"{answer}\"\n\n"
                  "Which option best matches? Reply with just the letter.")
LETTERS = "ABCDEFGHIJKLMNOPQRST"
OPTION_FLOOR = 1e-4   # probability for an option outside the model's top 20 tokens
CALIBRATION_PATH = HERE / "pilot" / "calibration.json"
EXTRACT_RETRY = "That was not a valid reply. Reply with ONLY the JSON object."
CLARIFY_SYSTEM = (
    "You write one short follow-up question for a risk-profile interview. The person's earlier "
    "answers about one fact disagree, or were unclear. Ask, neutrally and in plain words, which "
    "is right, or for a clearer answer. Don't accuse them and don't give advice. Reply with ONE "
    'JSON object and nothing else: {"question": "<the question>"}')
CLARIFY_MESSAGE = "The fact: {fact}\nTheir earlier answers that mention it:\n{quotes}"
FACT_TEXT = {
    "horizon_yrs": "how many years until they need most of this money",
    "emergency_fund_months": "how many months of essential expenses their savings could cover",
    "income_stability": "how steady their income is",
    "debt_to_income": "what share of their income goes to debt payments",
    "dependents": "how many people depend on their income",
    "past_loss_reaction": "what they actually did the last time their investments fell a lot",
}
D_METHODS = ("D", "DR", "DP")
FORM_METHODS = ("A", "B", "C", "C0") + D_METHODS
_POOL, _TEMPERATURE = None, None
NO_EVIDENCE = {"facts": {}, "willingness": None, "behavioral": None, "no_past_loss": False}


def load_bank():
    return json.loads((HERE / "question_bank.json").read_text())


SHORT_FORMS_PATH = HERE / "pilot" / "short_forms.json"


def short_form(bank, budget, use_fitted=True):
    """The fixed form for methods A and B: the questions chosen on the pilot users
    (pilot/short_forms.json, from `python pilot.py fit`), else the top-priority items per
    dimension (short_form_allocation in the bank)."""
    if use_fitted and SHORT_FORMS_PATH.exists():
        ids = json.loads(SHORT_FORMS_PATH.read_text())[str(budget)]
        items = {i["id"]: i for i in bank["items"]}
        return [items[i] for i in ids]
    alloc = bank["short_form_allocation"][str(budget)]
    chosen = []
    for dim in DIMS:
        pool = sorted((i for i in bank["items"] if i["dimension"] == dim), key=lambda i: i["priority"])
        chosen += pool[:alloc[dim]]
    return chosen


def numbered(item):
    return "\n".join(f"{n}. {o['label']}" for n, o in enumerate(item["options"], 1))


def estimate(answers):
    """Dimension scores from answered items: the plain average (bank scoring rule)."""
    out = {}
    for dim in DIMS:
        vals = [a["score"] for a in answers if a["dimension"] == dim and a["score"] is not None]
        out[dim] = sum(vals) / len(vals) if vals else 0.5
    return out


def next_adaptive_item(bank, answers, asked_ids):
    """Method C's rule. No calibration data exists for item-response models, so C targets the
    dimension it is least sure about: few answers, answers that disagree, an estimate sitting
    near a band edge, or the dimension that currently decides the final band (the lowest).
    The first three questions cover one dimension each."""
    by_dim = {d: [a["score"] for a in answers if a["dimension"] == d and a["score"] is not None]
              for d in DIMS}
    unasked = {d: sorted((i for i in bank["items"] if i["dimension"] == d and i["id"] not in asked_ids),
                         key=lambda i: i["priority"]) for d in DIMS}
    if len(answers) < 3:
        dim = DIMS[len(answers)]
    else:
        est = {d: (sum(v) / len(v) if v else 0.5) for d, v in by_dim.items()}
        lowest = min(est, key=est.get)

        def uncertainty(d):
            v = by_dim[d]
            spread = (max(v) - min(v)) if len(v) > 1 else 0.5
            near_edge = min(abs(est[d] - e) for e in (0.2, 0.4, 0.6, 0.8)) < 0.05
            return (spread + 0.3) / math.sqrt(len(v) + 1) + 0.15 * (d == lowest) + 0.10 * near_edge

        dim = max((d for d in DIMS if unasked[d]), key=uncertainty)
    return unasked[dim][0] if unasked[dim] else next(i for d in DIMS for i in unasked[d])


def engine_pool(bank):
    """Bank items the belief engine can use: the five fact questions, willingness and
    behavior. CAP06-CAP11 ask about things the capacity formula doesn't use."""
    return [i for i in bank["items"] if BE.item_target(i) is not None]


def clean_evidence(obj):
    """Keep only well-formed evidence from the extractor's reply; None if unusable."""
    if not isinstance(obj, dict):
        return None
    ev = {"facts": {}, "willingness": None, "behavioral": None,
          "no_past_loss": str(obj.get("past_loss", "")).strip().lower() == "none"}
    facts = obj.get("facts") if isinstance(obj.get("facts"), dict) else {}
    for f, v in facts.items():
        if f not in BE.FACT_GRIDS or not isinstance(v, dict):
            continue
        clear = v.get("clear", True) is not False
        if f == "income_stability":
            s = INCOME_SCORE.get(str(v.get("value", "")).strip().lower())
            if s is not None:
                ev["facts"][f] = {"range": [s, s], "clear": clear}
            continue
        r = v.get("range")
        if isinstance(r, (list, tuple)) and len(r) == 2 and all(isinstance(x, (int, float)) for x in r):
            lo, hi = sorted(float(x) for x in r)
            if f == "debt_to_income" and hi > 1:   # given as a percent
                lo, hi = lo / 100, hi / 100
            ev["facts"][f] = {"range": [lo, hi], "clear": clear}
    for d in ("willingness", "behavioral"):
        v = obj.get(d)
        if isinstance(v, dict) and isinstance(v.get("score"), (int, float)):
            e = {"score": min(1.0, max(0.0, float(v["score"]))), "clear": v.get("clear", True) is not False}
            if d == "behavioral":
                e["kind"] = "past" if v.get("kind") == "past" else "hypothetical"
            ev[d] = e
    return ev


def pilot_pool():
    global _POOL
    if _POOL is None:
        import retrieval
        _POOL = retrieval.Pool.load()
    return _POOL


def temperature():
    """DP's calibration temperature, fitted on the pilot users (pilot.py calibrate)."""
    global _TEMPERATURE
    if _TEMPERATURE is None:
        _TEMPERATURE = (json.loads(CALIBRATION_PATH.read_text())["temperature"]
                        if CALIBRATION_PATH.exists() else 1.0)
    return _TEMPERATURE


def lettered(item):
    return "\n".join(f"{LETTERS[n]}. {o['label']}" for n, o in enumerate(item["options"]))


def option_probs(logprobs, n):
    """Probability of each of n options from the answer token's top alternatives. The answer
    is the last token whose top choice is an option letter (GLM may think first)."""
    valid = LETTERS[:n]
    for alts in reversed(logprobs or []):
        if alts and alts[0][0].strip() in valid:
            q = [OPTION_FLOOR] * n
            for tok, lp in alts:
                t = tok.strip()
                if len(t) == 1 and t in valid:
                    q[valid.index(t)] += math.exp(lp)
            total = sum(q)
            return [x / total for x in q]
    return None


def sharpen(q, t):
    """Temperature scaling: t > 1 flattens an overconfident distribution."""
    w = [x ** (1 / t) for x in q]
    return [x / sum(w) for x in w]


def read_options(llm, key, setting, question, item, answer, t=None):
    """Method DP: GLM's calibrated probability for each option of the item. Thinking is
    always off here: the reply is one letter. (setting is accepted for a uniform call.)"""
    msgs = [{"role": "system", "content": OPTION_SYSTEM},
            {"role": "user", "content": OPTION_MESSAGE.format(question=question, options=lettered(item),
                                                              answer=answer)}]
    r = llm.chat(key, msgs, "off", 400, 0.0, top_logprobs=20)
    q = option_probs(r.get("logprobs"), len(item["options"]))
    call = call_log(r, model=key, valid=q is not None, retry=False)
    if q is None:
        return None, [call]
    return sharpen(q, temperature() if t is None else t), [call]


def extract(llm, key, setting, question, item, answer, examples=""):
    """Method D: one spoken answer -> evidence (one retry if the reply isn't valid).
    examples: retrieved labeled answers for method DR (retrieval.examples_block)."""
    anchors = ""
    if item["dimension"] != "capacity":
        # bank scores run 0-1; the extractor's scale runs 0.1-0.9, so map them onto it
        anchors = "Answer options and their scores: " + "; ".join(
            f"{o['label']} ({0.1 + 0.8 * o['score']:.2f})" for o in BE.scored_options(item)) + "\n"
    msgs = [{"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": EXTRACT_MESSAGE.format(examples=examples, question=question,
                                                               anchors=anchors, answer=answer)}]
    calls = []
    for retry in (False, True):
        r = llm.chat(key, msgs, setting, C.INTERVIEWER_MAX_TOKENS, 0.0)
        ev = clean_evidence(extract_json(r["text"]))
        calls.append(call_log(r, model=key, valid=ev is not None, retry=retry))
        if ev is not None:
            return ev, calls
        msgs += [{"role": "assistant", "content": r["text"] or "(empty)"},
                 {"role": "user", "content": EXTRACT_RETRY}]
    return dict(NO_EVIDENCE), calls


def apply_evidence(belief, ev, turn):
    """Feed method D's evidence into the belief; returns contradiction flags."""
    flags = []
    for f, v in ev["facts"].items():
        hits = belief.observe_fact(f, *v["range"], vague=not v["clear"], turn=turn)
        if hits:
            flags.append(f"contradiction: {f} now {v['range']}, differs from the answer to question {hits[0] + 1}")
    if ev["willingness"]:
        w = ev["willingness"]
        belief.observe_score("willingness", w["score"], "stated", not w["clear"], turn)
    if ev["behavioral"]:
        b = ev["behavioral"]
        hits = belief.observe_score("behavioral", b["score"], b["kind"], not b["clear"], turn)
        if hits:
            flags.append(f"contradiction: past loss reaction differs from the answer to question {hits[0] + 1}")
    if ev.get("no_past_loss"):
        hits = belief.observe_no_past_loss(turn)
        if hits:
            flags.append(f"contradiction: says they never had a big loss, unlike the answer to question {hits[0] + 1}")
    return flags


FACT_ITEM = {"horizon_yrs": "CAP01", "emergency_fund_months": "CAP02", "income_stability": "CAP03",
             "debt_to_income": "CAP04", "dependents": "CAP05", "past_loss_reaction": "BEH02"}


def update_unclear(unclear, item, ev, flags, pool):
    """D re-asks a fact item only while it is unclear. "vague": its own answer gave no clear
    reading (re-asked once). "conflict": a contradiction about that fact was flagged, in
    this answer or any other (re-asked up to MAX_ASKS_PER_FACT times in all)."""
    fact = item.get("fact")
    if fact:
        got = ((ev["behavioral"] if ev["behavioral"] and ev["behavioral"]["kind"] == "past" else None)
               if fact == "past_loss_reaction" else ev["facts"].get(fact))
        clear = bool(got and got.get("clear", True)) or (fact == "past_loss_reaction" and ev.get("no_past_loss"))
        if clear:
            unclear.pop(item["id"], None)
        elif unclear.get(item["id"]) != "conflict":
            unclear[item["id"]] = "vague"
    for f in flags:
        if f.startswith("contradiction:"):
            topic = f.split(":", 1)[1].split()[0]
            target = FACT_ITEM.get(topic) or ("BEH02" if "past loss" in f or "never had a big loss" in f else None)
            if target:
                unclear[target] = "conflict"


def mentions(turn, fact):
    ev = turn.get("evidence") or {}
    if fact == "past_loss_reaction":
        return (ev.get("behavioral") or {}).get("kind") == "past" or bool(ev.get("no_past_loss"))
    return fact in ev.get("facts", {})


def clarify(llm, key, setting, item, turns):
    """Method D: word a question that re-asks one fact. Falls back to the bank wording."""
    fact = item["fact"]
    quotes = [t["a"] for t in turns if t["item"] == item["id"] or mentions(t, fact)][-3:]
    msgs = [{"role": "system", "content": CLARIFY_SYSTEM},
            {"role": "user", "content": CLARIFY_MESSAGE.format(
                fact=FACT_TEXT[fact], quotes="\n".join(f'- "{q}"' for q in quotes) or "- (none)")}]
    r = llm.chat(key, msgs, setting, C.INTERVIEWER_MAX_TOKENS, C.INTERVIEWER_TEMPERATURE)
    obj = extract_json(r["text"])
    q = obj.get("question") if isinstance(obj, dict) else None
    valid = isinstance(q, str) and bool(q.strip())
    return (q.strip() if valid else "Just to check: " + item["spoken"]), [
        call_log(r, model=key, valid=valid, retry=False, clarify=True)]


def pick_option(text, n):
    m = INT_RE.search(strip_think(text) or "")
    if m and 1 <= int(m.group(1)) <= n:
        return int(m.group(1))
    return None


def call_log(r, **extra):
    return {"usage": r["usage"], "latency": round(r["latency"], 3), "finish": r["finish"], **extra}


def run_form(llm, method, budget, persona, repeat, user, u_setting, mapper, m_setting, draw_noise,
             full_budget=True):
    """Methods A, B, C, C0 and D. full_budget: keep asking after the stop rule fires (main
    experiment); the turn where it fired is logged as would_stop_at."""
    bank = load_bank()
    pool = engine_pool(bank)
    # same seed as run_interview -> every method faces the same noise schedule
    rng = random.Random(zlib.crc32(f"{persona['id']}|{repeat}".encode()))
    u_msgs = [{"role": "system", "content": P.build_user_system(persona)}]
    fixed = short_form(bank, budget) if method in ("A", "B") else None
    spoken = method in ("B",) + D_METHODS
    belief = BE.Belief(channel="spoken" if method in ("D", "DR") else "form")
    answers, turns, u_calls, m_calls = [], [], [], []
    asks = {}
    unclear = {}   # D: fact item -> "vague" (no clear reading) or "conflict" (contradicted)
    said = set()
    would_stop_at, early_stop = None, False
    t0 = time.monotonic()

    for k in range(budget):
        t_engine = time.monotonic()
        info = None
        if fixed:
            item = fixed[k]
        elif method == "C0":
            item = next_adaptive_item(bank, answers, {a["id"] for a in answers})
        else:
            cands = [i for i in pool if i["id"] not in asks]
            if method in D_METHODS:   # a conversation can come back to a fact to check it.
                # Money facts: up to MAX_ASKS_PER_FACT asks; a second statement guards the
                # estimate against vague or false answers. The past-loss question: only when
                # unclear, because people repeat the same story (Nov 12, 20-user checks).
                cands += [i for i in pool if 0 < asks.get(i["id"], 0) < (
                    BE.MAX_ASKS_PER_FACT if i["dimension"] == "capacity" or unclear.get(i["id"]) == "conflict"
                    else 2 if unclear.get(i["id"]) == "vague" else 0)]
            item, info = belief.choose(cands, budget - k, seed=k)
            if info["settled"] and would_stop_at is None:
                would_stop_at = k   # the first time the band was settled
                if not full_budget:
                    early_stop = True
                    break
        engine_secs = round(time.monotonic() - t_engine, 3)
        reask = item["id"] in asks
        asks[item["id"]] = asks.get(item["id"], 0) + 1
        profile_before = belief.profile()
        step_calls = []

        noise = draw_noise(rng, persona, k)
        target = None
        if spoken:
            # spoken interview: same noise rules as method D0, including targeted contradictions
            if "contradiction" in noise:
                if said:
                    fact_rng = random.Random(zlib.crc32(f"{persona['id']}|{repeat}|{k}".encode()))
                    fact = fact_rng.choice(sorted(said))
                    target = {"fact": fact, "wrong": P.wrong_fact(persona, fact)}
                else:
                    noise.remove("contradiction")
            question = item["spoken"]
            if reask:
                question, step_calls = clarify(llm, mapper, m_setting, item, turns)
            note = P.private_note(noise, target["wrong"] if target else None)
        else:
            # a form has no follow-ups, so contradictions and agreeing-along don't apply
            noise = [n for n in noise if n in FORM_NOISE]
            question = FORM_PROMPT.format(question=item["text"], options=numbered(item))
            note = ("\n\n[Private note: " + " ".join(FORM_NOISE[n] for n in noise) + "]") if noise else ""

        u_msgs.append({"role": "user", "content": question + note})
        r = llm.chat(user, u_msgs, u_setting, C.USER_MAX_TOKENS, C.USER_TEMPERATURE)
        u_calls.append(call_log(r))
        answer = strip_think(r["text"]) or "(no answer)"
        u_msgs[-1]["content"] = question
        u_msgs.append({"role": "assistant", "content": answer})

        n = len(item["options"])
        choice, evidence, flags = None, None, []
        if method == "B":
            msgs = [{"role": "system", "content": MAPPER_SYSTEM},
                    {"role": "user", "content": MAPPER_MESSAGE.format(
                        question=item["spoken"], options=numbered(item), answer=answer)}]
            mr = llm.chat(mapper, msgs, m_setting, C.INTERVIEWER_MAX_TOKENS, 0.0)
            obj = extract_json(mr["text"])
            opt = obj.get("option") if isinstance(obj, dict) else None
            valid = isinstance(obj, dict) and (opt is None or (isinstance(opt, int) and 1 <= opt <= n))
            step_calls.append(call_log(mr, model=mapper, valid=valid, retry=False))
            choice = opt if valid else None
        elif method == "DP":
            q, calls = read_options(llm, mapper, m_setting, question, item, answer)
            step_calls += calls
            evidence = {"option_probs": [round(x, 4) for x in q] if q else None}
            if q:
                flags = [f"contradiction: {item.get('fact') or item['dimension']} differs from the answer "
                         f"to question {t + 1}" for t in belief.observe_soft(item, q, k)[:1]]
        elif method in D_METHODS:
            import retrieval
            examples = (retrieval.examples_block(pilot_pool().similar(item, question, answer))
                        if method == "DR" else "")
            evidence, calls = extract(llm, mapper, m_setting, question, item, answer, examples)
            step_calls += calls
            flags = apply_evidence(belief, evidence, k)
            update_unclear(unclear, item, evidence, flags, pool)
        else:
            choice = pick_option(answer, n)
            if choice is None:  # one nudge, then count it as unanswered
                u_msgs.append({"role": "user", "content": FORM_RETRY.format(n=n)})
                r2 = llm.chat(user, u_msgs, u_setting, C.USER_MAX_TOKENS, C.USER_TEMPERATURE)
                u_calls.append(call_log(r2, retry=True))
                u_msgs.append({"role": "assistant", "content": strip_think(r2["text"]) or "(no answer)"})
                choice = pick_option(r2["text"], n)
        if spoken and not {"vague", "flip", "contradiction"} & set(noise) and item.get("fact"):
            said.add(item["fact"])

        score = item["options"][choice - 1]["score"] if choice else None
        if method not in D_METHODS:
            belief.observe_option(item, choice)
            answers.append({"id": item["id"], "dimension": item["dimension"], "score": score})
        if belief.mismatch():
            flags.append("mismatch: two scores are likely 2+ bands apart")
        m_calls += step_calls
        # forms pick and score in code (no LLM); B's system call is the answer mapper; D's are
        # the extractor and, when it re-asks a fact, the clarifying question
        turns.append({"q": question, "item": item["id"], "reask": reask, "a": answer,
                      "option": choice, "score": score, "evidence": evidence, "noise": noise,
                      "contradiction_target": target, "profile_before": profile_before,
                      "flags_after": flags, "engine": info, "engine_secs": engine_secs,
                      "system_latency": round(sum(c["latency"] for c in step_calls), 3),
                      "system_calls": len(step_calls)})

    final_flags = (["mismatch: two scores are likely 2+ bands apart"]
                   if belief.mismatch() else [])
    return {
        "method": method, "budget": budget,
        "interviewer": mapper if spoken else None,
        "interviewer_setting": m_setting if spoken else None,
        "user": user, "user_setting": u_setting,
        "persona_id": persona["id"], "repeat": repeat,
        "truth": persona["ground_truth"], "persona": persona,
        "final_profile": belief.profile(),
        # the bank's plain-average scoring, kept for comparison (D has no option answers)
        "final_profile_mean": estimate(answers) if method not in D_METHODS else None,
        "final_flags": final_flags,
        "questions_asked": len(turns), "early_stop": early_stop,
        "would_stop_at": would_stop_at, "full_budget": full_budget,
        "aborted_invalid": False,
        "unanswered": sum(a["score"] is None for a in answers),
        "turns": turns, "interviewer_calls": m_calls, "user_calls": u_calls,
        "start_latency": 0.0, "engine_settings": BE.settings(),
        "short_form": [i["id"] for i in fixed] if fixed else None,
        "probes": [], "seconds": round(time.monotonic() - t0, 1),
    }
