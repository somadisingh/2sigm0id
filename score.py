"""Score bake-off and experiment results.

  python score.py results/stage1.jsonl
  python score.py results/stage2.jsonl
  python score.py results/experiment.jsonl
  python score.py FILE --by-persona        # add a per-test-user error table
  python score.py FILE --truth formula     # re-score old runs with capacity from capacity.py

Prints quality and cost tables, and writes <name>_summary.csv and
<name>_summary.md next to the results file.
"""

import csv
import json
import random
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import argparse

import config as C
from prompts import VERBOSITY_WORD_LIMIT, band

DIMS = ("capacity", "willingness", "behavioral")
METHOD_NAMES = {"A": "fixed form", "B": "scripted interview", "C": "adaptive form",
                "D": "adaptive interviewer", "C0": "adaptive form, old rule",
                "D0": "adaptive interviewer, LLM only", "DR": "adaptive interviewer + retrieval",
                "DP": "adaptive interviewer + token probabilities"}
FLAGGING = ("D", "DR", "DP", "D0")          # methods that raise contradiction flags
ENGINE_CHOOSES = ("C", "D", "DR", "DP", "D0")   # methods with a stop point (would stop)
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def cost(usage, model_key):
    m = C.MODELS[model_key]
    return (usage["in"] * m["price_in"] + usage["out"] * m["price_out"]) / 1e6


