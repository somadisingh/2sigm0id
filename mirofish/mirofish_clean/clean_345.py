"""Clean MiroFish batches 3-5 (55 users).

Facts and attitudes are built from each user's true profile (personas_100.json), so they can't
contradict it. The FLAVOR sentences are details hand-picked from MiroFish's text that fit the
person (job specifics, hobbies, sayings); social-media/organisation framing, other users' names
and MiroFish's invented numbers and attitudes are left out.
Writes batch3_clean.json, batch4_clean.json, batch5_clean.json in reddit_profiles.json format.
"""
import json
import re
import sys
from pathlib import Path

USERS = "/home/claude/users100/personas_100.json"
SEEDS = "/home/claude/users100/seeds"
IN = {3: "in_14616841.json", 4: "in_479158bd.json", 5: "in_15dddeca.json"}

PRON = {"he": ("He", "he", "his", "him", "s"), "she": ("She", "she", "her", "her", "s"),
        "they": ("They", "they", "their", "them", "")}

# name: (pronoun, flavor sentence(s), bio, topics)
FLAVOR = {
 "Hana Davis": ("she", "She is upbeat and casual, and spends weekends exploring the city's food scene.",
   "Marketing coordinator working toward financial independence.", ["marketing", "personal finance", "food"]),
 "Thomas Rodriguez": ("he", "He likes phrases like 'planning ahead' and 'financial discipline' and often talks retirement strategy with colleagues.",
   "Senior accountant planning for retirement.", ["accounting", "retirement planning", "tax planning"]),
 "Marcus Williams": ("he", "His favorite lines are 'Let's look at the numbers' and 'Your future self will thank you', and he builds budget templates for fun.",
   "Data analyst and young dad saving for retirement.", ["data analysis", "retirement planning", "parenting", "budgeting"]),
 "Camila Yamamoto": ("she", "She is early in her medical career and likes to keep things simple and low-maintenance outside the hospital.",
   "Young physician investing for the long run.", ["medicine", "long-term investing", "personal finance"]),
 "Imani Rossi": ("they", "They talk like a salesperson, with phrases like 'closing the deal' and 'side hustle', and dream of running their own business.",
   "Software sales rep and parent of three, hoping to start a business.", ["sales", "small business", "family budgeting"]),
 "Adrian Harris": ("they", "They photograph weddings and portraits and talk about parenting and creative work in the same breath.",
   "Freelance photographer and single parent.", ["photography", "freelancing", "parenting", "car buying"]),
 "Julia Rivera": ("she", "She works construction jobs day to day and likes to say 'every dollar counts'.",
   "Construction day laborer supporting an elderly parent.", ["construction work", "caring for family", "home repairs", "budgeting"]),
 "Joel Scott": ("he", "He works on backend systems and cloud architecture at a mid-sized tech company.",
   "Senior software engineer chasing financial independence.", ["software engineering", "cloud computing", "financial independence"]),
 "Emeka Santos": ("he", "He is practical and plain-spoken and likes long-term projects at work and at home.",
   "Civil engineer investing for the long run.", ["civil engineering", "long-term investing", "personal finance"]),
 "Elena Wang": ("she", "She has worked in fitness for more than three decades and often says 'listen to your body' and 'small steps count'.",
   "Veteran personal trainer planning a comfortable retirement.", ["fitness", "healthy aging", "retirement planning"]),
 "Alejandro Moore": ("they", "They design apps for a living and care a lot about clean, simple user experiences.",
   "UX designer saving for early retirement.", ["UX design", "early retirement", "personal finance"]),
 "Derek Flores": ("he", "He runs a shift at the local post office and keeps his life organized and predictable.",
   "Postal service supervisor saving for retirement.", ["postal service", "retirement savings", "personal finance"]),
 "Tariq Sullivan": ("he", "He needs a reliable car for his work, so replacing his aging one is his top priority.",
   "Rideshare driver supporting a family of four.", ["rideshare work", "car buying", "family budgeting"]),
 "Zoe Kaur": ("she", "She is warm and funny, likes to say 'another shift, another dollar', and backs her opinions with numbers.",
   "Event bartender planning for retirement and future grandkids.", ["bartending", "event work", "retirement planning", "family"]),
 "Gabriel Taylor": ("he", "He dreams of starting his own business and keeps a detailed spreadsheet for paying down debt.",
   "Medical lab technician and dad of two with entrepreneurial plans.", ["lab science", "small business", "parenting", "debt payoff"]),
 "Erin Brooks": ("she", "Her spouse stays home with their young daughter, so she is the family's only earner.",
   "Registered nurse and sole earner for a family of three.", ["nursing", "parenting", "financial independence"]),
 "Amara Torres": ("she", "She likes to say 'Let's look at the numbers' and 'Diversification is key'.",
   "Senior accountant saving for retirement.", ["accounting", "retirement planning", "diversification"]),
 "Megan Patel": ("she", "She has sold homes for decades as an independent agent and relies on her network and reputation.",
   "Veteran real estate agent planning for retirement and grandkids.", ["real estate", "self-employed retirement", "family"]),
 "Ryan Huang": ("he", "He drives rideshare in his early sixties and wants a steady income once he stops.",
   "Rideshare driver nearing retirement.", ["rideshare work", "retirement income", "family"]),
 "Kenji Chen": ("they", "They have worked at the same small salon for more than a decade and describe themselves as 'stylist, parent, money learner'.",
   "Hairstylist and single parent saving for early retirement.", ["hairstyling", "parenting", "early retirement"]),
 "Rafael Jackson": ("he", "He is calm and measured, keeps his feelings to himself, and enjoys a comfortable life with his wife, who has her own career.",
   "Hospital administrator investing for the long run.", ["hospital administration", "long-term investing", "personal finance"]),
 "Hector Adams": ("he", "He likes to say 'Ship it!' and 'Invest early, compound later'.",
   "Software developer and parent saving for retirement.", ["software development", "retirement planning", "parenting"]),
 "Lily Bello": ("she", "She is meticulous with numbers at work and at home.",
   "Senior accountant saving for a bigger home.", ["accounting", "home buying", "personal finance"]),
 "Maria Phillips": ("she", "She is focused on her engineering work and has only recently started thinking about investing.",
   "Senior software engineer investing for the long run.", ["software engineering", "long-term investing", "personal finance"]),
 "Fatima Price": ("she", "She is a licensed civil engineer with a passion for sustainable, community-focused design.",
   "Young civil engineer and mom aiming for financial independence.", ["civil engineering", "sustainable design", "parenting"]),
 "Bianca Walker": ("she", "She has worked behind a bank counter for years and supports her family on a single income.",
   "Bank teller planning for retirement and future grandkids.", ["banking", "retirement planning", "family"]),
 "Vera Kowalski": ("she", "She combines her interest in physical health with getting her finances in shape.",
   "Personal trainer saving for a house down payment.", ["fitness", "saving for a home", "debt payoff"]),
 "Nora Perez": ("she", "She has worked in hospitals for more than two decades and likes to say 'Treat your savings like a vital sign'.",
   "Registered nurse and mom of a teenager.", ["nursing", "financial independence", "parenting"]),
 "Zach Mendoza": ("he", "He is a single dad and the sole provider for his young daughter, and he is passionate about patient care and medication safety.",
   "Pharmacist and single dad aiming for financial independence.", ["pharmacy", "parenting", "financial independence"]),
 "Kevin Singh": ("he", "He is careful and deliberate, and gets most interested in money around tax season and year-end.",
   "Medical lab technician saving for early retirement.", ["lab science", "early retirement", "taxes"]),
 "Miguel Evans": ("he", "He spends his days writing code and his evenings on outdoor hobbies.",
   "Senior software engineer aiming for financial independence.", ["software engineering", "financial independence", "outdoors"]),
 "Talia Campbell": ("she", "She is a certified personal trainer, a wife and the mother of a young child.",
   "Personal trainer and young mom saving for a new car.", ["fitness", "parenting", "car buying"]),
 "Priya Alvarez": ("she", "She has spent more than 25 years in marketing at a regional retail company, researches decisions thoroughly, and loves hiking and cooking.",
   "Marketing coordinator working toward financial independence.", ["marketing", "hiking", "cooking", "financial independence"]),
 "Uma Nguyen": ("she", "She earned an associate degree part-time while working, and her husband does part-time freelance design while caring for their young daughter.",
   "Postal service supervisor saving for a first home.", ["postal service", "saving for a home", "parenting"]),
 "Amir Wilson": ("he", "He likes to say 'always read the fine print'.",
   "Bank teller supporting an elderly parent.", ["banking", "caring for family", "home buying"]),
 "Ravi Hall": ("he", "He has written software for more than 30 years, specializing in backend systems, and talks about 'technical debt' and 'best practices'.",
   "Veteran software developer planning a comfortable retirement.", ["software development", "backend systems", "retirement planning"]),
 "Sofia Ramirez": ("she", "She is early in her nursing career and lives with her partner.",
   "Registered nurse saving for early retirement.", ["nursing", "early retirement", "personal finance"]),
 "Alex Reyes": ("he", "He talks about money 'from behind the counter' and wants better financial education in schools.",
   "Bank teller and dad of two saving for retirement.", ["banking", "retirement planning", "parenting", "financial education"]),
 "Ines Green": ("she", "She thinks in terms of 'strategic planning' and 'legacy building'.",
   "Corporate attorney saving for retirement and her child's college.", ["law", "retirement planning", "college savings"]),
 "Jamal Washington": ("he", "He left community college to work full-time when his daughter was born and plans to go back someday. He talks casually, but gets serious when the topic is his daughter.",
   "Warehouse temp worker and single dad saving for his daughter's college.", ["parenting", "college savings", "warehouse work"]),
 "Aisha Lee": ("they", "They have designed digital products for years and care about the people behind the screens.",
   "UX designer and parent of two teens saving for retirement.", ["UX design", "retirement planning", "parenting"]),
 "Zainab Thomas": ("she", "She has planned trips for clients for decades and likes to say 'Travel smart, save more'.",
   "Travel agent supporting a family and saving for retirement.", ["travel", "retirement planning", "family"]),
 "Sara White": ("she", "She has supervised a postal team for over a decade and is disciplined about schedules.",
   "Postal service supervisor saving for a house.", ["postal service", "saving for a home", "budgeting"]),
 "Leon Lewis": ("he", "He runs a small dental practice focused on family and cosmetic dentistry.",
   "Dentist working toward financial independence.", ["dentistry", "financial independence", "small business"]),
 "Xavier Morales": ("he", "He works a chair at a suburban salon and likes to say 'keep it real' and 'one step at a time'.",
   "Hairstylist supporting a family of four on one income.", ["hairstyling", "family budgeting", "financial independence"]),
 "Chloe Vargas": ("she", "She has freelanced for decades and jokes that 'just like kerning, alignment matters in your budget'.",
   "Freelance graphic designer planning for retirement and grandkids.", ["graphic design", "freelancing", "retirement planning"]),
 "Daniela Garcia": ("she", "She practices internal medicine with a focus on preventive care.",
   "Physician investing for the long run.", ["medicine", "preventive care", "long-term investing"]),
 "Oscar Zhang": ("he", "He shares an apartment with a long-time friend, tracks his net worth monthly, loves hiking and photography, and quotes Warren Buffett.",
   "Hospital administrator aiming for financial independence.", ["hospital administration", "financial independence", "hiking", "photography"]),
 "Chris Gomez": ("he", "He has sold cars for more than three decades, grows tomatoes and peppers in his backyard, and says 'That's the way the cookie crumbles' when things go wrong.",
   "Veteran car salesperson planning a comfortable retirement.", ["car sales", "gardening", "retirement planning"]),
 "Sam Fischer": ("he", "He has worked in tech for more than 25 years, loves woodworking and hiking, and says 'measure twice, cut once'.",
   "Senior software engineer saving for retirement.", ["software engineering", "woodworking", "hiking", "retirement planning"]),
 "Brandon Okafor": ("he", "He works at a community health center, loves jazz and vintage vinyl, and volunteers at a food bank on Saturdays.",
   "Social worker investing for the long run.", ["social work", "jazz", "volunteering", "index investing"]),
 "Kavya Martin": ("she", "She has a master's degree in statistics and spent two decades turning raw numbers into strategy.",
   "Data analyst and mom of two teens saving for retirement.", ["data analysis", "retirement planning", "parenting"]),
 "Ximena Diaz": ("she", "She likes to say 'let's look at the numbers' and 'based on historical trends'.",
   "Data analyst planning for retirement.", ["data analysis", "retirement planning", "market history"]),
 "Tessa Murphy": ("she", "She handles mergers and acquisitions at a law firm, loves hiking and reads financial news daily.",
   "Corporate attorney aiming for financial independence.", ["law", "hiking", "financial independence", "index funds"]),
 "Yara James": ("she", "She has worked for the postal service for more than two decades and values stability.",
   "Postal service supervisor planning for retirement.", ["postal service", "retirement planning", "personal finance"]),
}


