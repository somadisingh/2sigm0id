"""The three form-based methods for the main experiment. Method D (the adaptive
interviewer) is run_interview in run_bakeoff.py.

  A  fixed form          the default short form from question_bank.json, in order
  B  scripted interview  the same questions in their 'spoken' wording; the person answers
                         in their own words and a mapper model picks the matching option
  C  adaptive form       picks each next question from the bank based on what it knows so far

Every method uses the same simulated user, the same noise schedule and the same budget.
"""

import json
import math
import random
import re
import time
import zlib
from pathlib import Path

import config as C
import prompts as P
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


def load_bank():
    return json.loads((HERE / "question_bank.json").read_text())


def short_form(bank, budget):
    """Default short form: top-priority items per dimension (see short_form_allocation)."""
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


def pick_option(text, n):
    m = INT_RE.search(strip_think(text) or "")
    if m and 1 <= int(m.group(1)) <= n:
        return int(m.group(1))
    return None


def call_log(r, **extra):
    return {"usage": r["usage"], "latency": round(r["latency"], 3), "finish": r["finish"], **extra}


def run_form(llm, method, budget, persona, repeat, user, u_setting, mapper, m_setting, draw_noise):
    bank = load_bank()
    # same seed as run_interview -> every method faces the same noise schedule
    rng = random.Random(zlib.crc32(f"{persona['id']}|{repeat}".encode()))
    u_msgs = [{"role": "system", "content": P.build_user_system(persona)}]
    fixed = short_form(bank, budget) if method in ("A", "B") else None
    answers, turns, u_calls, m_calls = [], [], [], []
    said = set()
    t0 = time.monotonic()

    for k in range(budget):
        item = fixed[k] if fixed else next_adaptive_item(bank, answers, {a["id"] for a in answers})
        noise = draw_noise(rng, persona, k)
        target = None
        if method == "B":
            # spoken interview: same noise rules as method D, including targeted contradictions
            if "contradiction" in noise:
                if said:
                    fact_rng = random.Random(zlib.crc32(f"{persona['id']}|{repeat}|{k}".encode()))
                    fact = fact_rng.choice(sorted(said))
                    target = {"fact": fact, "wrong": P.wrong_fact(persona, fact)}
                else:
                    noise.remove("contradiction")
            question = item["spoken"]
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
        if method == "B":
            msgs = [{"role": "system", "content": MAPPER_SYSTEM},
                    {"role": "user", "content": MAPPER_MESSAGE.format(
                        question=item["spoken"], options=numbered(item), answer=answer)}]
            mr = llm.chat(mapper, msgs, m_setting, C.INTERVIEWER_MAX_TOKENS, 0.0)
            obj = extract_json(mr["text"])
            opt = obj.get("option") if isinstance(obj, dict) else None
            valid = isinstance(obj, dict) and (opt is None or (isinstance(opt, int) and 1 <= opt <= n))
            m_calls.append(call_log(mr, model=mapper, valid=valid, retry=False))
            choice = opt if valid else None
            if not {"vague", "flip", "contradiction"} & set(noise) and item.get("fact"):
                said.add(item["fact"])
        else:
            choice = pick_option(answer, n)
            if choice is None:  # one nudge, then count it as unanswered
                u_msgs.append({"role": "user", "content": FORM_RETRY.format(n=n)})
                r2 = llm.chat(user, u_msgs, u_setting, C.USER_MAX_TOKENS, C.USER_TEMPERATURE)
                u_calls.append(call_log(r2, retry=True))
                u_msgs.append({"role": "assistant", "content": strip_think(r2["text"]) or "(no answer)"})
                choice = pick_option(r2["text"], n)

        score = item["options"][choice - 1]["score"] if choice else None
        answers.append({"id": item["id"], "dimension": item["dimension"], "score": score})
        turns.append({"q": question, "item": item["id"], "a": answer, "option": choice,
                      "score": score, "noise": noise, "contradiction_target": target,
                      "profile_before": None})

    return {
        "method": method, "budget": budget,
        "interviewer": mapper if method == "B" else None,
        "interviewer_setting": m_setting if method == "B" else None,
        "user": user, "user_setting": u_setting,
        "persona_id": persona["id"], "repeat": repeat,
        "truth": persona["ground_truth"], "persona": persona,
        "final_profile": estimate(answers), "final_flags": None,
        "questions_asked": len(turns), "early_stop": False, "aborted_invalid": False,
        "unanswered": sum(a["score"] is None for a in answers),
        "turns": turns, "interviewer_calls": m_calls, "user_calls": u_calls,
        "probes": [], "seconds": round(time.monotonic() - t0, 1),
    }
