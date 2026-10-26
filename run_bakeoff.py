"""Model bake-off for the adaptive risk-profiling interviewer.

Commands (run from this folder):
  python run_bakeoff.py list-models            # exact model IDs on your Baseten account
  python run_bakeoff.py check                  # does each model + thinking setting work?
  python run_bakeoff.py stage1                 # compare interviewers
  python run_bakeoff.py stage2 --interviewer glm-5.3   # compare simulated users
  python run_bakeoff.py prompts --interviewer glm-5.3 --user deepseek-v4-flash-0731 --user-setting off
                                               # compare interviewer prompt versions
Add --mock to any stage to test the pipeline without an API key or cost.
Results go to results/*.jsonl; score them with score.py.
"""

import argparse
import difflib
import json
import os
import random
import sys
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import config as C
import prompts as P
from llm import LLM, extract_json, strip_think, validate_interviewer

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


# ---------------------------------------------------------------- setup

def load_env():
    env_file = HERE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def make_llm(mock):
    if mock:
        return LLM(C.MODELS, C.REASONING_SETTINGS, mock=True)
    load_env()
    key = os.environ.get("BASETEN_API_KEY")
    if not key:
        sys.exit("BASETEN_API_KEY is not set. Put it in a .env file in this folder "
                 "(see .env.example) or export it in your shell.")
    base_url = os.environ.get("BASETEN_BASE_URL", C.BASE_URL)  # override only for local testing
    return LLM(C.MODELS, C.REASONING_SETTINGS, base_url=base_url, api_key=key)


def load_personas():
    personas = json.loads((HERE / "personas.json").read_text())
    for p in personas:
        gt = p["ground_truth"]
        expected = min(P.band(gt[d]) for d in ("capacity", "willingness", "behavioral"))
        if expected != gt["final_band"]:
            sys.exit(f"{p['id']}: final_band {gt['final_band']} doesn't match the "
                     f"lowest-of-three rule ({expected}).")
    return personas


def check_ids(llm, keys):
    """Warn about configured model IDs that don't exist on the account."""
    if llm.mock:
        return
    try:
        available = {m.id for m in llm.client.models.list()}
    except Exception as e:  # noqa: BLE001
        print(f"(Couldn't list models to verify IDs: {e}. Continuing.)")
        return
    missing = [k for k in keys if C.MODELS[k]["id"] not in available]
    if missing:
        print("These model IDs in config.py were not found on your Baseten account:")
        for k in missing:
            close = difflib.get_close_matches(C.MODELS[k]["id"], list(available), n=3, cutoff=0.3)
            print(f"  {k}: {C.MODELS[k]['id']}   closest: {close or 'none'}")
        sys.exit("Fix the IDs in config.py (run `python run_bakeoff.py list-models`), then rerun.")


# ---------------------------------------------------------------- one interview

def draw_noise(rng, persona, turn_idx):
    n = persona["noise"]
    kinds = []
    if rng.random() < n["vague_rate"]:
        kinds.append("vague")
    if turn_idx >= 2 and rng.random() < n["contradiction_rate"]:
        kinds.append("contradiction")
    elif rng.random() < n["flip_prob"]:
        kinds.append("flip")
    if rng.random() < n["acquiescence"]:
        kinds.append("acquiescence")
    return kinds


def interviewer_step(llm, key, setting, msgs):
    """One interviewer turn, with one retry if the reply isn't valid JSON."""
    calls = []
    r = llm.chat(key, msgs, setting, C.INTERVIEWER_MAX_TOKENS, C.INTERVIEWER_TEMPERATURE)
    out = validate_interviewer(extract_json(r["text"]))
    calls.append({**_call_log(r), "valid": out is not None, "retry": False})
    if out is not None:
        msgs.append({"role": "assistant", "content": json.dumps(out)})
        return out, calls
    # retry once, then drop the failed exchange so the history stays clean
    msgs.append({"role": "assistant", "content": r["text"] or "(empty)"})
    msgs.append({"role": "user", "content": P.RETRY_MESSAGE})
    r2 = llm.chat(key, msgs, setting, C.INTERVIEWER_MAX_TOKENS, C.INTERVIEWER_TEMPERATURE)
    out = validate_interviewer(extract_json(r2["text"]))
    calls.append({**_call_log(r2), "valid": out is not None, "retry": True})
    del msgs[-2:]
    if out is not None:
        msgs.append({"role": "assistant", "content": json.dumps(out)})
    return out, calls