def mean(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None


def bootstrap_ci(xs, n=2000, seed=0):
    if len(xs) < 2:
        return (None, None)
    rng = random.Random(seed)
    means = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def has_flag(flags, kind):
    return any(str(f).lower().startswith(kind) for f in (flags or []))


def probe_ok(field, answer, persona):
    truth = persona["experience"]["past_loss_reaction"] if field == "past_loss_reaction" \
        else persona["finances"][field]
    answer = (answer or "").lower()
    if field == "past_loss_reaction":
        found = re.findall(r"\b(sold|held|none)\b", answer)
        return bool(found) and found[0] == truth
    nums = NUM_RE.findall(answer)
    if not nums:
        return False
    x = float(nums[0])
    if field == "dependents":
        return x == truth
    if field == "emergency_fund_months":
        return abs(x - truth) <= max(1.0, 0.5 * truth)
    return abs(x - truth) <= max(2.0, 0.3 * truth)  # horizon_yrs


def summarize(recs):
    ok = [r for r in recs if not r.get("error")]
    errs = len(recs) - len(ok)
    scored = [r for r in ok if r.get("final_profile")]
    s = {"n": len(recs), "errors": errs, "no_profile": len(ok) - len(scored)}

    per_interview = [mean([abs(r["final_profile"][d] - r["truth"][d]) for d in DIMS]) for r in scored]
    s["avg_error"] = mean(per_interview)
    s["ci_low"], s["ci_high"] = bootstrap_ci(per_interview)
    for d in DIMS:
        s[f"err_{d}"] = mean([abs(r["final_profile"][d] - r["truth"][d]) for r in scored])
    pred_bands = [min(band(r["final_profile"][d]) for d in DIMS) for r in scored]
    true_bands = [r["truth"]["final_band"] for r in scored]
    s["band_exact"] = mean([p == t for p, t in zip(pred_bands, true_bands)]) if scored else None
    s["band_within1"] = mean([abs(p - t) <= 1 for p, t in zip(pred_bands, true_bands)]) if scored else None

    first_calls = [c for r in ok for c in r["interviewer_calls"] if not c.get("retry")]
    s["valid_json"] = mean([c["valid"] for c in first_calls if "valid" in c]) if first_calls else None
    s["total_cost"] = mean([sum(cost(c["usage"], c.get("model") or r.get("interviewer"))
                                for c in r["interviewer_calls"])
                            + sum(cost(c["usage"], r["user"]) for c in r["user_calls"]) for r in ok])

    # Per completed profile. "System" = calls that build the profile (D's interviewer, B's
    # answer mapper); A and C make none. Simulated-user calls are counted separately.
    s["sys_calls"] = mean([len(r["interviewer_calls"]) for r in scored])
    for k in ("in", "out", "reasoning"):
        s[f"sys_tokens_{k}"] = mean([sum(c["usage"][k] for c in r["interviewer_calls"]) for r in scored])
    s["sys_cost"] = mean([sum(cost(c["usage"], c.get("model") or r.get("interviewer"))
                              for c in r["interviewer_calls"]) for r in scored])
    s["sys_secs"] = mean([sum(c["latency"] for c in r["interviewer_calls"]) for r in scored])
    waits = sorted(t["system_latency"] for r in scored for t in r["turns"] if "system_latency" in t)
    s["sys_secs_per_turn"] = mean(waits)
    s["sys_secs_turn_p95"] = waits[int(0.95 * (len(waits) - 1))] if waits else None
    s["user_calls"] = mean([len(r["user_calls"]) for r in scored])
    s["user_cost"] = mean([sum(cost(c["usage"], r["user"]) for c in r["user_calls"]) for r in scored])

    mm = [r for r in ok if r["truth"]["mismatch_type"] != "none"]
    s["mismatch_caught"] = mean([
        has_flag(r.get("final_flags"), "mismatch")
        or any(has_flag(t.get("flags_after"), "mismatch") for t in r["turns"]) for r in mm]) if mm else None
    contra_turns = [t for r in ok for t in r["turns"] if "contradiction" in t["noise"]]
    s["contradiction_turns"] = len(contra_turns)
    s["contradiction_caught"] = mean([has_flag(t.get("flags_after"), "contradiction")
                                      for t in contra_turns]) if contra_turns else None
    clean = [r for r in ok if r["persona"]["noise"]["contradiction_rate"] == 0
             and r["persona"]["noise"]["flip_prob"] == 0]
    s["false_contra_per_interview"] = mean([
        sum(has_flag(t.get("flags_after"), "contradiction") for t in r["turns"]) for r in clean]) if clean else None

    # Did a contradiction pull the estimate off course, and did it come back by the end?
    # (noise version 2 records which fact each contradiction targeted)
    pulled, recovered = [], []
    for r in scored:
        for i, t in enumerate(r["turns"]):
            tgt = t.get("contradiction_target")
            if not tgt or "contradiction" not in t["noise"] or not t.get("profile_before"):
                continue
            dim = "behavioral" if tgt["fact"] == "past_loss_reaction" else "capacity"
            truth = r["truth"][dim]
            before = t["profile_before"][dim]
            after = (r["turns"][i + 1]["profile_before"][dim] if i + 1 < len(r["turns"])
                     else r["final_profile"][dim])
            pulled.append(abs(after - truth) - abs(before - truth))
            recovered.append(abs(r["final_profile"][dim] - truth) <= abs(before - truth) + 0.05)
    s["contra_targeted"] = len(recovered)
    s["contra_pulled"] = mean(pulled)
    s["contra_recovered"] = mean(recovered) if recovered else None

    s["questions"] = mean([r["questions_asked"] for r in ok])
    # main experiment: D keeps asking to the full budget; this is where it would have stopped
    full = [r for r in ok if r.get("full_budget")]
    s["would_stop_share"] = mean([r["would_stop_at"] is not None for r in full]) if full else None
    s["would_stop_at"] = mean([r["would_stop_at"] for r in full if r["would_stop_at"] is not None])
    s["stopped_anyway"] = sum(r["early_stop"] for r in full) if full else None
    s["early_stop"] = mean([r["early_stop"] for r in ok]) if ok else None
    s["seconds"] = mean([r["seconds"] for r in ok])

    iv = next((r.get("interviewer") for r in ok if r.get("interviewer")), None)
    s["iv_cost"] = mean([sum(cost(c["usage"], iv) for c in r["interviewer_calls"]) for r in ok])
    s["iv_out_tokens"] = mean([sum(c["usage"]["out"] for c in r["interviewer_calls"]) for r in ok])
    s["iv_think_tokens"] = mean([sum(c["usage"]["reasoning"] for c in r["interviewer_calls"]) for r in ok])
    calls_per = mean([len(r["interviewer_calls"]) for r in ok])
    s["full_iv_cost"] = s["iv_cost"] * C.FULL_RUN_INTERVIEWS if s["iv_cost"] is not None else None
    s["full_iv_hours"] = (C.FULL_RUN_INTERVIEWS * calls_per / C.MODELS[iv]["rpm"] / 60) if calls_per else None

    user = ok[0]["user"] if ok else recs[0]["user"]
    answer_calls = [c for r in ok for c in r["user_calls"] if not c.get("probe")]
    s["user_cost_per_answer"] = mean([cost(c["usage"], user) for c in answer_calls])
    s["full_user_cost"] = (s["user_cost_per_answer"] * C.FULL_RUN_USER_ANSWERS
                           if s["user_cost_per_answer"] is not None else None)
    s["full_user_hours"] = C.FULL_RUN_USER_ANSWERS / C.MODELS[user]["rpm"] / 60

    words = [(len(t["a"].split()), r["persona"]["style"]["verbosity"]) for r in ok for t in r["turns"]]
    s["words_per_answer"] = mean([w for w, _ in words])
    s["verbosity_ok"] = mean([w <= VERBOSITY_WORD_LIMIT[v] for w, v in words]) if words else None
    probes = [(p, r["persona"]) for r in ok for p in r.get("probes", [])]
    s["probe_accuracy"] = mean([probe_ok(p["field"], p["answer"], per) for p, per in probes]) if probes else None
    return s


def fmt(v, kind):
    if v is None:
        return "-"
    return {"pct": f"{v * 100:.0f}%", "err": f"{v:.3f}", "usd": f"${v:,.3f}" if v < 1 else f"${v:,.2f}",
            "usd4": f"${v:.4f}",
            "num": f"{v:.1f}", "int": f"{v:.0f}", "hrs": f"{v:.1f} h"}[kind]


def table(rows, cols):
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, (h, _) in enumerate(cols)]
    line = "  ".join(h.ljust(w) for (h, _), w in zip(cols, widths))
    out = [line, "-" * len(line)]
    out += ["  ".join(c.ljust(w) for c, w in zip(r, widths)) for r in rows]
    return "\n".join(out)


