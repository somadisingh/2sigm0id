"""Live chat in the terminal: a real person answers method D's questions (or method A's form).

Used for testing and the demo. For the classmate study, use the web app (web_app.py). Both use
live_session.py, which follows method D's steps in run_form (methods.py) with the person's
typed answer in place of the AI test user.

  python live_chat.py --participant P01                 # method D, 10 questions
  python live_chat.py --participant P01 --method A      # fixed form, 10 questions
  python live_chat.py --participant demo --stop-early   # end at the stop point (demo)
  python live_chat.py --participant test --mock         # no API key, random readings

Sessions are saved to live_sessions/ (gitignored). Use a participant ID, never a name.
The result is a risk profile for a study. It is not investment advice.
"""

import argparse
import sys

import config as C
from live_session import BAND_NAMES, DIM_NAMES, HERE, AForm, DInterview


def ask_text(prompt):
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


def show_result(r):
    print("\n" + "=" * 60 + "\nYour risk profile\n")
    for d, v in r["profile"].items():
        print(f"  {DIM_NAMES[d]:<48} {v:.2f}  (band {r['bands'][d]})")
    print(f"\n  Final band: {r['final_band']} ({BAND_NAMES[r['final_band']]})")
    print("  The final band is the lowest of the three bands.\n\n  How sure the system is:")
    for i, p in enumerate(r["band_probs"], 1):
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

    try:
        if args.method == "D":
            from run_bakeoff import make_llm
            s = DInterview(args.participant, make_llm(args.mock), C.EXPERIMENT_INTERVIEWER,
                           C.EXPERIMENT_INTERVIEWER_REASONING, args.budget, args.stop_early)
        else:
            s = AForm(args.participant, args.budget)
    except ValueError as e:
        sys.exit(str(e))

    print("Risk-profile interview" + (" (form)" if args.method == "A" else ""))
    print("Answer in your own words." if args.method == "D" else "Type the number of your answer.")
    print("There are no right or wrong answers. Press Ctrl-C to stop at any time.")
    try:
        while (q := s.next_question()) is not None:
            print(f"\nQuestion {s.k + 1} of {s.budget}")
            if args.method == "D":
                print(f"  {q}")
                answer = ask_text("  > ")
                print("  ...", end="", flush=True)
                s.answer(answer)
                print("\r     \r", end="")
            else:
                print(f"  {q['text']}")
                for n, o in enumerate(q["options"], 1):
                    print(f"    {n}. {o['label']}")
                s.answer(ask_option(len(q["options"])))
    except KeyboardInterrupt:
        s.stop()
        print(f"\n\nStopped. The answers so far are saved in {s.path.relative_to(HERE)}.")
        return
    show_result(s.finish())
    print(f"\nSaved: {s.path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
