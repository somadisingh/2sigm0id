"""Flag backstories that need a human look, so you don't have to read all 100 closely.

    python check_backstories.py personas_100_with_backstories.json

Flags (per user):
  MISSING     no backstory yet
  CHINESE     MiroFish wrote in Chinese (switch the MiroFish page to English before uploading)
  SOCIAL      talks about an account, followers, posting, etc. (MiroFish's social-media framing)
  AGE         states an age that isn't the user's
  NUMBERS     states a dollar amount, % or month count that isn't in the user's finances
  OTHERS      mentions another test user by name
  LONG        over 200 words (the simulator only needs a short paragraph)
It can't catch everything: also skim the flagged ones' attitudes against their true bands.
"""
import json
import re
import sys
from pathlib import Path

SOCIAL = re.compile(r"\b(followers?|posts? (?:about|to|on)|posting|audience|engagement|subscribers?|"
                    r"social media|(?:this|the|her|his|their) account|content creator|operat\w+ (?:the|this))\b",
                    re.I)


def allowed_numbers(u):
    f, d = u["finances"], u["demographics"]
    nums = {str(d["age"]), str(f["horizon_yrs"]), str(f["dependents"]), str(int(f["debt_to_income"] * 100)),
            f"{f['investable_amount']:,}", str(f["investable_amount"]), str(f["emergency_fund_months"]).rstrip("0").rstrip(".")}
    nums |= {str(y) for y in range(1990, 2031)}   # years like "in 2022" are fine
    return nums


def check(u, all_names):
    b = (u.get("profile") or {}).get("backstory") or ""
    flags = []
    if not b.strip():
        return ["MISSING"]
    if re.search(r"[一-鿿]", b):
        flags.append("CHINESE")
    if SOCIAL.search(b):
        flags.append("SOCIAL")
    ages = re.findall(r"\b(\d{2})-year-old\b", b)
    if any(a != str(u["demographics"]["age"]) for a in ages):
        flags.append("AGE")
    ok = allowed_numbers(u)
    stated = re.findall(r"\$\s?([\d,]+)|\b(\d+(?:\.\d+)?)\s?(?:%|percent|months?)\b", b)
    if any((m or n) not in ok for m, n in stated):
        flags.append("NUMBERS")
    me = u["profile"]["name"]
    if any(n != me and n in b for n in all_names):
        flags.append("OTHERS")
    if len(b.split()) > 200:
        flags.append("LONG")
    return flags


def main():
    users = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    names = [u["profile"]["name"] for u in users]
    flagged = 0
    for u in users:
        f = check(u, names)
        if f:
            flagged += 1
            print(f"{u['id']:32} {u['profile']['name']:22} {', '.join(f)}")
    print(f"\n{flagged}/{len(users)} users flagged; {len(users) - flagged} look clean.")


if __name__ == "__main__":
    main()
