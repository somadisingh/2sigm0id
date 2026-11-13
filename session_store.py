"""Where live sessions are kept: always in live_sessions/ on this machine, and also in a private
GitHub repo when SESSION_REPO and SESSION_REPO_TOKEN are set.

A hosted web app (Streamlit Community Cloud) loses its disk when it restarts, so there the
private repo is the real store. The repo must be PRIVATE: the files hold real people's answers.

  SESSION_REPO        owner/name of a private repo, for example Preyansh17/risk-study-data
  SESSION_REPO_TOKEN  a fine-grained GitHub token with "Contents: read and write" on that repo only

Files go to sessions/<participant>_<method>_<time>.json in the repo.
"""

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

LOCAL_DIR = Path(__file__).resolve().parent / "live_sessions"
REMOTE_DIR = "sessions"
API = "https://api.github.com"
_shas = {}   # file name -> blob sha of the last version written (needed to update a file)


def _remote():
    repo, token = os.environ.get("SESSION_REPO"), os.environ.get("SESSION_REPO_TOKEN")
    return (repo, token) if repo and token else None


def _call(method, url, token, body=None):
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}",
                                          "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28",
                                          "User-Agent": "risk-profile-study"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read() or b"null")


def check_remote():
    """Raise if a repo is configured but can't be used, or is public. Returns the repo or None."""
    remote = _remote()
    if not remote:
        return None
    repo, token = remote
    info = _call("GET", f"{API}/repos/{repo}", token)
    if not info.get("private"):
        raise RuntimeError(f"{repo} is public. Session files hold real people's answers: use a private repo.")
    return repo


def save(name, data):
    """Write one session file locally and, if configured, to the private repo. Returns False if
    the repo write failed. The whole file is written each time, so the next save catches up."""
    LOCAL_DIR.mkdir(exist_ok=True)
    text = json.dumps(data, indent=1)
    path = LOCAL_DIR / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text)
    tmp.replace(path)
    remote = _remote()
    if not remote:
        return True
    repo, token = remote
    url = f"{API}/repos/{repo}/contents/{REMOTE_DIR}/{name}"
    body = {"message": f"session {name}", "content": base64.b64encode(text.encode()).decode()}
    for attempt in range(2):
        if name in _shas:
            body["sha"] = _shas[name]
        try:
            _shas[name] = _call("PUT", url, token, body)["content"]["sha"]
            return True
        except urllib.error.HTTPError as e:
            if e.code in (409, 422) and attempt == 0:   # stale or unknown sha: read it, try again
                try:
                    _shas[name] = _call("GET", url, token)["sha"]
                    continue
                except (urllib.error.URLError, OSError, KeyError, ValueError):
                    pass
            print(f"session_store: could not save {name} to {repo}: {e}")
            return False
        except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
            print(f"session_store: could not save {name} to {repo}: {e}")
            return False
    return False


def load_all(prefix):
    """All saved sessions whose file name starts with prefix (from the repo if configured)."""
    remote = _remote()
    if not remote:
        out = []
        for f in sorted(LOCAL_DIR.glob(f"{prefix}*.json")):
            try:
                out.append(json.loads(f.read_text()))
            except (OSError, ValueError):
                pass
        return out
    repo, token = remote
    try:
        listing = _call("GET", f"{API}/repos/{repo}/contents/{REMOTE_DIR}", token)
    except urllib.error.HTTPError as e:
        if e.code == 404:   # no session saved yet
            return []
        raise
    out = []
    for f in sorted(listing, key=lambda f: f["name"]):
        if f["name"].startswith(prefix) and f["name"].endswith(".json"):
            blob = _call("GET", f"{API}/repos/{repo}/contents/{REMOTE_DIR}/{f['name']}", token)
            _shas[f["name"]] = blob["sha"]
            out.append(json.loads(base64.b64decode(blob["content"])))
    return out
