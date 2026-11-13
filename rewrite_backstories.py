"""Rewrite the risk sentences in the 100 test users' backstories (Nov 13, 2026).

Why: the first backstories used a few fixed sentences for each band ("gets out fast and loses
sleep" = behavior band 1, "sees a bargain and adds more" = band 5, "wants maximum growth and
insists losses don't scare" x23). The users sounded alike, and a fixed sentence per band is a
clue the extractor can learn. This script asks GLM 5.3 to rewrite only the parts about risk and
market drops, with a different concrete "angle" for each user, and keeps everything else.
True scores do not change. The old story stays in profile.backstory_v1.

  python rewrite_backstories.py write      # rewrite (about 100 calls) -> results/backstory_rewrites.jsonl
  python rewrite_backstories.py check      # checks + blind read -> persona_checks/backstory_rewrite.md
  python rewrite_backstories.py apply      # write the checked stories into the persona file
"""

import argparse
import json
import random
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import config as C
import run_bakeoff as R
from llm import extract_json, strip_think
from prompts import band

HERE = Path(__file__).resolve().parent
PERSONAS = HERE / "mirofish/personas_100_with_backstories.json"
OUT = HERE / "results/backstory_rewrites.jsonl"
REPORT = HERE / "persona_checks/backstory_rewrite.md"
MODEL = "glm-5.3"

# The meaning of each band (same as WILLINGNESS_TEXT / BEHAVIORAL_TEXT in prompts.py).
WILL = {
    1: "very cautious: would rather earn little than risk losing anything",
    2: "fairly cautious: small ups and downs are fine, big swings make them uneasy",
    3: "in the middle: accepts some risk for some growth",
    4: "fairly bold: happy to take real risk for higher growth",
    5: "very aggressive: wants the highest growth and claims losses don't bother them",
}
BEH = {
    1: "when their own investments lose a lot of value, they sell quickly to stop the losses",
    2: "when their own investments lose a lot of value, they get anxious and sell a good part to feel safer",
    3: "when their own investments lose a lot of value, they feel uneasy and may sell a little, but mostly hold",
    4: "when their own investments lose a lot of value, they stay calm, keep everything and wait",
    5: "when their own investments lose a lot of value, they invest more",
}
# One concrete angle per user, drawn by seed, so the same band is told in different ways.
ANGLES = {
    1: ["moved everything into a savings account after a drop and has not gone back",
        "checks the investing app many times a day and sells as soon as it turns red",
        "stops all contributions and pulls money out at the first bad week",
        "keeps most money in cash or CDs because a drop makes their stomach turn",
        "sells at the first dip, then buys back later at a higher price",
        "calls a relative for advice during a drop but sells before they call back",
        "deletes the app during a drop, then sells everything a few days later"],
    2: ["moves about half into cash when the news turns bad",
        "switches to a 'safer' fund after a few red weeks",
        "sells the holdings that are down the most to feel in control",
        "pauses contributions and sells part of the account",
        "talks it over with a friend or partner, then sells a good chunk"],
    3: ["trims one position and leaves the rest alone",
        "pauses new contributions for a while but sells almost nothing",
        "complains a lot and checks more often, but mostly sits still",
        "sells a small piece to feel better, keeps the rest"],
    4: ["does not open the app during a drop and waits it out",
        "reminds themselves of their long time frame and keeps automatic contributions running",
        "remembers a past recovery and keeps everything invested",
        "reads the bad news but changes nothing in the account"],
    5: ["keeps some cash ready on purpose to buy when prices fall",
        "raises their monthly contribution when the market is down",
        "treats a market drop like a store sale and buys more",
        "buys more of the funds that dropped the most"],
}
PAST = {
    "none": ("they have never been through a big investment loss. Describe their reaction only "
             "as what they WOULD do if it happened (use 'would'). Do not describe any past dip, "
             "drop or slide, not even a small one, and do not say they held or sold before"),
    "held": "in a past market drop they held on",
    "sold": "in a past market drop they sold out of fear",
}
REASON = {
    "says aggressive, would panic-sell": [
        "they talk big because friends, coworkers or online finance accounts all talk that way",
        "they like the idea of being a bold investor more than the reality",
        "they read about big winners and assume they would hold on too"],
    "says aggressive, can't afford it": [
        "a friend or relative made a lot of money fast and they want the same",
        "their job rewards optimism and they bring that attitude to money",
        "they feel they must take big swings to ever catch up",
        "they are sure their plan will work and do not think about the downside"],
    "can afford risk, prefers caution": [
        "at their age, they would rather keep what they have than chase more",
        "peace of mind matters more to them than extra return",
        "investing is low on their list; family, work or health come first",
        "they watched a parent or relative lose money and never forgot it"],
}
BANNED = ["lose sleep", "loses sleep", "losing sleep", "sold in a panic", "still thinks about it",
          "still think about it", "gets out fast", "get out fast", "maximum growth",
          "losses don't scare", "sees a bargain", "see a bargain", "adds more",
          "stays calm and waits it out", "stay calm and wait it out", "middle-of-the-road",
          "gets uneasy with big swings", "cut their losses", "cut his losses", "cut her losses",
          "trim a little, but mostly", "comfortable taking real risk", "20%", "band", "score"]

