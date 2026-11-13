"""Live chat: a real person answers method D's questions (or method A's form) in the terminal.

Used for the classmate study (task S5) and the final demo. Method D follows the same steps as
method D in run_form (methods.py); the only change is that a person types each answer instead
of an AI test user. Method A shows the default short form and scores it with the same engine.

  python live_chat.py --participant P01                 # method D, 10 questions
  python live_chat.py --participant P01 --method A      # fixed form, 10 questions
  python live_chat.py --participant demo --stop-early   # end at the stop point (demo)
  python live_chat.py --participant test --mock         # no API key, random readings

Each session is saved to live_sessions/<participant>_<method>_<time>.json after every answer,
so a crash or Ctrl-C keeps what was said. live_sessions/ is in .gitignore: the repo is public,
and these files hold real people's answers. Use a participant ID, never a name.

The result is a risk profile for a study. It is not investment advice.
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

import belief as BE
import config as C
import methods as M
from prompts import band

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "live_sessions"
BAND_NAMES = {1: "very careful", 2: "careful", 3: "balanced", 4: "bold", 5: "very bold"}
DIM_NAMES = {"capacity": "Capacity (how much loss you can afford)",
             "willingness": "Willingness (how much risk you say you like)",
             "behavioral": "Behavior (what you do in a loss)"}
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def band_state(b):
    """The current final-band probabilities and the most likely band."""
    pmf = b.final_pmf(b.band_pmfs())
    return {"top_band": int(np.argmax(pmf)) + 1, "band_probs": [round(float(x), 3) for x in pmf]}


def ask_text(prompt):
    """Read one non-empty answer from the person."""
    while True:
        try:
            text = input(prompt).strip()
        except EOFError:
            raise KeyboardInterrupt
        if text:
            return text
        print("  Please type an answer (or press Ctrl-C to stop).")


def ask_option(n):
    while True:
        text = ask_text(f"  Your answer (1-{n}): ")
        if text.isdigit() and 1 <= int(text) <= n:
            return int(text)
        print(f"  Please type one number from 1 to {n}.")


class Session:
    """One person's conversation, saved to disk after every answer."""

    def __init__(self, participant, method, budget, stop_early, model, setting):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        OUT_DIR.mkdir(exist_ok=True)
        self.path = OUT_DIR / f"{participant}_{method}_{stamp}.json"
        self.data = {"participant": participant, "method": method, "budget": budget,
                     "stop_early": stop_early, "started": datetime.now().isoformat(timespec="seconds"),
                     "extractor": model if method == "D" else None,
                     "extractor_setting": setting if method == "D" else None,
                     "engine_settings": BE.settings(), "turns": [], "system_calls": [],
                     "would_stop_at": None, "finished": False}

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1))
        tmp.replace(self.path)


def run_d(llm, session, budget, stop_early, model, setting):
    """Method D with a person: the loop of run_form (methods.py), minus the AI test user and
    the injected noise."""
    pool = M.engine_pool(M.load_bank())
    b = BE.Belief(channel="spoken")
    asks, unclear, turns = {}, {}, session.data["turns"]

    for k in range(budget):
        cands = [i for i in pool if i["id"] not in asks]
        # same re-ask rule as run_form for method D
        cands += [i for i in pool if 0 < asks.get(i["id"], 0) < (
            BE.MAX_ASKS_PER_FACT if i["dimension"] == "capacity" or unclear.get(i["id"]) == "conflict"
            else 2 if unclear.get(i["id"]) == "vague" else 0)]
        item, info = b.choose(cands, budget - k, seed=k)
        if info["settled"] and session.data["would_stop_at"] is None:
            session.data["would_stop_at"] = k
            if stop_early:
                break
        reask = item["id"] in asks
        asks[item["id"]] = asks.get(item["id"], 0) + 1
        before, profile_before = band_state(b), b.profile()

        calls = []
        question = item["spoken"]
        if reask:
            question, calls = M.clarify(llm, model, setting, item, turns)
        print(f"\nQuestion {k + 1} of {budget}\n  {question}")
        t_answer = time.monotonic()
        answer = ask_text("  > ")
        answer_secs = round(time.monotonic() - t_answer, 1)

        print("  ...", end="", flush=True)
        evidence, ext_calls = M.extract(llm, model, setting, question, item, answer)
        print("\r     \r", end="")
        calls += ext_calls
        flags = M.apply_evidence(b, evidence, k)
        M.update_unclear(unclear, item, evidence, flags, pool)
        if b.mismatch():
            flags.append("mismatch: two scores are likely 2+ bands apart")
        after = band_state(b)

        # logged for ablation test 3: does a re-ask change the band for a real person?
        turns.append({"q": question, "item": item["id"], "reask": reask, "a": answer,
                      "answer_secs": answer_secs, "evidence": evidence, "flags_after": flags,
                      "engine": info, "profile_before": profile_before,
                      "band_before": before, "band_after": after,
                      "band_changed": before["top_band"] != after["top_band"],
                      "system_latency": round(sum(c["latency"] for c in calls), 3)})
        session.data["system_calls"] += calls
        session.save()
    return b


