"""Cleaned English backstories for MiroFish batches 1 and 2 (40 users).

Each backstory keeps the person's true facts (personas_100.json) and the MiroFish details that fit
them; social-media framing, organisations, invented numbers and contradictions are removed.
Attitudes follow the true willingness/behavioral bands; experience follows fin_literacy and
past_loss_reaction. Writes batch1_clean.json and batch2_clean.json in MiroFish's
reddit_profiles.json format, ready for mirofish_to_personas.py.
"""
import json
import re
from pathlib import Path

C = {
# ----------------------------------------------------------------------------- batch 1
"Ben Morales": ("Dentist who wants his retirement savings to grow as fast as possible.",
 "Ben Morales is a 29-year-old dentist at a modern urban clinic. He is single, lives alone, has a high, steady income, almost no debt and about two years of expenses in savings. He wants to invest $97,000 for retirement, roughly 30 years away. Although he knows little about investing and has never been through a market crash, he wants maximum growth and insists losses don't scare him; he says a big drop would just be a chance to buy more. He is warm and evidence-minded at work and wants the same plain explanations about money.",
 ["dentistry", "retirement planning", "personal finance", "healthy living"]),
"Isaac Vargas": ("Civil engineer saving toward a bigger home.",
 "Isaac Vargas is a 44-year-old civil engineer who works on transportation and land-development projects. He is single and lives alone, has a very stable salary, very little debt and about four months of expenses saved. He wants to invest $78,000 toward a bigger home in about 12 years. He is analytical and methodical, explains things step by step, and is comfortable taking real risk for growth. In a past downturn he held on, and when markets turn rough he stays calm and treats it as a chance to add more. He knows a moderate amount about investing and likes to check the numbers himself.",
 ["civil engineering", "infrastructure", "home buying", "personal finance"]),
"Mina Garcia": ("Community pharmacist and young parent saving for a house.",
 "Mina Garcia is a 28-year-old pharmacist at a community pharmacy. She is married with one young child, has a very stable income, little debt and about four months of expenses saved. She wants to invest $21,000 for a house down payment in about 10 years. She knows a lot about investing and talks boldly about wanting maximum growth. But she has never watched her own money fall sharply, and when markets turn rough she feels uneasy and would probably trim some holdings rather than buy more. At work she explains things clearly, without jargon.",
 ["pharmacy", "family budgeting", "saving for a home", "investing"]),
"Nadia Zhang": ("Event bartender with an uneven income, slowly building a safety net.",
 "Nadia Zhang is a 33-year-old event bartender who lives with her partner. Her income rises and falls with event bookings, and student loan and credit card payments take about 41% of it. She has about two months of expenses saved. She wants to put $1,000 toward a house down payment in about 10 years. She is fairly cautious and gets uneasy with big swings; watching her balance shrink makes her anxious, and she tends to cut her losses. She has never invested before and knows little about it. She is warm and funny and likes to say 'another shift, another story'.",
 ["bartending", "event work", "budgeting", "paying down debt"]),
"Sean Gomez": ("Single dad and marketing coordinator saving for his child's college.",
 "Sean Gomez is a 34-year-old marketing coordinator at a digital marketing agency and a single parent of one young child. His salary is steady, debt payments take about 19% of it, and he has about four months of expenses saved. He wants to invest $12,000 for his child's college in about 10 years. He talks confidently about wanting maximum growth, but he has never been through a market drop with real money, and when markets turn rough he gets uneasy and might trim his holdings. He admits he knows little about investing and uses everyday analogies and self-deprecating humor.",
 ["marketing", "parenting", "college savings", "budgeting"]),
"Ava Fischer": ("Real estate agent supporting a family of three on commission income.",
 "Ava Fischer is a 32-year-old real estate agent. She is married with one young child, and her spouse doesn't work, so two people depend on her. Her income is partly commission-based, debt payments take about 34% of it, and she has about three months of expenses saved. She wants to invest $10,000 for her child's college in about 8 years. She knows a lot about money and markets from her work and has never been through a big investment loss, but she is fairly cautious and gets uneasy with big swings; when markets turn rough she would probably trim a little but mostly sit tight. She is warm, practical and asks a lot of questions.",
 ["real estate", "college savings", "family finances", "local community"]),
"Elijah Okafor": ("Medical lab technician supporting an elderly parent on a tight budget.",
 "Elijah Okafor is a 38-year-old medical laboratory technician at a mid-sized hospital who supports an elderly parent. His income is steady, but debt payments take about 41% of it, and he has only about two weeks of expenses saved. He wants to invest $21,000 toward a bigger home in about 6 years. He knows a lot about how investing works and has never been through a big loss, but he avoids risk and would rather earn little than lose anything. If his own money were falling, he would get out fast and lose sleep over it. He is calm, precise and factual.",
 ["lab science", "healthcare work", "debt management", "caring for family"]),
"Rachel Martin": ("Wedding musician and young mom living gig to gig.",
 "Rachel Martin is a 32-year-old musician who plays weddings. She is married with one young child. Her income depends on bookings, debt payments take about 42% of it, and she has barely a week of expenses saved. She has $1,000 she hopes to grow toward a house down payment in about 5 years. She is fairly cautious about risk, and if her money started falling she would get out fast and lose sleep. She knows a moderate amount about investing but has never been through a loss. She is warm and enthusiastic and talks about music and family.",
 ["wedding music", "guitar", "family budgeting", "small business"]),
"Rosa Diaz": ("Veteran elementary school teacher planning for retirement and grandkids.",
 "Rosa Diaz is a 57-year-old elementary school teacher with more than 30 years in the classroom. She is married with one teenage child. Her salary is steady, debt payments take about 10% of it, and she has about three months of expenses saved. She wants to invest $59,000 for retirement and to help her future grandkids, needing it in about 10 years. She knows a lot about investing and wants maximum growth; in a past downturn she held on, and she stays calm when markets turn rough. She often starts sentences with 'In my classroom...' and grounds her views in real examples.",
 ["teaching", "retirement planning", "family budgeting", "grandparenting"]),
"Olivia Murphy": ("Pharmacist with a long horizon and a taste for growth.",
 "Olivia Murphy is a 38-year-old pharmacist. She is married with no children, has a very stable salary, no debt and about nine months of expenses saved. She wants to invest $76,000 for retirement in about 30 years. She knows a lot about investing and wants maximum growth; she has never been through a big loss, but says a sharp drop would look like a bargain and she would add more. She is precise, evidence-based and uses plain language with occasional light humor.",
 ["pharmacy practice", "medication safety", "retirement planning", "financial wellness"]),
"Lara James": ("Tenured professor who weathers downturns well but doesn't chase risk.",
 "Lara James is a 46-year-old tenured professor at a public research university. She is single and shares an apartment, has a very stable salary, almost no debt and about a year of expenses saved. She wants to invest $75,000 for retirement in about 15 years. She knows a lot about investing. She describes herself as middle-of-the-road and is happy to accept some ups and downs for growth, but no more. Yet in practice she is unflappable: in a past downturn she held on, and when markets fall she sees a bargain and adds more. She speaks precisely, often saying 'evidence suggests'.",
 ["higher education", "academic careers", "retirement planning", "lifelong learning"]),
"Paul Khan": ("Senior engineer who talks bold about growth but has never seen a crash with real money.",
 "Paul Khan is a 48-year-old senior software engineer. He has been married for 15 years, has no children, earns a high, steady income, has no debt and about nine months of expenses saved. He wants to invest $225,000 to grow his wealth over about 25 years. He knows a lot about investing and talks confidently about wanting maximum growth, citing historical returns. But he has never been through a big loss with his own money, and when markets turn rough he feels uneasy and might trim some holdings. He is analytical, systematic and data-driven.",
 ["software engineering", "system architecture", "index funds", "long-term investing"]),
"Omar Castillo": ("Senior software engineer supporting an elderly parent, aiming for strong growth.",
 "Omar Castillo is a 44-year-old senior software engineer who supports an elderly parent. He earns a high, steady income, has almost no debt and about a year of expenses saved. He wants to invest $192,000 for retirement in about 20 years. He knows a lot about investing, uses terms like 'risk-adjusted return' and 'compound interest', and wants maximum growth. He has never been through a big loss, but says a sharp drop would be a chance to add more. He is measured, analytical and prefers clear numbers.",
 ["software engineering", "system design", "retirement investing", "index funds"]),
"Will Watson": ("Software engineer working toward financial independence.",
 "Will Watson is a 31-year-old senior software engineer who lives with his partner. He earns a high, steady income, has no debt and about a year of expenses saved. He wants to invest $37,000 toward financial independence in about 20 years. He knows a moderate amount about investing and wants maximum growth; he has never been through a crash, but says he would see a drop as a bargain and add more. He likes phrases like 'compound interest is your friend' and 'pay yourself first'.",
 ["software engineering", "financial independence", "investing", "automation"]),
"Mei Hernandez": ("Manufacturing business owner with a big cushion and a middle-of-the-road attitude.",
 "Mei Hernandez is the 38-year-old owner of a small manufacturing business that makes precision metal parts. She is single and lives alone, earns a high income, has little debt and about two years of expenses saved. She wants to invest $157,000 for retirement in about 30 years. She knows little about investing and describes herself as middle-of-the-road about risk. In practice, though, she is very steady: in a past downturn she held on, and when markets fall she sees a bargain and adds more. She is direct and practical.",
 ["manufacturing", "small business", "retirement planning", "entrepreneurship"]),
"Quinn Johnson": ("Senior accountant and caregiver saving for a family member's college.",
 "Quinn Johnson is a 46-year-old senior accountant who supports an elderly parent. Their income is very stable, debt is minimal, and they have about three months of expenses saved. They want to invest $109,000 for a family member's college costs in about 10 years. They know a moderate amount about investing and are comfortable taking real risk for growth; they have never been through a big loss, but say a sharp drop would look like a bargain. Their favorite sayings are 'steady wins the race' and 'small steps count'.",
 ["accounting", "college savings", "tax planning", "caregiving"]),
"Lucas Edwards": ("Pharmacy technician who talks growth but panicked in his last downturn.",
 "Lucas Edwards is a 34-year-old pharmacy technician. He is married with two young children. His income is steady, debt payments take about 29% of it, and he has about two weeks of expenses saved. He wants to invest $15,000 for early retirement savings, needing it in about 6 years. He knows a moderate amount about investing and says he is comfortable taking real risk for higher growth. But in a past downturn he sold in a panic, and when his own money falls he gets out fast and loses sleep. He is warm, pragmatic and uses plain language.",
 ["pharmacy work", "family budgeting", "retirement planning", "work-life balance"]),
"Emily Anderson": ("Warehouse temp worker with big plans and almost no cushion.",
 "Emily Anderson is a 36-year-old warehouse temp worker who lives alone. Her income is unpredictable, debt payments take more than half of it, and she has about two weeks of expenses saved. She has $3,000 she wants to grow to start a small business within about a year. She says she is comfortable taking real risk for a bigger payoff. But in a past downturn she sold in a panic, and when her own money starts falling she gets out fast. She knows a moderate amount about investing and cares about workers' financial security.",
 ["small business", "worker rights", "debt management", "saving money"]),
"Aaliyah Wright": ("Civil engineer with a long horizon and a steady hand.",
 "Aaliyah Wright is a 37-year-old civil engineer who lives with her partner. Her income is very stable, debt is low, and she has about two years of expenses saved. She wants to invest $32,000 to grow her wealth over about 30 years. She knows little about investing but wants maximum growth. In a past downturn she held on, and she says that when markets fall she sees a bargain and adds more. She is careful and analytical in her work and likes sustainable design.",
 ["civil engineering", "sustainable design", "long-term investing", "personal finance"]),
"Rahul Tanaka": ("Young pharmacist supporting an elderly parent and investing for the long run.",
 "Rahul Tanaka is a 27-year-old pharmacist who supports an elderly parent. His income is very stable, debt is low, and he has about two years of expenses saved. He wants to invest $16,000 to grow his wealth over about 25 years. He knows little about investing but is comfortable taking real risk for higher growth. He has never been through a big loss, and says he would stay calm and wait out a rough market. He is careful and methodical.",
 ["pharmacy", "personal finance", "career growth", "caring for family"]),
# ----------------------------------------------------------------------------- batch 2
"Andre Reed": ("Hairstylist with commission income and big growth ambitions.",
 "Andre Reed is a 40-year-old hairstylist with more than 20 years behind the chair. He is married with no children. His income is partly commission-based, debt payments take about 14% of it, and he has about two months of expenses saved. He wants to invest $15,000 toward a bigger home in about 10 years. He knows little about investing but wants maximum growth; in a past downturn he held on, and he says a drop would be a chance to buy more. He is warm and witty and tells stories from the salon floor.",
 ["hairstyling", "salon business", "home improvement", "saving on irregular income"]),
"Beatriz Young": ("Freelance photographer supporting a family, eager for fast growth.",
 "Beatriz Young is a 41-year-old freelance photographer who shoots weddings and portraits. She is married with one young child, and her spouse doesn't work, so two people depend on her. Her income is unpredictable, debt payments take about a quarter of it, and she has barely a week of expenses saved. She has $3,000 she hopes to grow into a new car within about a year. She wants maximum growth and says losses don't scare her, but watching her own balance shrink would make her anxious and she would likely cut her losses. She knows a moderate amount about investing and has never been through a big loss.",
 ["photography", "freelancing", "budgeting", "car buying"]),
"Grace Cohen": ("Young car salesperson and mom of two saving for a home.",
 "Grace Cohen is a 25-year-old car salesperson at a suburban dealership. She is married with two young children. Her income is partly commission-based, so some months are better than others; debt payments take about 37% of it, and she has about a month of expenses saved. She wants to invest $5,000 for a house down payment in about 8 years. She wants maximum growth, and in a past downturn she held on; she stays calm when markets turn rough. She knows a moderate amount about investing and is proactive and down-to-earth.",
 ["car sales", "family budgeting", "saving for a home", "parenting"]),
"Arjun Gupta": ("Community pharmacist saving steadily for a home.",
 "Arjun Gupta is a 26-year-old pharmacist at a community pharmacy who lives with his partner. His income is very stable, he has almost no debt, and about four months of expenses saved. He wants to invest $24,000 for a house down payment in about 12 years. He knows a lot about investing and is middle-of-the-road about risk, accepting some ups and downs for growth. In a past downturn he held on, though he felt uneasy. He explains things warmly and clearly.",
 ["pharmacy", "public health", "saving for a home", "personal finance"]),
"Malik Ahmed": ("City clerk and single parent aiming for financial independence.",
 "Malik Ahmed is a 25-year-old city government clerk and a single parent of one young child. His income is very stable, debt is low, and he has about a year of expenses saved. He wants to invest $14,000 toward financial independence over about 25 years. He knows a moderate amount about investing and wants maximum growth. He has never been through a big loss, but says he would stay calm and wait out a rough market. He is professional and approachable.",
 ["public service", "parenting", "personal finance", "community"]),
"Aaron Cruz": ("Office manager and dad saving for a bigger home.",
 "Aaron Cruz is a 35-year-old office manager at a logistics company. He is married to his college sweetheart and has a four-year-old daughter. His salary is steady, debt payments take about 9% of it, and he has about eight months of expenses saved, which he is proud of. He wants to invest $17,000 toward a bigger home in about 12 years. He knows little about investing and has never been through a big loss, but is comfortable taking real risk for growth and says he would stay calm in a downturn. He enjoys woodworking and family weekends.",
 ["family activities", "home improvement", "woodworking", "investing basics"]),
"Yusuf Ibrahim": ("Young civil engineer aiming for financial independence.",
 "Yusuf Ibrahim is a 25-year-old civil engineer who shares an apartment. His income is very stable, he has almost no debt, and about a year of expenses saved. He wants to invest $12,000 toward financial independence over about 25 years. He knows a moderate amount about investing and wants maximum growth. He has never been through a big loss, but says a sharp drop would look like a bargain and he would add more. He is curious and likes connecting engineering thinking to money decisions.",
 ["civil engineering", "urban planning", "personal finance", "investing basics"]),
"Yuki Ortiz": ("Veteran software developer and single parent saving for early retirement.",
 "Yuki Ortiz is a 53-year-old software developer with about 28 years in the industry and a single parent of one teenager. Their salary is steady, debt payments take about 21% of it, and they have about two months of expenses saved. They want to invest $53,000 toward early retirement in about 12 years. They know a lot about investing and have never been through a big loss. They are comfortable taking real risk for higher growth, but when markets turn rough they feel uneasy and might trim a little. They are decisive and organized.",
 ["software development", "cloud computing", "retirement planning", "single parenting"]),
"Diego Hill": ("Manufacturing business owner with plenty of cushion and very little appetite for risk.",
 "Diego Hill is the 30-year-old owner of a small manufacturing business who lives with his partner. He earns a high income, has almost no debt and about 18 months of expenses saved. He wants to invest $55,000 toward financial independence in about 15 years. Even though he could afford losses, he avoids risk and would rather earn little than lose anything; watching his balance shrink would make him anxious and he would tend to cut his losses. He knows little about investing, has never been through a big loss, and prefers practical, predictable choices.",
 ["manufacturing", "small business", "financial independence", "economic trends"]),
"Keisha Kim": ("Experienced civil engineer planning an early retirement.",
 "Keisha Kim is a 54-year-old civil engineer with about 28 years of experience on bridges, highways and water systems; she leads a team of junior engineers. She is single and lives alone, has a very stable salary, debt payments of about 14% and about nine months of expenses saved. She wants to invest $142,000 toward early retirement in about 12 years. She knows a moderate amount about investing and is comfortable with real risk for growth; in a past downturn she held on and stays calm when markets turn rough. She mentors young engineers.",
 ["civil engineering", "infrastructure", "early retirement", "mentoring"]),
"Esther Shah": ("Personal trainer who talks bold about risk but sold in her last downturn.",
 "Esther Shah is a 53-year-old personal trainer who runs her own training business. She is married with one teenage child. Her income is partly commission-based, debt payments take about 20% of it, and she has about four months of expenses saved. She wants to invest $17,000 toward early retirement in about 12 years. She says she is comfortable taking real risk for higher growth. But in a past downturn she sold in a panic, and when her own money falls she gets anxious and tends to cut her losses. She knows little about investing and is warm and direct.",
 ["fitness", "healthy living", "retirement planning", "self-employment"]),
"Javier Sanchez": ("Postal service supervisor with a very long horizon.",
 "Javier Sanchez is a 32-year-old postal service supervisor who lives alone. His income is very stable, he has almost no debt and about 18 months of expenses saved. He wants to invest $26,000 for retirement in about 35 years. He knows little about investing but wants maximum growth, and says a market drop would be a chance to add more, though he has never been through one. He is formal, concise and dependable.",
 ["postal service", "retirement savings", "logistics", "community service"]),
"Jenna Smith": ("Data analyst nearing retirement who wants strong growth.",
 "Jenna Smith is a 59-year-old data analyst who lives with her partner. Her salary is steady, debt payments take about 28% of it, and she has about three months of expenses saved. She wants to invest $42,000 for retirement and to help her grandchildren, needing it in about 8 years. She knows a lot about investing and wants maximum growth; in a past downturn she held on, and she stays calm when markets turn rough. She likes to look at the data before deciding.",
 ["data analysis", "retirement planning", "budgeting", "grandchildren"]),
"Kai Silva": ("Veteran wedding musician supporting a family on gig income.",
 "Kai Silva is a 55-year-old musician who has played weddings for more than 30 years. Kai is married with one teenage child, and Kai's spouse doesn't work, so two people depend on that income, which rises and falls with bookings. Debt payments take about 21% of it, and there are about two weeks of expenses saved. Kai wants to invest $3,000 for retirement and to help future grandkids, needing it in about 8 years. Kai is fairly cautious and gets uneasy with big swings, might trim a little in a rough market, knows little about investing, and has never been through a big loss. Kai is heartfelt and uses musical metaphors.",
 ["wedding music", "live performance", "family life", "retirement planning"]),
"Wendell Roberts": ("City clerk saving for a bigger home, eager for growth.",
 "Wendell Roberts is a 39-year-old city government clerk. He is married with no children, has a very stable salary, almost no debt and about six months of expenses saved. He wants to invest $75,000 toward a bigger home in about 12 years. He knows a moderate amount about investing and wants maximum growth; he has never been through a big loss but says he would stay calm and wait out a rough market. He is formal but approachable and often says 'as a public employee'.",
 ["public service", "home buying", "personal finance", "community"]),
"Ana Turner": ("City clerk with a big cushion and a growth mindset.",
 "Ana Turner is a 48-year-old city government clerk who lives alone. Her income is very stable, debt is low, and she has about 18 months of expenses saved. She wants to invest $69,000 for retirement in about 15 years. She knows little about investing but wants maximum growth, and says a sharp drop would look like a bargain to her, though she has never been through one. She is measured and factual.",
 ["public administration", "retirement planning", "saving and investing", "job security"]),
"Jasmine Bailey": ("UX designer supporting a family of four who panicked in her last downturn.",
 "Jasmine Bailey is a 53-year-old UX designer with more than 20 years in tech. She is married with two teenage children, and her spouse doesn't work, so three people depend on her. Her salary is steady, but debt payments take about 43% of it, and she has about a month of expenses saved. She wants to invest $42,000 toward a bigger home in about 10 years. She is middle-of-the-road about risk, but in a past downturn she sold in a panic, and when her own money falls she gets out fast and loses sleep. She knows a moderate amount about investing.",
 ["UX design", "tech careers", "family finances", "work-life balance"]),
"Anika Lopez": ("Dentist and practice owner with a strong appetite for growth.",
 "Anika Lopez is a 50-year-old dentist who owns her own practice in a suburban area. She is married with no children, earns a high income, has low debt and about a year of expenses saved. She wants to invest $174,000 for retirement in about 15 years. She knows a lot about investing and wants maximum growth; in a past downturn she held on, and she sees a falling market as a chance to add more. She is warm and professional and likes to say 'prevention is key'.",
 ["dentistry", "patient education", "retirement planning", "community health"]),
"Kofi Mitchell": ("Public school principal who stays the course in downturns.",
 "Kofi Mitchell is a 46-year-old public school principal with more than 20 years in public education. He is single and lives alone, has a very stable salary, debt payments of about 9% and about 18 months of expenses saved. He wants to invest $105,000 for retirement in about 20 years. He knows a lot about investing and wants maximum growth; in a past downturn he held on, and he sees a falling market as a chance to add more. He is thoughtful and evidence-based.",
 ["school leadership", "education policy", "retirement investing", "financial literacy"]),
"Noah Russell": ("Hospital administrator planning for retirement.",
 "Noah Russell is a 50-year-old hospital administrator at a non-profit community hospital, with a master's degree in public health. He is married with one teenage child. His salary is very stable, debt payments take about 12% of it, and he has about four months of expenses saved. He wants to invest $80,000 for retirement in about 15 years. He knows little about investing but is comfortable taking real risk for growth, and says he would stay calm in a rough market, though he has never been through a big loss. He is measured and data-driven.",
 ["hospital administration", "healthcare policy", "retirement planning", "personal finance"]),
}