SYSTEM = """You edit short character backstories for a research study with simulated people.
Rewrite ONLY the parts of the story about attitude to risk, reactions to market drops, past
investment losses and investing knowledge. Keep every other sentence as it is: name, pronouns,
age, job, family, every number about money, the goal, hobbies, personality and speech habits.
Reply with the new story only, no title and no comments."""

USER = """Story:
{story}

The rewritten risk parts must show these facts about the person:
- What they SAY about risk: {will}.
- What they really DO: {beh}. Show it through this concrete habit: {angle}. Always state
  this clearly, even if they have never been through a loss (then say what they would do).
- Past experience: {past}.
- Investing knowledge: {lit}.{reason}

Rules:
- Show it through concrete everyday details that fit this person's life, not labels.
- Do not use these phrases: {banned}.
- No percentages for market drops, no scores, no bands. Do not add new numbers about money.
- Keep the story about the same length ({words} words, plus or minus 20%)."""


def personas():
    return json.loads(PERSONAS.read_text())


def story_of(p):
    pr = p["profile"]
    return pr.get("backstory_v1") or pr["backstory"]


def prompt_for(p):
    g, e = p["ground_truth"], p["experience"]
    rng = random.Random(f"{p['id']}-rewrite")
    b = band(g["behavioral"])
    mm = g["mismatch_type"]
    reason = ""
    if mm in REASON:
        reason = (f"\n- They have a mismatch ({mm}). Add one short, believable reason that fits "
                  f"their life, for example: {rng.choice(REASON[mm])}.")
    story = story_of(p)
    return USER.format(story=story, will=WILL[band(g["willingness"])], beh=BEH[b],
                       angle=rng.choice(ANGLES[b]), past=PAST[e["past_loss_reaction"]],
                       lit=e["fin_literacy"], reason=reason, banned="; ".join(BANNED[:-3]),
                       words=len(story.split()))


def numbers(text):
    """Numbers that must survive: money, months, ages, percentages (not years)."""
    nums = re.findall(r"\$?\d[\d,]*(?:\.\d+)?%?", text)
    return {n.replace(",", "").lstrip("$") for n in nums if not re.fullmatch(r"(19|20)\d\d", n)}


def problems(old, new):
    out = []
    low = new.lower()
    # word match, so "husband" is not "band"; a phrase already in the old story (a 20% debt) is fine
    out += [f"banned: {b}" for b in BANNED
            if re.search(rf"(?<![a-z]){re.escape(b.lower())}(?![a-z])", low)
            and b.lower() not in old.lower()]
    missing = numbers(old) - numbers(new)
    out += [f"missing number: {m}" for m in sorted(missing)]
    if old.split()[0] != new.split()[0]:
        out.append("name changed")
    ratio = len(new.split()) / len(old.split())
    if not 0.7 <= ratio <= 1.4:
        out.append(f"length x{ratio:.2f}")
    return out


def write(args):
    llm = R.make_llm(args.mock)
    ps = personas()
    done = {}
    if OUT.exists():
        done = {r["id"]: r for r in map(json.loads, OUT.read_text().splitlines())
                if not r["problems"]}
    if args.only:   # these users only; with --redo, also ones already written
        todo = [p for p in ps if p["id"][:4] in args.only and (args.redo or p["id"] not in done)]
    else:
        todo = [p for p in ps if args.redo or p["id"] not in done]

    def one(p):
        old = story_of(p)
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt_for(p)}]
        for attempt in range(3):
            r = llm.chat(MODEL, msgs, "off", 1500, 0.8)
            new = strip_think(r["text"]).strip().strip('"')
            probs = problems(old, new)
            if not probs:
                break
        return {"id": p["id"], "old": old, "new": new, "problems": probs, "attempts": attempt + 1}

    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        for r in ex.map(one, todo):
            done[r["id"]] = r
            print(r["id"], "ok" if not r["problems"] else r["problems"])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("".join(json.dumps(done[p["id"]]) + "\n" for p in ps if p["id"] in done))
    bad = [r for r in done.values() if r["problems"]]
    print(f"{len(done)} written, {len(bad)} with problems. Next: python rewrite_backstories.py check")


JUDGE = """Read this short description of a person. Rate them on two 1-5 scales.
willingness: what they SAY about risk (1 = very cautious, 3 = in the middle, 5 = very aggressive).
behavior: what they would really DO when their investments lose a lot of value
(1 = sell quickly, 2 = sell a good part, 3 = sell a little but mostly hold, 4 = hold calmly, 5 = buy more).
past: their past big investment loss: "none", "held" or "sold".
Reply with JSON only: {"willingness": n, "behavior": n, "past": "..."}

Description:
"""


def ngram_repeats(stories, n=5):
    """How many 5-word sequences appear in 5+ different stories (style lines included)."""
    seen = Counter()
    for s in stories:
        w = re.sub(r"[^a-z' ]", " ", s.lower()).split()
        seen.update({" ".join(w[i:i + n]) for i in range(len(w) - n + 1)})
    return sum(1 for c in seen.values() if c >= 5), seen.most_common(5)