def apply_formula_truth(recs):
    """Replace each record's true capacity with the capacity formula's value."""
    from capacity import capacity_from_facts
    for r in recs:
        if r.get("error") or "persona" not in r:
            continue
        t = dict(r["truth"])
        t["capacity"], _ = capacity_from_facts(r["persona"]["finances"])
        bands = [band(t[d]) for d in DIMS]
        t["final_band"] = min(bands)
        t["mismatch_type"] = "bands 2+ apart" if max(bands) - min(bands) >= 2 else "none"
        r["truth"] = t


def persona_table(groups, order, label):
    rows = []
    for k in order:
        by = defaultdict(list)
        for r in groups[k]:
            if not r.get("error") and r.get("final_profile"):
                by[r["persona_id"]].append(r)
        for pid in sorted(by):
            rs = by[pid]
            signed = [mean([r["final_profile"][d] - r["truth"][d] for r in rs]) for d in DIMS]
            given = " ".join(str(min(band(r["final_profile"][d]) for d in DIMS)) for r in rs)
            rows.append([label(k), pid, str(len(rs))] + [f"{x:+.2f}" for x in signed]
                        + [f"{given} / {rs[0]['truth']['final_band']}"])
    cols = [("group", None), ("test user", None), ("n", None), ("capacity", None),
            ("willingness", None), ("behavior", None), ("bands given / true", None)]
    return ("PER TEST USER (average signed error: + means rated riskier than the truth)\n"
            + table(rows, cols))


def interview_error(r):
    return mean([abs(r["final_profile"][d] - r["truth"][d]) for d in DIMS])


def noise_level(p):
    """clean / moderate / heavy: from the test-user ID, else from its noise rates."""
    tail = p["id"].rsplit("-", 1)[-1]
    if tail in ("clean", "moderate", "heavy"):
        return tail
    n = p["noise"]
    total = n["vague_rate"] + n["flip_prob"] + n["contradiction_rate"]
    return "clean" if total <= 0.05 else "moderate" if total <= 0.4 else "heavy"