def _call_log(r):
    return {"usage": r["usage"], "latency": round(r["latency"], 3), "finish": r["finish"]}


def run_interview(llm, interviewer, i_setting, user, u_setting, persona, repeat, probes,
                  prompt=P.INTERVIEWER_PROMPT):
    # Same seed for every model -> every interviewer faces the same noise schedule.
    rng = random.Random(zlib.crc32(f"{persona['id']}|{repeat}".encode()))
    budget = C.BUDGET
    i_msgs = [{"role": "system", "content": P.INTERVIEWER_PROMPTS[prompt]},
              {"role": "user", "content": P.START_MESSAGE.format(left=budget)}]
    u_msgs = [{"role": "system", "content": P.build_user_system(persona)}]
    turns, i_calls, u_calls = [], [], []
    last_valid, asked, invalid_turns, early_stop = None, 0, 0, False
    said = set()  # persona facts the user has already stated clearly
    t_start = time.monotonic()

    while True:
        out, calls = interviewer_step(llm, interviewer, i_setting, i_msgs)
        i_calls += calls
        if turns:  # flags raised right after the previous answer
            turns[-1]["flags_after"] = out["flags"] if out else None
        if out is None:
            invalid_turns += 1
            break  # can't continue without a question; score the last valid profile
        last_valid = out
        left = budget - asked
        if left == 0:
            break
        if out["question"] is None:
            early_stop = True
            break

        noise = draw_noise(rng, persona, asked)
        target = None
        if "contradiction" in noise:
            if said:  # separate rng so the main noise schedule stays identical across runs
                fact_rng = random.Random(zlib.crc32(f"{persona['id']}|{repeat}|{asked}".encode()))
                fact = fact_rng.choice(sorted(said))
                target = {"fact": fact, "wrong": P.wrong_fact(persona, fact)}
            else:
                noise.remove("contradiction")  # nothing stated yet that could be contradicted
        wrong = target["wrong"] if target else None
        u_msgs.append({"role": "user", "content": out["question"] + P.private_note(noise, wrong)})
        ur = llm.chat(user, u_msgs, u_setting, C.USER_MAX_TOKENS, C.USER_TEMPERATURE)
        u_calls.append(_call_log(ur))
        answer = strip_think(ur["text"]) or "(no answer)"
        u_msgs[-1]["content"] = out["question"]  # don't keep private notes in the history
        u_msgs.append({"role": "assistant", "content": answer})
        asked += 1
        if not {"vague", "flip", "contradiction"} & set(noise):
            said |= P.facts_asked(out["question"])
        turns.append({"q": out["question"], "a": answer, "noise": noise,
                      "contradiction_target": target,
                      "profile_before": out["profile"], "confidence_before": out["confidence"]})
        left = budget - asked
        msg = P.ANSWER_MESSAGE.format(answer=answer, left=left)
        i_msgs.append({"role": "user", "content": msg + (P.FINAL_SUFFIX if left == 0 else "")})

    probe_results = []
    if probes:
        for pr in P.PROBES:
            u_msgs.append({"role": "user", "content": pr["q"]})
            ur = llm.chat(user, u_msgs, u_setting, C.USER_MAX_TOKENS, C.USER_TEMPERATURE)
            u_calls.append({**_call_log(ur), "probe": True})
            ans = strip_think(ur["text"])
            u_msgs.append({"role": "assistant", "content": ans or "(no answer)"})
            probe_results.append({"field": pr["field"], "answer": ans})

    return {
        "interviewer": interviewer, "interviewer_setting": i_setting, "prompt": prompt,
        "noise_version": 2,  # 2 = contradictions name a fact already stated
        "user": user, "user_setting": u_setting,
        "persona_id": persona["id"], "repeat": repeat, "budget": budget,
        "truth": persona["ground_truth"], "persona": persona,
        "final_profile": last_valid["profile"] if last_valid else None,
        "final_flags": last_valid["flags"] if last_valid else None,
        "questions_asked": asked, "early_stop": early_stop,
        "aborted_invalid": invalid_turns > 0,
        "turns": turns, "interviewer_calls": i_calls, "user_calls": u_calls,
        "probes": probe_results, "seconds": round(time.monotonic() - t_start, 1),
    }