def band(s):
    return min(5, int(s * 5) + 1)


def months(m):
    if m < 0.4: return "about a week of expenses saved"
    if m < 0.75: return "about two weeks of expenses saved"
    if m < 1.5: return "about a month of expenses saved"
    if m < 11: return f"about {int(m)} months of expenses saved"
    if m < 15: return "about a year of expenses saved"
    if m < 21: return "about a year and a half of expenses saved"
    return "about two years of expenses saved"


INCOME = {"unstable": "income is unpredictable", "partly commission-based": "income is partly commission-based",
          "stable": "salary is steady", "very stable": "income is very stable", "stable and high": "income is high and steady"}

HOUSE = {
    "single, lives alone": "{S} {is} single and live{v} alone.",
    "single, shares an apartment": "{S} {is} single and share{v} an apartment.",
    "lives with a partner": "{S} live{v} with a partner.",
    "married, no children": "{S} {is} married with no children.",
    "married, grown children": "{S} {is} married with grown children.",
    "supports an elderly parent": "{S} support{v} an elderly parent.",
}

WILL = {1: "{S} avoid{v} risk and would rather earn little than lose anything.",
        2: "{S} {is} fairly cautious and get{v} uneasy with big swings.",
        3: "{S} {is} middle-of-the-road about risk, accepting some ups and downs for growth.",
        4: "{S} {is} comfortable taking real risk for higher growth.",
        5: "{S} want{v} maximum growth and insist{v} losses don't scare {o}."}
