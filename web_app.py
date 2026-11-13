"""Web app for the classmate study (task S5): each classmate does the interview (method D) and
the form (method A) in their browser, in the order from study_order.json.

Run it on one laptop and share it with a Cloudflare quick tunnel (see README, "Web app"):

  streamlit run web_app.py                      # needs BASETEN_API_KEY and STUDY_ACCESS_CODE in .env
  LIVE_MOCK=1 streamlit run web_app.py          # no API key: random readings, for testing

The API key and the answers stay on the laptop that runs the app. Answers are saved to
live_sessions/ (gitignored) after every answer. Results are shown only after both parts, so
the first result cannot change the answers in the second part. The result is a risk profile
for a study. It is not investment advice.
"""

import hmac
import os

import streamlit as st

import config as C
import study_order
from live_session import BAND_NAMES, DIM_NAMES, OUT_DIR, AForm, DInterview
from run_bakeoff import load_env, make_llm

load_env()
MOCK = os.environ.get("LIVE_MOCK") == "1"
ACCESS_CODE = os.environ.get("STUDY_ACCESS_CODE", "test" if MOCK else "")
FORM_URL = os.environ.get("STUDY_FORM_URL", "")   # Siya's Google Form, shown at the end
BUDGET = 10
PART_NAMES = {"D": "Interview: answer in your own words", "A": "Form: pick one answer for each question"}

st.set_page_config(page_title="Risk-profile study", page_icon="📋", layout="centered")

if not ACCESS_CODE:
    st.error("STUDY_ACCESS_CODE is not set in .env. The app will not start without it.")
    st.stop()


@st.cache_resource
def llm():
    return make_llm(MOCK)


@st.cache_resource
def orders():
    return study_order.load()


def finished_before(pid):
    """True if this ID already has a finished interview and a finished form."""
    import json
    done = set()
    for f in OUT_DIR.glob(f"{pid}_*.json"):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if d.get("finished"):
            done.add(d.get("method"))
    return {"A", "D"} <= done


def new_part(method, pid, position):
    extra = {"study_order": orders()[pid], "position": position, "channel": "web"}
    if method == "D":
        return DInterview(pid, llm(), C.EXPERIMENT_INTERVIEWER, C.EXPERIMENT_INTERVIEWER_REASONING,
                          BUDGET, extra=extra)
    return AForm(pid, BUDGET, extra=extra)


S = st.session_state
S.setdefault("stage", "login")

st.title("Risk-profile study")
if MOCK:
    st.warning("Test mode: random readings, no API calls. Access code: test")

# ---------------------------------------------------------------- login
if S.stage == "login":
    st.write("Thank you for helping with our class project. Enter the participant ID and the "
             "access code that you received.")
    with st.form("login"):
        pid = st.text_input("Participant ID (for example P07)").strip().upper()
        code = st.text_input("Access code", type="password")
        ok = st.form_submit_button("Continue")
    if ok:
        if not hmac.compare_digest(code.encode(), ACCESS_CODE.encode()):
            st.error("The access code is not correct.")
        elif pid not in orders():
            st.error("This participant ID is not in the study list. Check the ID that you received.")
        elif finished_before(pid):
            st.error("This ID has already completed the study. If this is a mistake, contact the study team.")
        else:
            S.pid, S.order, S.stage = pid, orders()[pid], "consent"
            st.rerun()

# ---------------------------------------------------------------- consent
elif S.stage == "consent":
    st.subheader("Before you start")
    st.markdown(
        "- You do two short parts: an **interview** where you answer in your own words, and a "
        "**form** where you pick answers. Each part has 10 questions. Together they take about "
        "15 to 20 minutes.\n"
        "- Answer as yourself. There are no right or wrong answers. You can skip details you "
        "do not want to share by saying so.\n"
        "- **Do not type your name** or other details that identify you.\n"
        "- Your answers are saved with your participant ID only and used for our class project. "
        "In the interview, an AI model reads your answers.\n"
        "- At the end you see a risk profile. It is a research result, **not investment advice**.\n"
        "- **Do not refresh or close this page** until the end, or your progress is lost.")
    agree = st.checkbox("I understand and want to take part.")
    if st.button("Start", disabled=not agree):
        S.part = 0
        S.session = new_part(S.order[0], S.pid, 1)
        S.stage = "part"
        st.rerun()

# ---------------------------------------------------------------- the two parts
elif S.stage == "part":
    s = S.session
    method = S.order[S.part]
    st.subheader(f"Part {S.part + 1} of 2. {PART_NAMES[method]}")

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
        S.setdefault("results", {})[method] = s.finish()
        if S.part == 0:
            S.part, S.stage = 1, "between"
        else:
            S.stage = "done"
        st.rerun()

# ---------------------------------------------------------------- between the parts
elif S.stage == "between":
    st.success("Part 1 is done. Thank you.")
    st.write(f"Part 2: **{PART_NAMES[S.order[1]]}**. You will see your results after part 2.")
    if st.button("Start part 2"):
        S.session = new_part(S.order[1], S.pid, 2)
        S.stage = "part"
        st.rerun()

# ---------------------------------------------------------------- results
elif S.stage == "done":
    st.success("You are done. Thank you for taking part.")
    st.write("Here are your two risk profiles. Each score is from 0 (very careful) to 1 (very bold). "
             "Each score has a band from 1 to 5. The final band is the lowest of the three bands.")
    for method, title in (("D", "Interview result"), ("A", "Form result")):
        r = S.results[method]
        st.subheader(title)
        cols = st.columns(3)
        for col, (d, v) in zip(cols, r["profile"].items()):
            col.metric(DIM_NAMES[d].split(" (")[0], f"{v:.2f}", f"band {r['bands'][d]}", delta_color="off")
        st.write(f"**Final band: {r['final_band']} ({BAND_NAMES[r['final_band']]})**")
        st.bar_chart({"chance": {f"band {i}": p for i, p in enumerate(r["band_probs"], 1)}},
                     horizontal=True, height=180)
    st.info("This is a research profile for a class project. It is not investment advice.")
    st.subheader("Last step")
    st.write(f"Please complete the short survey and enter your participant ID **{S.pid}**.")
    if FORM_URL:
        st.link_button("Open the survey", FORM_URL)
