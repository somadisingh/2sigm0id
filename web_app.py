"""Web app for the classmate study (task S5). Siya's Google Form runs the study and links here
for "Interview 1" and "Interview 2". Each classmate does the standard form (method A) and the
adaptive interviewer (method D) in this app, in the order that the form gives:

  odd participant code (P01, P03, ...)   standard form first, then the adaptive interviewer
  even participant code (P02, P04, ...)  adaptive interviewer first, then the standard form

After each part the app shows that part's result, and the person goes back to the form to rate
it. A person who closes the page after part 1 logs in again and continues with part 2.

  streamlit run web_app.py                      # needs BASETEN_API_KEY and STUDY_ACCESS_CODE in .env
  LIVE_MOCK=1 streamlit run web_app.py          # no API key: random readings, for testing

Answers are saved to live_sessions/ (gitignored) after every answer. The result is a risk
profile for a study. It is not investment advice.
"""

import hmac
import os
import re

import streamlit as st

import config as C
import session_store
from live_session import DIM_NAMES, AForm, DInterview
from run_bakeoff import load_env, make_llm

load_env()
MOCK = os.environ.get("LIVE_MOCK") == "1"
ACCESS_CODE = os.environ.get("STUDY_ACCESS_CODE", "test" if MOCK else "")
BUDGET = 10
PID_RE = re.compile(r"^P\d{2}$")
# the names that Siya's form uses for the two parts and the five bands
PART_NAMES = {"A": "Standard form", "D": "Adaptive interviewer"}
PART_HELP = {"A": "Pick one answer for each question.", "D": "Answer each question in your own words."}
FORM_BANDS = {1: "Very Conservative", 2: "Conservative", 3: "Moderate", 4: "Aggressive", 5: "Very aggressive"}

st.set_page_config(page_title="Risk-profile study", page_icon="📋", layout="centered")

if not ACCESS_CODE:
    st.error("STUDY_ACCESS_CODE is not set. The app will not start without it.")
    st.stop()


@st.cache_resource
def store_check():
    """None if storage is fine, else the problem. A hosted app sets SESSION_STORE_REQUIRED=1:
    its disk is wiped on restart, so it must save to the private repo."""
    try:
        repo = session_store.check_remote()
    except Exception as e:   # noqa: BLE001 - shown to the operator, the app stops
        return f"The private session repo can't be used: {e}"
    if not repo and os.environ.get("SESSION_STORE_REQUIRED") == "1":
        return "SESSION_REPO and SESSION_REPO_TOKEN are not set, so answers would be lost."
    return None


if problem := store_check():
    st.error(f"The study app is not ready. {problem}")
    st.stop()


@st.cache_resource
def llm():
    return make_llm(MOCK)


def order_for(pid):
    """Siya's form: odd codes do the standard form first, even codes the interviewer first."""
    return ["A", "D"] if int(pid[1:]) % 2 else ["D", "A"]


def finished_parts(pid):
    """Methods this participant already finished, with their saved results."""
    done = {}
    for d in session_store.load_all(f"{pid}_"):
        if d.get("finished"):
            done[d["method"]] = {"profile": d["final_profile"], "bands": d["final_bands"],
                                 "final_band": d["final_band"], "band_probs": d["band_probs"]}
    return done


def new_part(method, pid, position):
    extra = {"study_order": S.order, "position": position, "channel": "web"}
    if method == "D":
        return DInterview(pid, llm(), C.EXPERIMENT_INTERVIEWER, C.EXPERIMENT_INTERVIEWER_REASONING,
                          BUDGET, extra=extra)
    return AForm(pid, BUDGET, extra=extra)


def show_result(r):
    cols = st.columns(3)
    for col, (d, v) in zip(cols, r["profile"].items()):
        col.metric(DIM_NAMES[d].split(" (")[0], f"band {r['bands'][d]}", f"score {v:.2f}", delta_color="off")
    st.markdown(f"### Final band: {r['final_band']} ({FORM_BANDS[r['final_band']]})")
    st.caption("Each score is from 0 (very careful) to 1 (very bold) and has a band from 1 to 5. "
               "The final band is the lowest of the three bands.")
    st.write("How sure the assistant is about your final band:")
    st.bar_chart({"chance": {f"band {i}": p for i, p in enumerate(r["band_probs"], 1)}},
                 horizontal=True, height=180)
    st.info("This is a research profile for a class project. It is not investment advice.")


S = st.session_state
S.setdefault("stage", "login")

st.title("Risk-profile study")
if MOCK:
    st.warning("Test mode: random readings, no API calls. Access code: test")