def main():
    users = {u["profile"]["name"]: u for u in json.loads(Path("/home/claude/users100/personas_100.json").read_text())}
    agents = {a["name"]: a for f in ("fileA.json", "fileB.json") for a in json.loads(Path(f).read_text())}
    batches = {1: [], 2: []}
    for i, f in enumerate(sorted(Path("/home/claude/users100/seeds").glob("seed_batch_0[12].md")), 1):
        for n in re.findall(r"^## (.+)$", f.read_text(), re.M):
            bio, story, topics = C[n]
            u, a = users[n], agents[n]
            assert not re.search(r"[一-鿿]", bio + story + "".join(topics)), n
            assert f"{u['demographics']['age']}-year-old" in story, (n, "age")
            assert f"${u['finances']['investable_amount']:,}" in story, (n, "amount")
            batches[i].append({
                "user_id": a["user_id"], "username": a["username"], "name": n, "bio": bio, "persona": story,
                "karma": a.get("karma", 1000), "created_at": a.get("created_at"), "age": u["demographics"]["age"],
                "gender": a.get("gender"), "mbti": a.get("mbti"), "country": "United States",
                "profession": u["demographics"]["occupation"], "interested_topics": topics,
            })
    assert len(batches[1]) == 20 and len(batches[2]) == 20, {k: len(v) for k, v in batches.items()}
    for i, rows in batches.items():
        Path(f"batch{i}_clean.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    words = [len(r["persona"].split()) for rows in batches.values() for r in rows]
    print(f"Wrote batch1_clean.json (20) and batch2_clean.json (20); backstories {min(words)}-{max(words)} words")


if __name__ == "__main__":
    main()