# ---------------------------------------------------------------- stages

def run_jobs(llm, jobs, out_path):
    """Run interviews in parallel; skip ones already in the results file (resume)."""
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                if not rec.get("error"):
                    done.add(rec["job_key"])
    todo = [j for j in jobs if j["job_key"] not in done]
    print(f"{len(jobs)} interviews planned, {len(jobs) - len(todo)} already done, "
          f"{len(todo)} to run -> {out_path.name}")
    lock = threading.Lock()

    def work(j):
        try:
            rec = run_interview(llm, j["interviewer"], j["i_setting"], j["user"], j["u_setting"],
                                j["persona"], j["repeat"], j["probes"], j["prompt"])
        except Exception as e:  # noqa: BLE001 - keep the run going, log the failure
            rec = {k: j[k] for k in ("interviewer", "user", "repeat")}
            rec.update(interviewer_setting=j["i_setting"], user_setting=j["u_setting"],
                       persona_id=j["persona"]["id"], error=f"{type(e).__name__}: {e}")
        rec["job_key"] = j["job_key"]
        rec["stage"] = j["stage"]
        with lock:
            with out_path.open("a") as f:
                f.write(json.dumps(rec) + "\n")
        return rec

    finished = 0
    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as pool:
        futures = [pool.submit(work, j) for j in todo]
        for fut in as_completed(futures):
            rec = fut.result()
            finished += 1
            status = f"ERROR {rec['error'][:120]}" if rec.get("error") else (
                f"{rec['questions_asked']} questions, {rec['seconds']}s")
            print(f"[{finished}/{len(todo)}] {rec['interviewer']} | {rec['user']}"
                  f"({rec['user_setting']}) | {rec['persona_id']}: {status}")
    print("Done. Next: python score.py", out_path.relative_to(HERE))


def job(stage, interviewer, i_setting, user, u_setting, persona, repeat, probes,
        prompt=P.INTERVIEWER_PROMPT):
    key = f"{stage}|{interviewer}|{i_setting}|{user}|{u_setting}|{persona['id']}|{repeat}"
    if prompt != "v1":  # keeps v1 keys identical to earlier runs
        key += f"|{prompt}"
    return dict(stage=stage, interviewer=interviewer, i_setting=i_setting, user=user,
                u_setting=u_setting, persona=persona, repeat=repeat, probes=probes,
                prompt=prompt, job_key=key)


def stage1(args):
    llm = make_llm(args.mock)
    personas = load_personas()
    user = C.STAGE1_USER
    clash = [k for k in C.STAGE1_INTERVIEWERS if C.MODELS[k]["family"] == C.MODELS[user]["family"]]
    if clash:
        sys.exit(f"Stage 1 user {user} is from the same company as: {clash}. Pick another user.")
    check_ids(llm, C.STAGE1_INTERVIEWERS + [user])
    jobs = [job("stage1", iv, C.STAGE1_INTERVIEWER_REASONING, user, C.STAGE1_USER_REASONING,
                p, r, False)
            for iv in C.STAGE1_INTERVIEWERS for p in personas for r in range(args.repeats)]
    run_jobs(llm, jobs, RESULTS / ("stage1_mock.jsonl" if args.mock else "stage1.jsonl"))


def stage2(args):
    llm = make_llm(args.mock)
    personas = load_personas()
    iv = args.interviewer
    if iv not in C.MODELS:
        sys.exit(f"Unknown interviewer '{iv}'. Options: {', '.join(C.MODELS)}")
    fam = C.MODELS[iv]["family"]
    users = [u for u in C.STAGE2_USER_CANDIDATES if C.MODELS[u]["family"] != fam]
    skipped = [u for u in C.STAGE2_USER_CANDIDATES if u not in users]
    if skipped:
        print(f"Skipping {skipped}: same company as the interviewer ({fam}).")
    check_ids(llm, [iv] + users)
    jobs = [job("stage2", iv, C.STAGE2_INTERVIEWER_REASONING, u, s, p, r, True)
            for u in users for s in C.STAGE2_USER_REASONING
            for p in personas for r in range(args.repeats)]
    run_jobs(llm, jobs, RESULTS / ("stage2_mock.jsonl" if args.mock else "stage2.jsonl"))


