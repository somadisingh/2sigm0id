"""One live session with a real person, one question at a time. Shared by the terminal chat
(live_chat.py) and the web app (web_app.py).

DInterview follows the steps of method D in run_form (methods.py): the same question choice,
re-ask rule, extractor and evidence update. The person's answer replaces the AI test user, and
no noise is injected. AForm is the default short form (method A), scored by the same engine.

Each session is saved to live_sessions/<participant>_<method>_<time>.json after every answer.
live_sessions/ is in .gitignore: the repo is public, and these files hold real people's answers.
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path

import numpy as np

import belief as BE
import methods as M
from prompts import band

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "live_sessions"
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
BAND_NAMES = {1: "very careful", 2: "careful", 3: "balanced", 4: "bold", 5: "very bold"}
DIM_NAMES = {"capacity": "Capacity (how much loss you can afford)",
             "willingness": "Willingness (how much risk you say you like)",
             "behavioral": "Behavior (what you do in a loss)"}


def band_state(b):
    """The current final-band probabilities and the most likely band."""
    pmf = b.final_pmf(b.band_pmfs())
    return {"top_band": int(np.argmax(pmf)) + 1, "band_probs": [round(float(x), 3) for x in pmf]}


class _Session:
    method = None

    def __init__(self, participant, budget, extra=None):
        if not ID_RE.match(participant):
            raise ValueError("Use a short participant ID with letters, numbers, - or _ (for example P01).")
        self.budget = budget
        self.belief = None
        self.k = 0          # questions answered so far
        self.current = None  # (question text, item) waiting for an answer
        self.asked_at = None
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        OUT_DIR.mkdir(exist_ok=True)
        self.path = OUT_DIR / f"{participant}_{self.method}_{stamp}.json"
        self.data = {"participant": participant, "method": self.method, "budget": budget,
                     "started": datetime.now().isoformat(timespec="seconds"),
                     "engine_settings": BE.settings(), "turns": [], "would_stop_at": None,
                     "finished": False, **(extra or {})}

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1))
        tmp.replace(self.path)

    @property
    def done(self):
        return self.data["finished"] or (self.current is None and self.k >= self.budget)

    def stop(self):
        """The person stopped early: keep what was said."""
        self.data["ended"] = datetime.now().isoformat(timespec="seconds")
        self.save()

    def finish(self):
        b = self.belief
        profile = b.profile()
        pmf = b.final_pmf(b.band_pmfs())
        self.data.update({"final_profile": profile,
                          "final_bands": {d: band(v) for d, v in profile.items()},
                          "final_band": int(np.argmax(pmf)) + 1,
                          "band_probs": [round(float(x), 3) for x in pmf],
                          "mismatch": b.mismatch(), "finished": True,
                          "ended": datetime.now().isoformat(timespec="seconds")})
        self.save()
        return self.result()

    def result(self):
        d = self.data
        return {"profile": d["final_profile"], "bands": d["final_bands"],
                "final_band": d["final_band"], "band_probs": d["band_probs"]}


class DInterview(_Session):
    """Method D with a person."""
    method = "D"

    def __init__(self, participant, llm, model, setting, budget=10, stop_early=False, extra=None):
        super().__init__(participant, budget, {"extractor": model, "extractor_setting": setting,
                                               "stop_early": stop_early, "system_calls": [],
                                               **(extra or {})})
        self.llm, self.model, self.setting, self.stop_early = llm, model, setting, stop_early
        self.pool = M.engine_pool(M.load_bank())
        self.belief = BE.Belief(channel="spoken")
        self.asks, self.unclear = {}, {}
        self._pending = None

    def next_question(self):
        """The next question text, or None when the interview is over."""
        if self.current:
            return self.current[0]
        if self.k >= self.budget:
            return None
        cands = [i for i in self.pool if i["id"] not in self.asks]
        # same re-ask rule as run_form for method D
        cands += [i for i in self.pool if 0 < self.asks.get(i["id"], 0) < (
            BE.MAX_ASKS_PER_FACT if i["dimension"] == "capacity" or self.unclear.get(i["id"]) == "conflict"
            else 2 if self.unclear.get(i["id"]) == "vague" else 0)]
        item, info = self.belief.choose(cands, self.budget - self.k, seed=self.k)
        if info["settled"] and self.data["would_stop_at"] is None:
            self.data["would_stop_at"] = self.k
            if self.stop_early:
                self.budget = self.k
                return None
        reask = item["id"] in self.asks
        self.asks[item["id"]] = self.asks.get(item["id"], 0) + 1
        calls, question = [], item["spoken"]
        if reask:
            question, calls = M.clarify(self.llm, self.model, self.setting, item, self.data["turns"])
        self._pending = {"info": info, "reask": reask, "calls": calls,
                         "before": band_state(self.belief), "profile_before": self.belief.profile()}
        self.current = (question, item)
        self.asked_at = time.monotonic()
        return question

    def answer(self, text):
        question, item = self.current
        p = self._pending
        answer_secs = round(time.monotonic() - self.asked_at, 1)
        evidence, ext_calls = M.extract(self.llm, self.model, self.setting, question, item, text)
        calls = p["calls"] + ext_calls
        flags = M.apply_evidence(self.belief, evidence, self.k)
        M.update_unclear(self.unclear, item, evidence, flags, self.pool)
        if self.belief.mismatch():
            flags.append("mismatch: two scores are likely 2+ bands apart")
        after = band_state(self.belief)
        # logged for ablation test 3: does a re-ask change the band for a real person?
        self.data["turns"].append({
            "q": question, "item": item["id"], "reask": p["reask"], "a": text,
            "answer_secs": answer_secs, "evidence": evidence, "flags_after": flags,
            "engine": p["info"], "profile_before": p["profile_before"],
            "band_before": p["before"], "band_after": after,
            "band_changed": p["before"]["top_band"] != after["top_band"],
            "system_latency": round(sum(c["latency"] for c in calls), 3)})
        self.data["system_calls"] += calls
        self.k += 1
        self.current = self._pending = None
        self.save()


class AForm(_Session):
    """Method A with a person: the default short form."""
    method = "A"

    def __init__(self, participant, budget=10, extra=None):
        super().__init__(participant, budget, extra)
        self.form = M.short_form(M.load_bank(), budget)
        self.data["short_form"] = [i["id"] for i in self.form]
        self.belief = BE.Belief()

    def next_question(self):
        """The next item (dict with text and options), or None when the form is done."""
        if self.k >= len(self.form):
            return None
        item = self.form[self.k]
        self.current = (item["text"], item)
        self.asked_at = time.monotonic()
        return item

    def answer(self, choice):
        _, item = self.current
        if not (isinstance(choice, int) and 1 <= choice <= len(item["options"])):
            raise ValueError(f"choice must be 1-{len(item['options'])}")
        before = band_state(self.belief)
        self.belief.observe_option(item, choice)
        self.data["turns"].append({"q": item["text"], "item": item["id"], "option": choice,
                                   "score": item["options"][choice - 1]["score"],
                                   "answer_secs": round(time.monotonic() - self.asked_at, 1),
                                   "band_before": before, "band_after": band_state(self.belief)})
        self.k += 1
        self.current = None
        self.save()
