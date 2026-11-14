"""Test session_store.py's private-repo saving against a fake GitHub API (no network, no token).

  python test_session_store.py
"""

import base64
import io
import json
import os
import urllib.error

import session_store as SS


class FakeGitHub:
    def __init__(self, private=True):
        self.private, self.files, self.n = private, {}, 0

    def __call__(self, method, url, token, body=None):
        path = url.split("/contents/", 1)[1] if "/contents/" in url else None
        if path is None:
            return {"private": self.private}
        if method == "PUT":
            if path in self.files and body.get("sha") != self.files[path]["sha"]:
                raise urllib.error.HTTPError(url, 409, "conflict", {}, io.BytesIO())
            self.n += 1
            self.files[path] = {"sha": f"sha{self.n}", "content": body["content"]}
            return {"content": {"sha": f"sha{self.n}"}}
        if path == SS.REMOTE_DIR:
            if not self.files:
                raise urllib.error.HTTPError(url, 404, "not found", {}, io.BytesIO())
            return [{"name": p.split("/")[-1]} for p in self.files]
        f = self.files[path]
        return {"sha": f["sha"], "content": f["content"]}


def main():
    os.environ.update(SESSION_REPO="me/private-data", SESSION_REPO_TOKEN="fake")
    gh = FakeGitHub()
    SS._call = gh
    SS._shas.clear()

    assert SS.check_remote() == "me/private-data"
    assert SS.load_all("P96_") == []                      # empty repo
    assert SS.save("P96_A_1.json", {"turns": [1]})        # create
    assert SS.save("P96_A_1.json", {"turns": [1, 2]})     # update with the known sha
    SS._shas["P96_A_1.json"] = "stale"                    # e.g. another app instance wrote it
    assert SS.save("P96_A_1.json", {"turns": [1, 2, 3]})  # 409, re-read sha, retry
    got = SS.load_all("P96_")
    assert got == [{"turns": [1, 2, 3]}], got
    stored = json.loads(base64.b64decode(gh.files["sessions/P96_A_1.json"]["content"]))
    assert stored == {"turns": [1, 2, 3]}

    def down(*a, **k):
        raise urllib.error.URLError("network down")
    SS._call = down
    assert SS.save("P96_A_1.json", {"turns": [4]}) is False   # page keeps working
    assert (SS.LOCAL_DIR / "P96_A_1.json").exists()           # local copy still written

    SS._call = FakeGitHub(private=False)
    try:
        SS.check_remote()
        raise AssertionError("public repo accepted")
    except RuntimeError as e:
        assert "public" in str(e)

    (SS.LOCAL_DIR / "P96_A_1.json").unlink()
    print("ok: create, update, stale-sha retry, load, network failure and public-repo refusal")


if __name__ == "__main__":
    main()