# ---------------------------------------------------------------- login
if S.stage == "login":
    st.write("Enter your participant code from the survey and the access code.")
    with st.form("login"):
        pid = st.text_input("Participant code (for example P07)").strip().upper()
        code = st.text_input("Access code", type="password")
        ok = st.form_submit_button("Continue")
    if ok:
        try:
            done = finished_parts(pid) if PID_RE.match(pid) else {}
        except Exception:   # noqa: BLE001 - the session repo can't be read right now
            st.error("The study app can't check your progress right now. Please try again in a minute.")
            st.stop()
        if not hmac.compare_digest(code.encode(), ACCESS_CODE.encode()):
            st.error("The access code is not correct.")
        elif not PID_RE.match(pid) or pid == "P00":
            st.error("The participant code is P followed by two digits, for example P07.")
        elif {"A", "D"} <= set(done):
            st.error("This code has already finished both parts. Go back to the survey. "
                     "If this is a mistake, contact the study team.")
        else:
            S.pid, S.order, S.results = pid, order_for(pid), done
            S.part = 0 if S.order[0] not in done else 1
            S.stage = "intro"
            st.rerun()

# ---------------------------------------------------------------- before a part
elif S.stage == "intro":
    method = S.order[S.part]
    if S.part == 1 and S.order[0] in S.results:
        st.success(f"Welcome back. You finished part 1 ({PART_NAMES[S.order[0]]}).")
    st.subheader(f"Part {S.part + 1} of 2: {PART_NAMES[method]}")
    st.markdown(
        f"- {PART_HELP[method]} There are {BUDGET} questions and no right or wrong answers.\n"
        "- Use the same finances as in the survey. Ranges are fine.\n"
        "- **Do not type your name** or other details that identify you.\n"
        "- **Do not refresh or close this page** until you see your result."
        + ("\n- An AI model reads your answers." if method == "D" else ""))
    if st.button(f"Start part {S.part + 1}"):
        S.session = new_part(method, S.pid, S.part + 1)
        S.stage = "part"
        st.rerun()

# ---------------------------------------------------------------- a part
elif S.stage == "part":
    s = S.session
    method = S.order[S.part]
    st.subheader(f"Part {S.part + 1} of 2: {PART_NAMES[method]}")

    if method == "D":
        for t in s.data["turns"]:
            st.chat_message("assistant").write(t["q"])
            st.chat_message("user").write(t["a"])
        with st.spinner("Preparing the next question..."):
            q = s.next_question()
        if q is not None:
            st.progress(s.k / s.budget, text=f"Question {s.k + 1} of {s.budget}")
            st.chat_message("assistant").write(q)
            answer = st.chat_input("Type your answer")
            if answer and answer.strip():
                with st.spinner("Reading your answer..."):
                    s.answer(answer.strip())
                st.rerun()
    else:
        q = s.next_question()
        if q is not None:
            st.progress(s.k / s.budget, text=f"Question {s.k + 1} of {s.budget}")
            with st.form(f"q{s.k}", clear_on_submit=True):
                st.write(f"**{q['text']}**")
                labels = [o["label"] for o in q["options"]]
                pick = st.radio("Your answer", labels, index=None, label_visibility="collapsed")
                sent = st.form_submit_button("Next")
            if sent:
                if pick is None:
                    st.error("Please pick one answer.")
                else:
                    s.answer(labels.index(pick) + 1)
                    st.rerun()

    if q is None:   # this part is over
        S.results[method] = s.finish()
        S.stored = s.stored
        S.stage = "result"
        st.rerun()

# ---------------------------------------------------------------- after a part
elif S.stage == "result":
    method = S.order[S.part]
    st.success(f"Part {S.part + 1} of 2 is done. Thank you.")
    if not S.get("stored", True):
        st.warning(f"Your answers could not be saved online. Please tell the study team your "
                   f"code ({S.pid}) and the time.")
    st.subheader(f"Your result: {PART_NAMES[method]}")
    show_result(S.results[method])
    st.subheader("Next step")
    if S.part == 0:
        st.write(f"Go back to the survey tab and answer the questions under **After interview 1**. "
                 f"Then come back to this page and start part 2 ({PART_NAMES[S.order[1]]}). "
                 "Keep this page open.")
        if st.button("Start part 2"):
            S.part, S.stage = 1, "intro"
            st.rerun()
    else:
        st.write("Go back to the survey tab, answer the questions under **After interview 2**, "
                 "and submit the survey. You can then close this page.")
