"""Headless test of the study web app in mock mode (no API key, no browser).

  python test_web_app.py

Walks one participant through login, consent, both parts and the results page, and checks the
saved session files. Also checks a wrong access code, an unknown ID and a reused ID.
"""

import json
import os
import shutil

os.environ["LIVE_MOCK"] = "1"
os.environ["STUDY_ACCESS_CODE"] = "test"

from streamlit.testing.v1 import AppTest   # noqa: E402

import study_order                          # noqa: E402
from live_session import OUT_DIR            # noqa: E402

PID = "P39"   # an ID late in the list, so a real study's files are not touched
TIMEOUT = 60


def app():
    return AppTest.from_file("web_app.py", default_timeout=TIMEOUT).run()


def login(at, pid, code="test"):
    at.text_input[0].set_value(pid)
    at.text_input[1].set_value(code)
    at.button[0].click().run()
    return at


def errors(at):
    return " ".join(e.value for e in at.error)


def main():
    for f in OUT_DIR.glob(f"{PID}_*.json"):
        f.unlink()

    assert "not correct" in errors(login(app(), PID, "wrong")), "wrong code accepted"
    assert "not in the study list" in errors(login(app(), "P99")), "unknown ID accepted"

    at = login(app(), PID)
    assert at.session_state.stage == "consent", at.session_state.stage
    at.checkbox[0].check().run()
    at.button[0].click().run()

    order = study_order.load()[PID]
    for part, method in enumerate(order):
        assert at.session_state.stage == "part" and at.session_state.part == part
        for k in range(10):
            if method == "D":
                at.chat_input[0].set_value("I would hold and wait, about 12 years, no debt").run()
            else:
                at.radio[0].set_value(at.radio[0].options[min(2, len(at.radio[0].options) - 1)])
                at.button[0].click().run()
            assert not at.exception, at.exception
        if part == 0:
            assert at.session_state.stage == "between", at.session_state.stage
            at.button[0].click().run()

    assert at.session_state.stage == "done", at.session_state.stage
    assert set(at.session_state.results) == {"A", "D"}
    text = " ".join(m.value for m in at.markdown)
    assert "not investment advice" in " ".join(i.value for i in at.info)
    assert PID in text

    files = sorted(OUT_DIR.glob(f"{PID}_*.json"))
    data = [json.loads(f.read_text()) for f in files]
    assert len(data) == 2 and all(d["finished"] and len(d["turns"]) == 10 for d in data)
    assert {d["method"] for d in data} == {"A", "D"}
    assert all(d["study_order"] == order and d["channel"] == "web" for d in data)
    assert "already completed" in errors(login(app(), PID)), "reused ID accepted"

    for f in files:
        f.unlink()
    print(f"ok: {PID} order {order}, both parts saved and finished; wrong code, unknown ID "
          "and reused ID are refused")


if __name__ == "__main__":
    main()