def run_a(session, budget):
    """Method A with a person: the default short form, scored by the engine (form channel)."""
    bank = M.load_bank()
    form = M.short_form(bank, budget)
    b = BE.Belief()
    for k, item in enumerate(form):
        print(f"\nQuestion {k + 1} of {len(form)}\n  {item['text']}")
        for n, o in enumerate(item["options"], 1):
            print(f"    {n}. {o['label']}")
        before = band_state(b)
        choice = ask_option(len(item["options"]))
        b.observe_option(item, choice)
        after = band_state(b)
        session.data["turns"].append({"q": item["text"], "item": item["id"], "option": choice,
                                      "score": item["options"][choice - 1]["score"],
                                      "band_before": before, "band_after": after})
        session.save()
    session.data["short_form"] = [i["id"] for i in form]
    return b


def show_result(b, session):
    profile = b.profile()
    pmf = b.final_pmf(b.band_pmfs())
    final = int(np.argmax(pmf)) + 1
    session.data.update({"final_profile": profile,
                         "final_bands": {d: band(v) for d, v in profile.items()},
                         "final_band": final, "band_probs": [round(float(x), 3) for x in pmf],
                         "mismatch": b.mismatch(), "finished": True,
                         "ended": datetime.now().isoformat(timespec="seconds")})
    session.save()

    print("\n" + "=" * 60 + "\nYour risk profile\n")
    for d, v in profile.items():
        print(f"  {DIM_NAMES[d]:<48} {v:.2f}  (band {band(v)})")
    print(f"\n  Final band: {final} ({BAND_NAMES[final]})")
    print("  The final band is the lowest of the three bands.\n\n  How sure the system is:")
    for i, p in enumerate(pmf, 1):
        print(f"    band {i}  {'#' * round(p * 30):<30} {p:.0%}")
    print("\n  This is a research profile for a class project. It is not investment advice.")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--participant", required=True, help="participant ID, for example P01 (never a name)")
    ap.add_argument("--method", choices=["D", "A"], default="D")
    ap.add_argument("--budget", type=int, choices=[5, 10, 15], default=10)
    ap.add_argument("--stop-early", action="store_true",
                    help="method D: end at the stop point (for the demo; the study asks the full budget)")
    ap.add_argument("--mock", action="store_true", help="no API key: random readings, for testing")
    args = ap.parse_args()
    if not ID_RE.match(args.participant):
        sys.exit("Use a short participant ID with letters, numbers, - or _ (for example P01).")

    model, setting = C.EXPERIMENT_INTERVIEWER, C.EXPERIMENT_INTERVIEWER_REASONING
    llm = None
    if args.method == "D":
        from run_bakeoff import make_llm
        llm = make_llm(args.mock)
    session = Session(args.participant, args.method, args.budget, args.stop_early, model, setting)

    print("Risk-profile interview" + (" (form)" if args.method == "A" else ""))
    print("Answer in your own words." if args.method == "D" else "Type the number of your answer.")
    print("There are no right or wrong answers. Press Ctrl-C to stop at any time.")
    try:
        b = (run_d(llm, session, args.budget, args.stop_early, model, setting)
             if args.method == "D" else run_a(session, args.budget))
    except KeyboardInterrupt:
        session.data["ended"] = datetime.now().isoformat(timespec="seconds")
        session.save()
        print(f"\n\nStopped. The answers so far are saved in {session.path.relative_to(HERE)}.")
        return
    show_result(b, session)
    print(f"\nSaved: {session.path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