BEH = {1: "when {p} own money is falling, {s} get{v} out fast and lose{v} sleep.",
       2: "watching {p} own balance shrink makes {o} anxious, and {s} tend{v} to cut {p} losses.",
       3: "when markets turn rough, {s} feel{v} uneasy and might trim a little, but mostly sit{v} tight.",
       4: "when markets turn rough, {s} stay{v} calm and wait{v} it out.",
       5: "when markets fall, {s} see{v} a bargain and add{v} more."}
GOAL = {"growing long-term wealth": "to grow {p} wealth over the long term",
        "financial independence": "toward financial independence"}
LIT = {"high": "knows a lot", "medium": "knows a moderate amount", "low": "knows little"}


def build(u, pron, flavor):
    S, s, p, o, v = PRON[pron]
    def V(t):  # {v} = verb ending, {is}/{has} = agreeing verbs
        return t.replace("{v}", v).replace("{is}", "are" if pron == "they" else "is") \
                .replace("{has}", "have" if pron == "they" else "has")
    d, f, e, g = u["demographics"], u["finances"], u["experience"], u["ground_truth"]
    name = u["profile"]["name"]
    out = [f"{name} is a {d['age']}-year-old {d['occupation']}."]
    hh = d["household"]
    if hh in HOUSE:
        out.append(V(HOUSE[hh]).format(S=S))
    else:
        hh2 = hh.replace("married, ", "married with ").replace("single parent, ", "a single parent of ")
        hh2 = hh2.replace("; spouse not working", ", and " + p + " spouse does not work")
        out.append(f"{S} {V('{is}')} {hh2}.")
    dti = f["debt_to_income"]
    debt = ("has almost no debt" if dti < 0.05 else "has little debt" if dti < 0.10
            else f"debt payments take about {int(round(dti * 100))}% of it")
    if dti < 0.10:
        out.append(f"{p.capitalize()} {INCOME[f['income_stability']]}, {s} {V(debt.replace('has', '{has}'))}, and {s} {V('{has}')} {months(f['emergency_fund_months'])}.")
    else:
        out.append(f"{p.capitalize()} {INCOME[f['income_stability']]}, {debt}, and {s} {V('{has}')} {months(f['emergency_fund_months'])}.")
    h = f["horizon_yrs"]
    when = "within about a year" if h <= 1 else f"in about {h} years"
    goal = GOAL.get(f["goal"], "for " + f["goal"]).format(p=p)
    out.append(f"{S} want{v} to invest ${f['investable_amount']:,} {goal}, needing it {when}.")
    out.append(f"{S} {LIT[e['fin_literacy']].replace('knows', 'know' if pron == 'they' else 'knows')} about investing.")
    wb, bb, cb = band(g["willingness"]), band(g["behavioral"]), band(g["capacity"])
    will = V(WILL[wb]).format(S=S, o=o)
    if g["mismatch_type"].startswith("can afford"):
        will = f"Even though {s} could afford losses, " + will[0].lower() + will[1:]
    out.append(will)
    loss = e["past_loss_reaction"]
    beh = V(BEH[bb]).format(s=s, p=p, o=o)
    contrast = "But" if (wb - bb) >= 2 else "And"
    if loss == "sold":
        first = f"in a past downturn {s} sold in a panic and still think{v} about it; {beh}"
        out.append(("But " if contrast == "But" else "") + (first if contrast == "But" else first[0].upper() + first[1:]))
    elif loss == "held":
        out.append(f"In a past downturn {s} held on, {'but' if contrast == 'But' else 'and'} {beh}")
    else:
        lead = f"{S} {V('{has}')} never been through a big investment loss"
        out.append(f"{lead}, {'but' if contrast == 'But' else 'and'} {s} say{v} that {beh}")
    out.append(flavor)
    return " ".join(out)


