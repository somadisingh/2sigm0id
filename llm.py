"""Thin wrapper around Baseten's OpenAI-compatible API: rate limits, retries,
usage logging, JSON parsing, and a mock mode for testing without an API key."""

import json
import math
import random
import re
import threading
import time

THINK_RE = re.compile(r"<think>.*?</think>", re.S)


class RateLimiter:
    """Spaces out request starts so a model never exceeds its requests-per-minute limit."""

    def __init__(self, rpm):
        self.interval = 60.0 / rpm if rpm else 0.0
        self.lock = threading.Lock()
        self.next_time = 0.0

    def wait(self):
        if not self.interval:
            return
        with self.lock:
            start = max(time.monotonic(), self.next_time)
            self.next_time = start + self.interval
        delay = start - time.monotonic()
        if delay > 0:
            time.sleep(delay)


class LLM:
    def __init__(self, models, reasoning_settings, base_url=None, api_key=None, mock=False):
        self.models = models
        self.reasoning_settings = reasoning_settings
        self.mock = mock
        self.limiters = {k: RateLimiter(0 if mock else v["rpm"]) for k, v in models.items()}
        self.client = None
        if not mock:
            from openai import OpenAI
            self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=240, max_retries=0)

    def extra_body(self, key, setting):
        overrides = self.models[key].get("reasoning", {})
        if setting in overrides:
            return overrides[setting]
        return self.reasoning_settings.get(setting, {})

    def chat(self, key, messages, setting, max_tokens, temperature=None, top_logprobs=0):
        """Returns dict(text, usage{in,out,reasoning}, latency, finish). With top_logprobs > 0
        it also returns "logprobs": for each output token, its top alternatives as
        [(token, logprob), ...]. Support depends on the model (GLM 5.3: yes; DeepSeek: no)."""
        if self.mock:
            return _mock_reply(messages, top_logprobs)
        m = self.models[key]
        kwargs = dict(model=m["id"], messages=messages, max_tokens=max_tokens)
        if top_logprobs:
            kwargs.update(logprobs=True, top_logprobs=top_logprobs)
        temp = m.get("temperature", temperature)
        if temp is not None:
            kwargs["temperature"] = temp
        body = self.extra_body(key, setting)
        if body:
            kwargs["extra_body"] = body  # merged into the top level of the request

        last_err = None
        for attempt in range(6):
            self.limiters[key].wait()
            t0 = time.monotonic()
            try:
                r = self.client.chat.completions.create(**kwargs)
                latency = time.monotonic() - t0
                msg = r.choices[0].message
                u = r.usage
                usage = {"in": getattr(u, "prompt_tokens", 0) or 0,
                         "out": getattr(u, "completion_tokens", 0) or 0,
                         "reasoning": 0}
                det = getattr(u, "completion_tokens_details", None)
                if det is not None and getattr(det, "reasoning_tokens", None):
                    usage["reasoning"] = det.reasoning_tokens
                out = {"text": msg.content or "", "usage": usage, "latency": latency,
                       "finish": r.choices[0].finish_reason}
                if top_logprobs:
                    lp = getattr(r.choices[0], "logprobs", None)
                    out["logprobs"] = [[(a.token, a.logprob) for a in (t.top_logprobs or [])]
                                       for t in ((lp.content or []) if lp else [])]
                return out
            except Exception as e:  # noqa: BLE001 - we classify by status code
                last_err = e
                status = getattr(e, "status_code", None)
                if status in (400, 401, 403, 404, 422):
                    raise  # bad request / auth / wrong model ID: retrying won't help
                time.sleep(min(60, 2 ** attempt + random.random()))
        raise RuntimeError(f"{key}: gave up after retries: {last_err}")


def strip_think(text):
    return THINK_RE.sub("", text or "").strip()


