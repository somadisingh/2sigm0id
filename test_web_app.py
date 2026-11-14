"""Headless test of the study web app in mock mode (no API key, no browser).

  python test_web_app.py

Walks an odd code (standard form first) through part 1, closes the page, logs in again,
continues with part 2 and checks the saved files. Checks that an even code starts with the
interviewer, and that a wrong access code, a bad code and a finished code are refused.
Uses codes P97 and P98, so a real study's files are not touched.
"""

import json
import os

os.environ["LIVE_MOCK"] = "1"
os.environ["STUDY_ACCESS_CODE"] = "test"

from streamlit.testing.v1 import AppTest   # noqa: E402

from live_session import OUT_DIR            # noqa: E402

ODD, EVEN = "P97", "P98"


def app():
    return AppTest.from_file("web_app.py", default_timeout=60).run()


def login(at, pid, code="test"):
    at.text_input[0].set_value(pid)
    at.text_input[1].set_value(code)
    at.button[0].click().run()
    return at


def errors(at):
    return " ".join(e.value for e in at.error)


def do_part(at, method):
    assert at.session_state.stage == "intro", at.session_state.stage
    at.button[0].click().run()
    for _ in range(10):
        if method == "D":
            at.chat_input[0].set_value("I would hold and wait, about 12 years, no debt").run()
        else:
            at.radio[0].set_value(at.radio[0].options[min(2, len(at.radio[0].options) - 1)])
            at.button[0].click().run()
        assert not at.exception, at.exception
    assert at.session_state.stage == "result", at.session_state.stage
    assert "not investment advice" in " ".join(i.value for i in at.info)
    assert any("Final band" in m.value for m in at.markdown)


def clean():
    for pid in (ODD, EVEN):
        for f in OUT_DIR.glob(f"{pid}_*.json"):
            f.unlink()


def main():
    clean()
    assert "not correct" in errors(login(app(), ODD, "wrong")), "wrong access code accepted"
    assert "P followed by two digits" in errors(login(app(), "Jane")), "bad code accepted"

    at = login(app(), EVEN)
    assert at.session_state.order == ["D", "A"], at.session_state.order

    # odd code: standard form first; part 1, then the page is closed
    at = login(app(), ODD)
    assert at.session_state.order == ["A", "D"], at.session_state.order
    do_part(at, "A")
    assert "After interview 1" in " ".join(m.value for m in at.markdown)

    # logs in again later: continues with part 2
    at = login(app(), ODD)
    assert at.session_state.part == 1, at.session_state.part
    assert "Welcome back" in " ".join(s.value for s in at.success)
    do_part(at, "D")
    assert "After interview 2" in " ".join(m.value for m in at.markdown)

    data = [json.loads(f.read_text()) for f in sorted(OUT_DIR.glob(f"{ODD}_*.json"))]
    assert len(data) == 2 and all(d["finished"] and len(d["turns"]) == 10 for d in data)
    assert {(d["method"], d["position"]) for d in data} == {("A", 1), ("D", 2)}
    assert "already finished both parts" in errors(login(app(), ODD)), "finished code accepted"

    clean()
    print("ok: odd code A then D with a break between parts, even code D first; wrong access "
          "code, bad code and finished code are refused")


if __name__ == "__main__":
    main()