def prompts(args):
    """Same interviewer and user, every interviewer prompt version, same noise schedule."""
    llm = make_llm(args.mock)
    personas = load_personas()
    iv, user = args.interviewer, args.user
    for k in (iv, user):
        if k not in C.MODELS:
            sys.exit(f"Unknown model '{k}'. Options: {', '.join(C.MODELS)}")
    if C.MODELS[iv]["family"] == C.MODELS[user]["family"]:
        sys.exit(f"{iv} and {user} are from the same company. Pick another user.")
    check_ids(llm, [iv, user])
    jobs = [job("prompts", iv, C.STAGE2_INTERVIEWER_REASONING, user, args.user_setting,
                p, r, False, v)
            for v in args.versions for p in personas for r in range(args.repeats)]
    name = args.out or ("prompts_mock.jsonl" if args.mock else "prompts.jsonl")
    run_jobs(llm, jobs, RESULTS / name)


def list_models(args):
    llm = make_llm(False)
    ids = sorted(m.id for m in llm.client.models.list())
    print("Models on your Baseten account:")
    for i in ids:
        print("  ", i)
    print("\nconfig.py check:")
    for k, m in C.MODELS.items():
        ok = "OK " if m["id"] in ids else "MISSING"
        close = "" if m["id"] in ids else f"  closest: {difflib.get_close_matches(m['id'], ids, n=3, cutoff=0.3)}"
        print(f"  {ok} {k:24} {m['id']}{close}")


def check(args):
    """Tiny request per model and thinking setting: does it work, and is thinking really off?"""
    llm = make_llm(args.mock)
    keys = args.models or list(C.MODELS)
    msgs = [{"role": "user", "content": "Reply with just the word OK."}]
    print(f"{'model':24} {'setting':8} {'result':8} {'secs':>5} {'out':>6} {'think':>6}  reply")
    for k in keys:
        for s in ("off", "low", "default"):
            try:
                r = llm.chat(k, msgs, s, 600, None)
                u = r["usage"]
                print(f"{k:24} {s:8} {'ok':8} {r['latency']:5.1f} {u['out']:6} {u['reasoning']:6}  "
                      f"{strip_think(r['text'])[:40]!r}")
            except Exception as e:  # noqa: BLE001
                print(f"{k:24} {s:8} {'FAILED':8} {'':5} {'':6} {'':6}  {str(e)[:90]}")
    print("\nIf 'off' still shows thinking tokens, that model ignores the off switch: "
          "note it, and treat its 'off' and 'low' runs as the same setting.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list-models").set_defaults(fn=list_models)
    c = sub.add_parser("check")
    c.add_argument("--models", nargs="*", help="model keys from config.py (default: all)")
    c.add_argument("--mock", action="store_true")
    c.set_defaults(fn=check)
    s1 = sub.add_parser("stage1")
    s1.add_argument("--repeats", type=int, default=1)
    s1.add_argument("--mock", action="store_true")
    s1.set_defaults(fn=stage1)
    s2 = sub.add_parser("stage2")
    s2.add_argument("--interviewer", required=True, help="winning interviewer key from stage 1")
    s2.add_argument("--repeats", type=int, default=1)
    s2.add_argument("--mock", action="store_true")
    s2.set_defaults(fn=stage2)
    pr = sub.add_parser("prompts")
    pr.add_argument("--interviewer", required=True)
    pr.add_argument("--user", required=True, help="simulated-user key, e.g. the stage 2 winner")
    pr.add_argument("--user-setting", default="off", choices=["off", "low", "default"])
    pr.add_argument("--versions", nargs="*", default=list(P.INTERVIEWER_PROMPTS))
    pr.add_argument("--repeats", type=int, default=3)
    pr.add_argument("--out", help="results file name, e.g. to rerun the same jobs fresh")
    pr.add_argument("--mock", action="store_true")
    pr.set_defaults(fn=prompts)
    args = ap.parse_args()
    RESULTS.mkdir(exist_ok=True)
    args.fn(args)


if __name__ == "__main__":
    main()
