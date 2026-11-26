"""Final chart (Nov 25): avg error against system cost per interview, one panel per budget.
No API calls.

python plot_final.py   # -> results/final_error_vs_cost.png

All methods come from the reruns with the Nov 22 engine and the old band rule, paired on the
same test users (U054 left out): A (rerun_form_a.jsonl), C, D, DN (rerun_engine.jsonl), DW v2
(rerun_written_v2.jsonl), CW, CWF, CF. Cost is the system's calls only, at list price; the
test users' calls are not counted, because a real person replaces them.
"""
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config as C
from nl_benefits import RUNS, all_err
from rerun_compare import BUDGETS, R, load

ALL = {**RUNS, **load("rerun_hybrid.jsonl"), **load("rerun_hybrid_ff.jsonl"),
       **load("rerun_form_ff.jsonl"), **load("rerun_form_a.jsonl")}
METHODS = ("A", "C", "CF", "D", "DN", "DW", "CW", "CWF")
NAMES = {"A": "A fixed form", "C": "C adaptive form", "CF": "CF form, facts first",
         "D": "D AI interviewer", "DN": "DN no re-asks", "DW": "DW AI-written",
         "CW": "CW hybrid", "CWF": "CWF hybrid, facts first"}
COLOR = {"CWF": "#2a78d6", "CF": "#eb6834"}   # reference palette slots 1 and 2 (validated)
GRAY, INK, INK2, SURFACE = "#9a9893", "#0b0b0b", "#52514e", "#fcfcfb"


def cost(r):
    return sum((c["usage"]["in"] * C.MODELS[c.get("model") or r["interviewer"]]["price_in"]
                + c["usage"]["out"] * C.MODELS[c.get("model") or r["interviewer"]]["price_out"]) / 1e6
               for c in r["interviewer_calls"])


def main():
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4), sharey=True, facecolor=SURFACE)
    for ax, bu in zip(axes, BUDGETS):
        ax.set_facecolor(SURFACE)
        pts = []
        for m in METHODS:
            rs = [r for (mm, x, _, _), r in ALL.items() if mm == m and x == bu]
            pts.append((m, mean(map(cost, rs)) * 100, mean(map(all_err, rs))))
        for m, x, y in pts:
            if m == "A":   # the baseline: an open ring on top, so a method at the same spot stays visible
                ax.scatter(x, y, s=60, facecolor="none", edgecolor=INK2, linewidth=1.6, zorder=4)
                continue
            ax.scatter(x, y, s=70 if m in COLOR else 45, color=COLOR.get(m, GRAY),
                       edgecolor=SURFACE, linewidth=2, zorder=3)
        # short labels; methods at about the same cost are spaced apart in y, with a thin
        # line back to their own dot when a label had to move
        gap, done = 0.0034, []
        for m, x, y in sorted(pts, key=lambda p: p[2]):
            ly = y
            for px, py in done:
                if abs(px - x) < 0.35 and ly - py < gap:
                    ly = py + gap
            done.append((x, ly))
            ax.annotate(m, (x, y), xytext=(x + 0.12, ly), va="center", fontsize=9,
                        color=INK if m in COLOR else INK2, fontweight="bold" if m in COLOR else "normal",
                        arrowprops=dict(arrowstyle="-", color="#c9c8c3", lw=0.8,
                                        shrinkA=0, shrinkB=4) if abs(ly - y) > 1e-9 else None)
        ax.set_title(f"{bu} questions", fontsize=11, color=INK, loc="left")
        ax.set_xlim(-0.15, 2.5)
        ax.set_xlabel("System cost per interview (cents, list price)", fontsize=9, color=INK2)
        ax.grid(axis="y", color="#e6e5e1", linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#c9c8c3")
        ax.tick_params(colors=INK2, labelsize=8.5)
    axes[0].set_ylabel("Avg error (lower is better)", fontsize=9, color=INK2)
    fig.suptitle("Error against system cost, synthetic test users (99 users x 3 repeats per point)",
                 fontsize=12, color=INK, x=0.01, ha="left")
    fig.text(0.01, 0.01, "Open ring: the baseline A.   " + "   ".join(f"{m} = {NAMES[m].split(' ', 1)[1]}" for m in METHODS),
             fontsize=8.5, color=INK2, ha="left")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = R / "final_error_vs_cost.png"
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    print(out)
    for bu in BUDGETS:
        print(bu, {m: round(mean(map(all_err, [r for (mm, x, _, _), r in ALL.items() if mm == m and x == bu])), 3)
                   for m in METHODS})


if __name__ == "__main__":
    main()