def extract_json(text):
    """Find the first JSON object in a reply (handles code fences and stray text)."""
    text = strip_think(text)
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def validate_interviewer(obj):
    """Return a cleaned reply, or None if it doesn't follow the required format."""
    if not isinstance(obj, dict) or not isinstance(obj.get("profile"), dict):
        return None
    prof = {}
    for dim in ("capacity", "willingness", "behavioral"):
        v = obj["profile"].get(dim)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1:
            return None
        prof[dim] = float(v)
    conf = obj.get("confidence") if isinstance(obj.get("confidence"), dict) else {}
    flags = obj.get("flags") if isinstance(obj.get("flags"), list) else []
    q = obj.get("question")
    q = q.strip() if isinstance(q, str) and q.strip() else None
    return {"profile": prof, "confidence": conf, "flags": [str(f) for f in flags], "question": q}


# ---------------------------------------------------------------- mock mode

def _mock_reply(messages, top_logprobs=0):
    """Fake replies so the whole pipeline can be tested without spending money."""
    system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
    last = messages[-1]["content"]
    prompt_chars = sum(len(m["content"]) for m in messages)
    if "onboarding interviewer" in system:
        if random.random() < 0.08:
            text = "Sure! Here's my assessment: the user seems cautious."  # invalid on purpose
        else:
            done = "Questions left: 0" in last or random.random() < 0.03
            flags = []
            if random.random() < 0.25:
                flags.append(random.choice(["contradiction: changed story about savings",
                                            "mismatch: bold talk, thin savings"]))
            text = "```json\n" + json.dumps({
                "profile": {d: round(random.random(), 2) for d in ("capacity", "willingness", "behavioral")},
                "confidence": {d: round(random.random(), 2) for d in ("capacity", "willingness", "behavioral")},
                "flags": flags,
                "question": None if done else "How would you feel if your savings dropped by a fifth?",
            }) + "\n```"
    elif "into evidence" in system:   # method D's extractor
        ev = {"facts": {}}
        if random.random() < 0.5:
            lo = random.choice([1, 3, 6, 12, 20])
            ev["facts"][random.choice(["horizon_yrs", "emergency_fund_months", "dependents"])] = {
                "range": [lo, lo + 2], "clear": random.random() < 0.8}
        for d in ("willingness", "behavioral"):
            if random.random() < 0.5:
                ev[d] = {"score": round(random.random(), 2), "clear": True, "kind": "past"}
        text = json.dumps(ev) if random.random() > 0.05 else "not json"
    elif "check one answer from an interview" in system:   # check_personas.py's judge
        m = re.search(r'Answer: "(.*?)"\nStatement', last, re.S)
        words = (m.group(1) if m else "").split()
        text = json.dumps({"says_it": random.random() < 0.7, "quote": " ".join(words[:3])})
    elif "check one reading" in system:   # check_extractor.py's judge
        m = re.search(r'Answer: "(.*?)"\nReading', last, re.S)
        words = (m.group(1) if m else "").split()
        text = json.dumps({"supported": random.random() < 0.85, "quote": " ".join(words[:4])})
    elif "follow-up question" in system:   # method D's clarifying question
        text = json.dumps({"question": "Just to check, which of those is right?"})
    elif "multiple-choice question" in system:   # method B's answer mapper
        text = json.dumps({"option": random.choice([1, 2, 3, None])})
    elif "Reply with just the number of your answer" in last or "Please reply with just one number" in last:
        text = random.choice(["2", "3", "I'd say 1", "4", "not sure"])
    elif "Reply with just a number" in last:
        text = str(random.choice([0, 1, 3, 4, 7, 12, 15, 20, 30]))
    elif "Reply with one word" in last:
        text = random.choice(["sold", "held", "none"])
    else:
        text = " ".join(random.choice(["honestly", "I", "think", "maybe", "savings", "not",
                                       "sure", "a", "few", "months", "risky"])
                        for _ in range(random.randint(5, 60)))
    out = len(text) // 4 + random.randint(0, 200)
    reply = {"text": text, "usage": {"in": prompt_chars // 4, "out": out, "reasoning": out // 3},
             "latency": random.uniform(0.5, 4.0), "finish": "stop"}
    if top_logprobs:   # method DP's option reader: a random spread over the first letters
        letters = "ABCDE"
        w = [random.random() ** 3 for _ in letters]
        reply["text"] = letters[w.index(max(w))]
        reply["logprobs"] = [[(c, math.log(x / sum(w))) for c, x in zip(letters, w)]]
    return reply