def paired_table(groups, order, label, base="A"):
    """Each method against the base method on the same test users and repeats: the
    difference in avg error (negative = better than the base) with a paired 95% range."""
    rows = []
    for k in order:
        if k[0] == base or (base, k[1]) not in groups:
            continue
        ref = {(r["persona_id"], r["repeat"]): r for r in groups[(base, k[1])]
               if not r.get("error") and r.get("final_profile")}
        diffs, band_diffs = [], []
        for r in groups[k]:
            b = ref.get((r["persona_id"], r["repeat"]))
            if b is None or r.get("error") or not r.get("final_profile"):
                continue
            diffs.append(interview_error(r) - interview_error(b))
            exact = lambda x: min(band(x["final_profile"][d]) for d in DIMS) == x["truth"]["final_band"]  # noqa: E731
            band_diffs.append(exact(r) - exact(b))
        if not diffs:
            continue
        lo, hi = bootstrap_ci(diffs)
        rows.append([label(k), str(len(diffs)), f"{mean(diffs):+.3f}",
                     "-" if lo is None else f"{lo:+.3f} to {hi:+.3f}",
                     f"{100 * mean(band_diffs):+.0f} points"])
    cols = [("method and budget", None), ("pairs", None), (f"avg error vs {base}", None),
            ("95% range", None), ("band exact vs " + base, None)]
    return (f"PAIRED AGAINST {base} (same test users; negative error = better than {base}; "
            "a range that excludes 0 is a real difference)\n" + table(rows, cols))


def group_table(groups, order, label):
    """Avg error by true final band, by mismatch, and by noise level."""
    cuts = ([(f"band {b}", lambda r, b=b: r["truth"]["final_band"] == b) for b in range(1, 6)]
            + [("no mismatch", lambda r: r["truth"]["mismatch_type"] == "none"),
               ("mismatch", lambda r: r["truth"]["mismatch_type"] != "none")]
            + [(lvl, lambda r, lvl=lvl: noise_level(r["persona"]) == lvl)
               for lvl in ("clean", "moderate", "heavy")])
    rows = []
    for k in order:
        ok = [r for r in groups[k] if not r.get("error") and r.get("final_profile")]
        cells = []
        for _, f in cuts:
            xs = [interview_error(r) for r in ok if f(r)]
            cells.append(f"{mean(xs):.3f} ({len(xs)})" if xs else "-")
        rows.append([label(k)] + cells)
    cols = [("method and budget", None)] + [(name, None) for name, _ in cuts]
    return "AVG ERROR BY GROUP (number of runs in brackets)\n" + table(rows, cols)