def check(args):
    llm = R.make_llm(args.mock)
    ps = {p["id"]: p for p in personas()}
    rows = [json.loads(x) for x in OUT.read_text().splitlines()]

    def read(text):
        r = llm.chat(MODEL, [{"role": "user", "content": JUDGE + text}], "off", 200, 0.0)
        try:
            return extract_json(strip_think(r["text"]))
        except Exception:
            return {}

    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        old_reads = list(ex.map(read, [r["old"] for r in rows]))
        new_reads = list(ex.map(read, [r["new"] for r in rows]))

    def hits(reads):
        out = Counter()
        for r, j in zip(rows, reads):
            g, e = ps[r["id"]]["ground_truth"], ps[r["id"]]["experience"]
            for dim, key in (("willingness", "willingness"), ("behavioral", "behavior")):
                try:
                    d = abs(int(j.get(key)) - band(g[dim]))
                except (TypeError, ValueError):
                    d = 9
                out[f"{key} exact"] += d == 0
                out[f"{key} within 1"] += d <= 1
            out["past right"] += j.get("past") == e["past_loss_reaction"]
        return out

    ho, hn = hits(old_reads), hits(new_reads)
    rep_old, top_old = ngram_repeats([r["old"] for r in rows])
    rep_new, top_new = ngram_repeats([r["new"] for r in rows])
    sleep = lambda key: sum("sleep" in r[key].lower() for r in rows)  # noqa: E731
    panic = lambda key: sum("panic" in r[key].lower() for r in rows)  # noqa: E731
    n = len(rows)
    lines = [
        "# Backstory rewrite check",
        "",
        "`rewrite_backstories.py` (Nov 13, 2026). Only the risk sentences changed; the true scores did not.",
        "",
        f"Stories: {n}. With problems after 3 tries: {sum(bool(r['problems']) for r in rows)}.",
        "",
        "## Blind read (GLM 5.3, does not see the true profile)",
        "",
        "It should still recover the profile from the new stories, about as well as from the old ones.",
        "",
        "| | old stories | new stories |",
        "|---|---|---|",
    ]
    for k in ("willingness exact", "willingness within 1", "behavior exact", "behavior within 1", "past right"):
        lines.append(f"| {k} | {ho[k]}/{n} | {hn[k]}/{n} |")
    lines += [
        "",
        "## Sameness",
        "",
        "| | old | new |",
        "|---|---|---|",
        f"| 5-word phrases in 5+ stories | {rep_old} | {rep_new} |",
        f"| stories with \"sleep\" | {sleep('old')} | {sleep('new')} |",
        f"| stories with \"panic\" | {panic('old')} | {panic('new')} |",
        "",
        "Most repeated 5-word phrases, new: " + "; ".join(f"\"{k}\" ({c})" for k, c in top_new),
        "",
        "## Users the blind read missed by 2+ bands (new stories)",
        "",
    ]
    for r, j in zip(rows, new_reads):
        g = ps[r["id"]]["ground_truth"]
        try:
            bad = [f"{k} read {j[k]}, true {band(g[d])}" for d, k in
                   (("willingness", "willingness"), ("behavioral", "behavior"))
                   if abs(int(j[k]) - band(g[d])) >= 2]
        except (KeyError, TypeError, ValueError):
            bad = ["no reading"]
        if bad:
            lines.append(f"- {r['id']}: " + "; ".join(bad))
    REPORT.write_text("\n".join(lines) + "\n")
    json.dump({"old": old_reads, "new": new_reads}, open(HERE / "results/backstory_reads.json", "w"))
    print("\n".join(lines))


def apply(args):
    rows = {r["id"]: r for r in map(json.loads, OUT.read_text().splitlines())}
    bad = [i for i, r in rows.items() if r["problems"]]
    if bad and not args.force:
        raise SystemExit(f"Not applied: {bad} still have problems (use --force to skip them).")
    raw = PERSONAS.read_text()
    ps = json.loads(raw)
    n = 0
    for p in ps:
        r = rows.get(p["id"])
        if r and not r["problems"]:
            pr = p["profile"]
            old = pr.get("backstory_v1", pr["backstory"])
            # rebuild so backstory_v1 sits right after backstory
            p["profile"] = {}
            for k, v in pr.items():
                if k == "backstory_v1":
                    continue
                p["profile"][k] = r["new"] if k == "backstory" else v
                if k == "backstory":
                    p["profile"]["backstory_v1"] = old
            n += 1
    end = "\n" if raw.endswith("\n") else ""   # keep the file's own format
    PERSONAS.write_text(json.dumps(ps, indent=2, ensure_ascii=False) + end)
    print(f"{n} stories applied to {PERSONAS.name} (old ones kept as profile.backstory_v1).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["write", "check", "apply"])
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--redo", action="store_true", help="rewrite all, not only missing or failed")
    ap.add_argument("--only", nargs="*", help="user id prefixes, e.g. U042 U050")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    {"write": write, "check": check, "apply": apply}[args.cmd](args)