def main():
    users = {u["profile"]["name"]: u for u in json.loads(Path(USERS).read_text())}
    all_names = set(users)
    for b, fn in IN.items():
        agents = {a["name"]: a for a in json.loads(Path(fn).read_text())}
        names = re.findall(r"^## (.+)$", Path(f"{SEEDS}/seed_batch_{b:02d}.md").read_text(), re.M)
        rows = []
        for n in names:
            pron, flavor, bio, topics = FLAVOR[n]
            u, a = users[n], agents[n]
            story = build(u, pron, flavor)
            others = [x for x in all_names if x != n and x in story]
            assert not others, (n, others)
            assert not re.search(r"[一-鿿]", story + bio + "".join(topics)), n
            rows.append({"user_id": a["user_id"], "username": a["username"], "name": n, "bio": bio,
                         "persona": story, "karma": a.get("karma", 1000), "created_at": a.get("created_at"),
                         "age": u["demographics"]["age"], "gender": {"he": "male", "she": "female"}.get(pron, "other"),
                         "mbti": a.get("mbti"), "country": "United States",
                         "profession": u["demographics"]["occupation"], "interested_topics": topics})
        Path(f"batch{b}_clean.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        print(f"batch{b}_clean.json: {len(rows)} users")


if __name__ == "__main__":
    main()