def cost_chart(summaries, path):
    """Avg error vs. system cost and system time per completed profile, one point per method+budget."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("(Skipped the cost chart: pip install matplotlib)")
        return
    colors = {"A": "#4C78A8", "B": "#F58518", "C": "#54A24B", "D": "#B279A2",
              "C0": "#9FD08F", "D0": "#D9B8D0", "DR": "#E45756", "DP": "#72B7B2"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, key, xlabel in ((axes[0], "sys_cost", "System $ per completed profile"),
                            (axes[1], "sys_secs", "System LLM seconds per completed profile")):
        for (m, b), s in sorted(summaries.items()):
            if s["avg_error"] is None:
                continue
            x, y = s[key] or 0.0, s["avg_error"]
            yerr = ([[y - s["ci_low"]], [s["ci_high"] - y]] if s["ci_low"] is not None else None)
            ax.errorbar(x, y, yerr=yerr, fmt="o", color=colors.get(m, "gray"), capsize=3,
                        label=f"{m} - {METHOD_NAMES.get(m, m)}")
            # A and C both sit at zero cost: label A on the left and C on the right so they can't collide
            left = m == "A"
            ax.annotate(f"{m}{b}", (x, y), textcoords="offset points", fontsize=8,
                        xytext=(-6, -3) if left else (6, -3), ha="right" if left else "left")
        ax.set_xlabel(xlabel)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Avg error (lower is better)")
    handles, labels = axes[0].get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    axes[1].legend(uniq.values(), uniq.keys(), fontsize=8, loc="best")
    fig.suptitle("Accuracy vs. cost per completed profile (labels: method + question budget)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {Path(path).name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--by-persona", action="store_true", help="add a per-test-user error table")
    ap.add_argument("--by-group", action="store_true",
                    help="add avg error by true band, mismatch and noise level (experiment only)")
    ap.add_argument("--truth", choices=["file", "formula"], default="file",
                    help="'formula' recomputes true capacity with capacity.py")
    args = ap.parse_args()
    path = Path(args.file)
    recs = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not recs:
        sys.exit("No results yet.")
    if args.truth == "formula":
        apply_formula_truth(recs)
    stage = recs[0]["stage"]
    groups = defaultdict(list)
    for r in recs:
        if stage == "stage1":
            key = (r["interviewer"], r["interviewer_setting"])
        elif stage == "prompts":
            key = (r["interviewer"], f"{r['interviewer_setting']}, prompt {r.get('prompt', 'v1')}")
        elif stage == "experiment":
            key = (r["method"], r["budget"])
        else:
            key = (r["user"], r["user_setting"])
        groups[key].append(r)
    summaries = {k: summarize(v) for k, v in groups.items()}
    order = sorted(summaries, key=lambda k: (summaries[k]["avg_error"] is None, summaries[k]["avg_error"] or 0))
    if stage == "experiment":
        order = sorted(summaries, key=lambda k: (k[1], k[0]))   # by budget, then method

    def label(k):
        if stage == "experiment":
            return f"{k[0]} - {METHOD_NAMES.get(k[0], k[0])}, {k[1]} questions"
        return f"{k[0]} ({k[1]})"

    def ci(s):
        return "-" if s["ci_low"] is None else f"{s['ci_low']:.2f}-{s['ci_high']:.2f}"

    blocks = []
    if stage in ("stage1", "prompts"):
        q_cols = [("interviewer", None), ("interviews", None), ("avg error", None), ("95% range", None),
                  ("band exact", None), ("within 1", None), ("valid JSON", None),
                  ("mismatch caught", None), ("contradiction caught", None), ("recovered", None),
                  ("false contra/interview", None), ("questions", None), ("errors", None)]
        q_rows = [[label(k), str(s["n"]), fmt(s["avg_error"], "err"), ci(s), fmt(s["band_exact"], "pct"),
                   fmt(s["band_within1"], "pct"), fmt(s["valid_json"], "pct"),
                   fmt(s["mismatch_caught"], "pct"),
                   f"{fmt(s['contradiction_caught'], 'pct')} of {s['contradiction_turns']}",
                   f"{fmt(s['contra_recovered'], 'pct')} of {s['contra_targeted']}",
                   fmt(s["false_contra_per_interview"], "num"), fmt(s["questions"], "num"),
                   str(s["errors"] + s["no_profile"])] for k, s in ((k, summaries[k]) for k in order)]
        c_cols = [("interviewer", None), ("$/interview", None), ("output tokens", None),
                  ("thinking tokens", None), ("secs/interview", None), ("rate limit", None),
                  ("full run $", None), ("full run time", None)]
        c_rows = [[label(k), fmt(s["iv_cost"], "usd"), fmt(s["iv_out_tokens"], "int"),
                   fmt(s["iv_think_tokens"], "int"), fmt(s["seconds"], "num"),
                   f"{C.MODELS[k[0]]['rpm']}/min", fmt(s["full_iv_cost"], "usd"), fmt(s["full_iv_hours"], "hrs")]
                  for k, s in ((k, summaries[k]) for k in order)]
    elif stage == "experiment":
        q_cols = [("method and budget", None), ("runs", None), ("avg error", None), ("95% range", None),
                  ("capacity", None), ("willingness", None), ("behavior", None),
                  ("band exact", None), ("within 1", None), ("mismatch caught", None),
                  ("contradiction caught", None), ("recovered", None), ("would stop", None),
                  ("errors", None)]

        def would_stop(s):
            if s["would_stop_share"] is None:
                return "-"
            at = f" at q{s['would_stop_at']:.1f}" if s["would_stop_at"] is not None else ""
            anyway = f", {s['stopped_anyway']} stopped anyway" if s["stopped_anyway"] else ""
            return fmt(s["would_stop_share"], "pct") + at + anyway

        q_rows = [[label(k), str(s["n"]), fmt(s["avg_error"], "err"), ci(s),
                   fmt(s["err_capacity"], "err"), fmt(s["err_willingness"], "err"),
                   fmt(s["err_behavioral"], "err"),
                   fmt(s["band_exact"], "pct"), fmt(s["band_within1"], "pct"),
                   fmt(s["mismatch_caught"], "pct") if k[0] in ("C",) + FLAGGING else "-",
                   f"{fmt(s['contradiction_caught'], 'pct')} of {s['contradiction_turns']}" if k[0] in FLAGGING else "-",
                   f"{fmt(s['contra_recovered'], 'pct')} of {s['contra_targeted']}" if k[0] in ("B",) + FLAGGING else "-",
                   would_stop(s) if k[0] in ENGINE_CHOOSES else "-",
                   str(s["errors"] + s["no_profile"])] for k, s in ((k, summaries[k]) for k in order)]
        c_cols = [("method and budget", None), ("questions", None), ("LLM calls", None),
                  ("tokens in", None), ("tokens out", None), ("thinking", None), ("system $", None),
                  ("wait/turn s", None), ("p95 wait s", None), ("system s", None),
                  ("sim-user calls", None), ("sim-user $", None), ("wall s/run", None)]
        c_rows = [[label(k), fmt(s["questions"], "num"), fmt(s["sys_calls"], "num"),
                   fmt(s["sys_tokens_in"], "int"), fmt(s["sys_tokens_out"], "int"),
                   fmt(s["sys_tokens_reasoning"], "int"), fmt(s["sys_cost"], "usd4"),
                   fmt(s["sys_secs_per_turn"], "num"), fmt(s["sys_secs_turn_p95"], "num"),
                   fmt(s["sys_secs"], "num"), fmt(s["user_calls"], "num"),
                   fmt(s["user_cost"], "usd4"), fmt(s["seconds"], "num")]
                  for k, s in ((k, summaries[k]) for k in order)]
    else:
        q_cols = [("simulated user", None), ("interviews", None), ("avg error", None), ("95% range", None),
                  ("persona checks", None), ("length ok", None), ("words/answer", None),
                  ("contradiction caught", None), ("errors", None)]
        q_rows = [[label(k), str(s["n"]), fmt(s["avg_error"], "err"), ci(s), fmt(s["probe_accuracy"], "pct"),
                   fmt(s["verbosity_ok"], "pct"), fmt(s["words_per_answer"], "num"),
                   f"{fmt(s['contradiction_caught'], 'pct')} of {s['contradiction_turns']}",
                   str(s["errors"] + s["no_profile"])] for k, s in ((k, summaries[k]) for k in order)]
        c_cols = [("simulated user", None), ("$/answer", None), ("rate limit", None),
                  ("full run $ (users)", None), ("full run time", None)]
        c_rows = [[label(k), f"${s['user_cost_per_answer']:.5f}" if s["user_cost_per_answer"] else "-",
                   f"{C.MODELS[k[0]]['rpm']}/min", fmt(s["full_user_cost"], "usd"), fmt(s["full_user_hours"], "hrs")]
                  for k, s in ((k, summaries[k]) for k in order)]

    title = "QUALITY (lower error is better)" if stage == "experiment" else \
        "QUALITY (sorted by avg error, lower is better)"
    blocks.append(title + "\n" + table(q_rows, q_cols))
    if stage == "experiment":
        blocks.append(paired_table(groups, order, label))
        if args.by_group:
            blocks.append(group_table(groups, order, label))
    if args.by_persona:
        blocks.append(persona_table(groups, order, label))
    blocks.append(("COST AND SPEED" if stage == "experiment" else
                   "COST AND SPEED (full run = projected for the main experiment)") + "\n" + table(c_rows, c_cols))
    if args.truth == "formula":
        blocks.append("Truth: capacity recomputed with capacity.py (--truth formula).")
    spent = sum(cost(c["usage"], c.get("model") or r["interviewer"]) for r in recs if not r.get("error")
                for c in r["interviewer_calls"])
    spent += sum(cost(c["usage"], r["user"]) for r in recs if not r.get("error") for c in r["user_calls"])
    blocks.append(f"Actual spend for this file: ${spent:.2f}")
    n_personas = len({r["persona_id"] for r in recs})
    if stage != "experiment":
        blocks.append(f"Note: {n_personas} test users per model. This is a screening test: when two "
                  "models' 95% ranges overlap, treat them as tied and decide on cost, speed and "
                      "valid-JSON rate. Add --repeats 2 or more personas for a firmer answer.")
    report = "\n\n".join(blocks)
    print(report)

    stem = Path(str(path.with_suffix("")) + ("_formula" if args.truth == "formula" else ""))
    with open(f"{stem}_summary.csv", "w", newline="") as f:
        keys = list(next(iter(summaries.values())).keys())
        w = csv.writer(f)
        w.writerow(["model", "setting"] + keys)
        for k in order:
            w.writerow([k[0], k[1]] + [summaries[k][x] for x in keys])
    Path(f"{stem}_summary.md").write_text("```\n" + report + "\n```\n")
    print(f"\nSaved {stem.name}_summary.csv and {stem.name}_summary.md")
    if stage == "experiment":
        cost_chart(summaries, f"{stem}_cost_vs_error.png")


if __name__ == "__main__":
    main()
