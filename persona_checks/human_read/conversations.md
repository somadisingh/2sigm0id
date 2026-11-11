# Persona check 6: read 20 conversations and guess the band

Each conversation is a real run of method D (the adaptive interviewer) with one AI test user.
We removed the true profiles. Your task: read each conversation and guess the person's final
band. This tells us if a person can see the profile in the answers, as the AI model must.

## The bands

Each person has three scores. Each score has a band from 1 (very careful) to 5 (very bold):

- **Capacity**: how much loss the person can afford. Look at the years until they need the
  money, emergency savings, income stability, debt payments and dependents.
- **Willingness**: how the person *says* they feel about risk.
- **Behavior**: what the person *does*, or would do, in a real loss.

The **final band is the lowest of the three bands**. Example: capacity 4, willingness 5,
behavior 2 gives final band 2.

## Steps

1. Read one conversation.
2. In `guesses.csv`, in your column, write the final band (1 to 5) for that conversation ID.
3. If you are not sure, write your best guess and add a note.
4. Do not open `key_DO_NOT_OPEN.json`. Do not talk about your guesses with the others before
   all three of you finish.
5. When all three columns are full, run `python check_personas.py human-read score`.

Some answers are vague or contradict earlier answers on purpose. That is planned noise.


---

## C01

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Eh, probably the coin flip, but honestly I’m not super sure. Depends on the day, I guess.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d probably just leave it alone and wait it out. I’m not the type to panic-sell.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Not much, honestly. We keep it pretty manageable.

**Q4.** Roughly what percentage of your income goes toward debt payments each month?

> Um, maybe around a fifth? I don’t keep exact track, but it feels like a decent chunk.

**Q5.** Just to be clear, would you say your monthly debt payments are roughly 20% of your income, or is it more like a smaller amount?

> Nah, it’s smaller than that. Maybe like a tiny bit, you know?

**Q6.** How would a close friend describe you when it comes to risk with money?

> Probably say I’m pretty bold, maybe even a bit reckless. But I feel good about taking chances.

**Q7.** When markets are falling, how often do you think you'd check your account?

> I dunno, maybe sometimes? I might peek, but I wouldn’t stress over it.

**Q8.** Roughly how many years from now do you think you'll need most of this money?

> Oh, a long ways off—like 30 to 40 years, I think.

**Q9.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> I’ve got a good cushion, probably around a year and a half. That feels safe to me.

**Q10.** If your investments fell 25% and stayed down for a whole year, how would that feel day to day?

> Eh, I guess I’d deal with it. Probably not great, but I’d try not to think about it too much.


---

## C02

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Give me the coin flip. I like the odds, and even if I lose, I’m not gonna lose sleep over it. I’d rather go for the bigger payoff.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d probably buy more, honestly. That drop just looks like a discount to me, and I’m not worried about the short-term noise. I’d hold tight and add to my position.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Eh, it’s a decent chunk, but nothing crazy. I’m handling it fine, so I don’t really think about the exact number.

**Q4.** Roughly what percent of your income goes toward debt payments each month?

> I’d say around 18% or so. It’s manageable, and I’ve got a good cushion saved up, so it doesn’t stress me out.

**Q5.** When markets are falling, how often do you think you'd check your account?

> Probably every day, honestly. I like to see what’s happening, but it doesn’t make me panic—I just see it as a chance to buy more.

**Q6.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> The last one, for sure. I want the biggest possible upside, even if it means more swings. I can handle the low end, so give me that range.

**Q7.** Roughly how many years from now do you think you'll need most of this money?

> Probably around 8 years or so. I’m aiming for early retirement, so I want it to grow as much as possible before then, even if it’s bumpy.

**Q8.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> I’ve got about 4 months of expenses tucked away, so I’d be okay for a bit. That gives me some breathing room before I’d need to touch anything else.

**Q9.** How steady is your income from month to month?

> It’s pretty steady—I’m a medical lab tech, so the pay is reliable. I don’t worry about big swings in my paycheck.

**Q10.** Just to make sure I have this right — is about 8 years the time when you expect to need most of this money, or could that timing change?

> Yeah, 8 years is the plan, but I’m flexible. If the market’s doing well, I might even wait longer. If it’s not, I can still hold off.


---

## C03

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Coin flip sounds good to me. I'll take the chance—worst case, I lose a bit, but the upside is way better.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d probably buy more, honestly. A dip like that is just a sale on future growth. I’d hold what I have and add if I could.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Not much—maybe a couple percent of my take-home. It’s pretty manageable.

**Q4.** When markets are falling, how often do you think you'd check your account?

> I’d check more often, I guess, but not because I’m nervous. I just want to spot the bargains and see if I can add more.

**Q5.** Roughly how many years from now do you think you'll need most of this money?

> Probably around 25 years out. I’m thinking long-term, not for anything soon.

**Q6.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> Around a year, give or take. I like having that cushion, so it’s not much of a worry.

**Q7.** You mentioned debt payments are a couple percent of your take-home pay—roughly what dollar amount or percentage of your monthly income does that come to?

> It’s pretty small—maybe around 2% or so, but honestly, I don’t track it down to the dollar. It’s just not a big factor in my budget.

**Q8.** How steady is your income from month to month?

> It’s pretty steady, I’d say. Law firm pay is predictable, though bonuses can vary a bit. I don’t stress about it.

**Q9.** You said you'll probably need most of this money in around 25 years — can you confirm that's the right timeframe, or is it closer to a different number?

> Yeah, I’m pretty sure it’s about 25 years. I want it for financial independence down the line, so that timeframe feels right.

**Q10.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> I’d take the widest range—between $7,000 and $13,500. The upside is worth the swing to me.


---

## C04

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Oh, well, that’s an easy one for me. I’d take the sure $1,000, no question. I mean, a guaranteed $1,000 is real money I can count on, you know? The coin flip sounds exciting, but the thought of walking away with nothing just doesn’t sit well with me. I guess I’m just not a gambler at heart. Maybe if I were younger or had more cushion, but not now.

**Q2.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> Hmm, let me think. I’d probably pick the one between $9,900 and $10,300, honestly. It’s not exciting, but I’d sleep fine knowing I’m not going to wake up to a huge drop. The bigger ranges sound tempting, but I get nervous just thinking about the lower end. I guess I’d rather have steady and small than wild and risky. Maybe if I had more saved up, I’d take a bigger chance, but not right now.

**Q3.** When you hear 'investment risk', what's the first thing that comes to mind?

> Oh, I guess the first thing I think of is losing money, plain and simple. Like, you put your hard-earned cash in, and suddenly it’s worth less than what you started with. That really scares me, to be honest. I know risk can mean higher returns, but my stomach just knots up when I imagine watching the numbers drop. I’d rather have less growth but know I won’t be up all night worrying.

**Q4.** Say your investments dropped 20% in a single month. What would you actually do?

> Oh, wow, that would really shake me up. I mean, 20% in a month? I’d probably panic first, I’m not gonna lie. I’d be tempted to sell everything right away to stop the bleeding, even if it means locking in the loss. I’d probably lose sleep over it, checking my accounts constantly. Maybe I’d call my advisor and ask if I should just pull out, but deep down I know that’s probably the worst move. Still, it’s hard to think straight when you see that much money vanish.

**Q5.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> I’d say around 20% goes to debt payments, maybe a little more on a slow month. It’s mostly my mortgage and a car loan, plus some credit card stuff I’m trying to keep down. Since my income is partly commission, some months are tighter than others, so I try to keep those payments steady. It’s not overwhelming, but it’s enough that I notice it. I guess I’m just careful not to let it get higher.

**Q6.** When markets are falling, how often do you think you'd check your account?

> Oh, I’d probably check it way too often, honestly. Maybe every day, sometimes twice a day if it’s a bad week. I know that’s not great for my nerves, but I can’t help it—I need to see what’s happening. If it’s really dropping, I might even check it at night before bed, which just makes me anxious. I guess I’d try to remind myself it’s long-term, but my brain doesn’t always listen.

**Q7.** Roughly how many years from now do you think you'll need most of this money?

> I’m thinking about six years, give or take. That’s when I’d like to start tapping into it, maybe for retirement and helping out my grandkids. I know it’s not super far off, so I don’t want to be too wild with it. I’d rather have it mostly there when I need it than chase big gains and risk it shrinking. That timeframe kind of shapes everything for me, I guess.

**Q8.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> Probably just about one month, maybe a little less if I’m being honest. I’ve been meaning to build that up, but with commissions being uneven, it’s hard to set aside as much as I’d like. That’s one reason I’m cautious with investments—I don’t have a huge cushion to fall back on. If things got tight, I’d have to start selling stuff or dip into credit, which scares me. So yeah, one month is about it.

**Q9.** Just to make sure I have it right — could your savings cover about one month of essential expenses, or is it closer to a little less than one month?

> Yeah, I’d say it’s right around one month, maybe just under it. I keep telling myself to add more, but life gets in the way, you know? It’s enough to get by for a bit, but not enough to feel really safe. I guess that’s why I’m so careful with anything that feels risky.

**Q10.** If your investments fell 25% and stayed down for a whole year, how would that feel day to day?

> Oh, that would be rough, real rough. I’d probably be checking my accounts every morning and losing sleep most nights. I’d keep thinking about all the work I put into that money and how long it’d take to get it back. I might even start talking myself into selling just to stop the pain, even though I know that’s probably the worst thing to do. Honestly, I’d be miserable the whole year. I’d rather have smaller, steadier gains than go through that.


---

## C05

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Honestly, I’d take the coin flip. A shot at $2,500 with a 50% chance of zero—that’s an expected value of $1,250, so the math favors it. And I’m not going to lose sleep over a $1,000 downside when I’ve got a solid emergency buffer. I’ve seen bigger drawdowns in my portfolio and held through them; that’s just the cost of playing for real gains.

**Q2.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Roughly nine percent of my gross monthly income goes to debt service—mostly my mortgage and a car note. I’ve kept it manageable; no consumer credit card balances to speak of. With my cash flow, that’s comfortable, and it frees up plenty to deploy into investments. I like keeping leverage low but not zero—it’s a tool, not a burden.

**Q3.** Just to confirm—is the roughly nine percent figure based on your gross monthly income, and does it include all debt payments such as your mortgage, car note, and any other loans?

> Yes, that’s correct—nine percent of my gross monthly income accounts for all recurring debt payments, including the mortgage and the car note. I don’t carry any other installment loans or revolving balances. I track this quarterly, and it’s stayed in that band for years. It’s low enough that I could service it even if my practice had a slow month, but I’m not in a rush to pay down cheap fixed-rate debt when I can put capital to work elsewhere.

**Q4.** Roughly how many years from now do you think you'll need most of this money?

> I’m looking at a 15-year horizon. That’s when I plan to step back from full-time practice, so I’ll want to start drawing on these funds then. I’m not planning to touch a penny before that—my emergency fund and current income cover any short-term needs. Fifteen years gives me plenty of runway to ride out volatility and compound growth. I’m comfortable with that timeline.

**Q5.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> I’ve got about 12 months of expenses tucked away in liquid, low-yield accounts. That’s not earning much, but it’s not meant to—it’s insurance. If my paycheck stopped tomorrow, I could keep the lights on and the loan payments current for a full year without touching my investment portfolio. Honestly, I could stretch it longer if I trimmed discretionary spending, but 12 months is the number I use.

**Q6.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> I’d take the widest range—$7,000 to $13,500. That asymmetric upside is exactly what I’m after at this stage. A 30% downside worst case doesn’t faze me; I’ve held through worse and added to positions. The potential 35% gain on the high end is worth the volatility. In 15 years, these swings are just noise. I want maximum growth, not a padded landing.

**Q7.** Just to confirm—do your savings cover about 12 months of essential expenses, or is that 12 months including things like discretionary spending that could be trimmed?

> That’s 12 months of essential expenses—mortgage, utilities, groceries, insurance, the car payment. I’ve deliberately budgeted for the bare-bones number, not the lifestyle number. If I had to, I could trim further—cancel subscriptions, eat out less—and stretch it to maybe 15 months. But the baseline is solidly 12 months of non-negotiables. That’s what I’m comfortable with.

**Q8.** How steady is your income from month to month?

> My income is very steady. I run my own dental practice, and it’s been stable for over two decades—revenue fluctuates maybe 5-10% seasonally, but it never dips anywhere near a crisis. I’ve got a solid patient base and low overhead relative to my gross. I’m not worried about volatility on the income side; that’s why I can afford to be aggressive with investments. If anything, my monthly cash flow gives me dry powder to deploy when markets dip.

**Q9.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d see that as a gift, honestly. A 20% haircut across the board means valuations just got more attractive, so I’d likely reallocate some cash into equities—maybe even shift a portion of my emergency cushion if it’s a true panic. I’ve done exactly that in past corrections: held my positions and added on weakness. I’m not panic-selling; I’m buying the dip. Over my 15-year horizon, that kind of move tends to pay off handsomely.

**Q10.** Just to make sure I have this right: is nine percent of your gross monthly income the total for all debt payments, and is there anything like a business loan or line of credit that isn't included in that figure?

> That nine percent is strictly personal debt—mortgage and car note. My practice’s business loans and equipment leases are separate and managed through the LLC, so they don’t touch my personal cash flow. I keep the two completely distinct for tax and liability reasons. So, yes, nine percent of gross personal income covers all my personal obligations. No hidden personal lines of credit or student loans lurking.


---

## C06

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Hmm, that's a straightforward expected value question. The coin flip has an expected value of $1,250, which is more than the sure $1,000, but I’m a cautious person at heart. I’d probably take the sure $1,000, honestly. The extra $250 isn’t worth the stomach drop of getting nothing, even if I know the math says otherwise. I can sleep better with a guaranteed outcome.

**Q2.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> That’s a good way to frame it—it really comes down to how much volatility you can stomach versus the upside you’re chasing. The first range feels almost like a savings account, which is safe but doesn’t do much for long-term growth. The wider ones offer more reward, but the downside gets uncomfortable, especially with retirement in mind. I guess I’d lean toward something in the middle, but honestly, it depends on the time horizon and what else I’ve got in the portfolio.

**Q3.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d probably grimace, check the news to see if it was systemic or something specific, and then... not touch anything. I’ve been through dips before, and selling at the bottom is the classic mistake—I know the math says stay the course, and I’ve held on in the past. With a 25-year horizon, a 20% drop is just noise, even if it doesn’t feel that way at the moment. I’d maybe rebalance if I had cash, but I wouldn’t panic. My wife would probably ask about it, and I’d give her the same calm answer.

**Q4.** When you hear 'investment risk', what's the first thing that comes to mind?

> Investment risk... that’s a broad term, isn’t it? It could mean a lot of things depending on the context—volatility, permanent loss, inflation risk, even behavioral risk like making a bad decision under stress. I guess I’d say it’s mostly about the chance that things don’t go as planned, but that’s pretty obvious. Different people define it differently, so it’s hard to pin down one clear thought. I suppose it just depends on what you’re comparing it to.

**Q5.** If a friend told you they'd made a lot on a risky investment, how would you react?

> I’d congratulate them, sure—good for them if it worked out. But I’d also quietly think about whether they’d sized it right and if they could handle a similar loss, because that’s the flip side. I’ve seen people get lucky and then assume it’s skill, which can be dangerous. I’d probably ask them a few questions about their time horizon and how they’d feel if it dropped 40% tomorrow. But I wouldn’t lecture them; their risk tolerance is their business.

**Q6.** What would bother you more, losing a lot of money or missing out on a big gain?

> Losing money would bother me more, without a doubt. Missing a gain stings a little, sure, but it doesn’t hurt my principal or my sleep. A big loss feels like a real setback, even if it’s paper, and it’s harder to explain to my family when they see the account balance. I’d rather leave some upside on the table than risk what I already have. That’s probably why I lean toward balanced portfolios and avoid the hot stocks. It’s just my temperament, I guess.

**Q7.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Roughly 19% of my monthly income goes to debt payments—mostly the mortgage and one car loan. That’s manageable, and it leaves enough room to save and invest, which matters to me. We don’t carry credit card balances, so that helps keep the number stable. I’d feel uncomfortable if it crept much higher, honestly. It’s a decent spot to be in.

**Q8.** When markets are falling, how often do you think you'd check your account?

> Honestly, I’d probably check it every single day, maybe even a couple times a day when things are really sliding. I know that’s not the textbook advice—you’re supposed to ignore short-term noise—but I’d want to see how bad it gets so I can react if needed. I’d tell myself it’s just monitoring, not trading, but I’d still be glued to the screen. It would make me uneasy, but I’d feel worse not knowing. That’s just how I’d handle it.

**Q9.** If your investments fell 25% and stayed down for a whole year, how would that feel day to day?

> That’s a tough scenario to picture, honestly. A year is a long time, and it would probably weigh on me more than I’d like to admit, especially with the kids and everything else. I’d try to keep perspective, but I’m sure there’d be some restless nights. It’s one of those things you can’t really know until you’re in it. I’d hope I’d stay disciplined, but I can’t promise I wouldn’t second-guess myself.

**Q10.** Just to confirm, is about 19% of your monthly income still the right figure for your total debt payments, or has that share changed recently?

> Actually, I think it might be a bit higher now—maybe around 22% or so. I said 19% earlier, but I’m second-guessing that because we just refinanced the car and the new payment is a little steeper. It’s still comfortable, but I don’t want to give you a number that’s too rosy. I’d rather be precise than optimistic. So yeah, let’s say it’s closer to 22% these days.


---

## C07

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> I mean, it depends on the context and what I’m using the money for. For fun money, maybe the flip; for something I need, the sure thing. I don’t have a hard rule.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d probably just let it sit and see how things play out. Markets move around, so I don’t feel the need to react to every swing. I’d keep an eye on the fundamentals and decide later.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> It’s pretty manageable, actually—maybe around 10% or so. I’ve kept my debt load low over the years, so it doesn’t eat up much of my paycheck.

**Q4.** How would a close friend describe you when it comes to risk with money?

> Probably says I’m pretty laid-back about it, not one to panic or chase trends. I tend to look at the long game rather than get caught up in short-term noise.

**Q5.** When markets are falling, how often do you think you'd check your account?

> I check it when I need to, not on a fixed schedule. It’s more about staying informed without getting distracted by daily moves.

**Q6.** For this money, is it more important to protect what you have or to grow it?

> Honestly, it depends on the timeframe and the specific goal. I can see the logic in both approaches, so it’s not a simple either-or for me. I’d probably weigh it against my overall plan.

**Q7.** How much of this money would you feel okay putting into stocks?

> I guess it depends on the market conditions and what the rest of my portfolio looks like. I’d say I’m comfortable with a decent chunk, but I don’t have a fixed percentage in mind. Just depends.

**Q8.** Just to make sure I have it right—roughly what percentage of your income goes toward debt payments each month: is it about 10%, or is it a different amount?

> Yeah, I’d say it’s somewhere in that neighborhood. Not a precise figure I keep track of every month, but it doesn’t feel like a big burden.

**Q9.** Roughly how many years from now do you think you'll need most of this money?

> Probably around 20 years from now. That’s the timeline I’m thinking for retirement.

**Q10.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> Probably about six months or so, maybe a bit more if I tighten up spending. I like having a cushion, so it’s not something I want to stretch too thin.


---

## C08

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Honestly? Give me the coin flip. I know the math: expected value is $1,250, which is better than a guaranteed grand. And I’m not afraid of the zero—I’ve got a high risk tolerance. I’d take the shot every time.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d probably feel a knot in my stomach, not gonna lie. But I’d hold—I know selling at a loss locks it in. I might trim a little if I needed cash for bills, since my income’s uneven. But mostly I’d stay put and maybe even add a bit if I had spare cash.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Roughly 16% of my take-home goes to debt payments—car loan, a couple of credit cards, and a small personal loan. It’s manageable, but it’s a constant line in the budget. I’ve got a month of expenses parked in savings as a buffer, so I’m not sweating it.

**Q4.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> About one month, honestly. It’s tight, but it’s what I’ve built so far. With three kids and my wife’s part-time gig, I’ve learned to stretch a dollar. I know it’s not ideal, but I’m working on padding it up.

**Q5.** Roughly how many years from now do you think you'll need most of this money?

> I’m aiming for around 12 years—that’s when I’d like to seriously transition out of bartending and into part-time work. That timeline also lines up with helping my grandkids with college or maybe a down payment. So yeah, 12 years is my target horizon.

**Q6.** Just to make sure I have it right—is 12 years when you'll need most of this money, or could some of it be needed sooner for things like helping your grandkids?

> I’d say most of it is locked away for that 12-year mark. But honestly, if a grandkid needs a boost for a car or tuition before then, I might pull a small chunk if it’s not a huge hit. I like to keep flexibility—but the core is retirement.

**Q7.** When markets are falling, how often do you think you'd check your account?

> Probably daily, maybe even twice a day if it’s a bad week. I’m glued to the numbers—I know it’s not ideal, but I can’t help it. I might feel a little jittery, but I’d force myself to stay in. I’ve never been through a big crash, so I’d watch closely but hold.

**Q8.** If your investments fell 25% and stayed down for a whole year, how would that feel day to day?

> Honestly, that would be rough. I’d be checking quotes every morning, second-guessing myself, maybe losing sleep. I know the historical odds say it could recover, but a full year of red would test my nerve. I’d probably move a small portion to cash just to feel in control, but I’d keep the bulk invested.

**Q9.** If the news kept saying a big crash might be coming, what would you do?

> I’d probably trim a bit, maybe 10% off the top, just to have dry powder if it actually dips hard. I’d watch the headlines like a hawk, but I wouldn’t panic-sell everything—that’s how you miss the rebound. I know market timing is a fool’s game, but a little caution feels right.

**Q10.** How would a close friend describe you when it comes to risk with money?

> They’d say I’m the guy who’s always chasing growth—aggressive, talks about alpha and diversification at parties. But they’d also laugh and note I get twitchy when numbers drop. So maybe they’d call me a paper tiger: loud about risk, but a bit shaky when it hits the fan.


---

## C09

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> I'd take the coin flip, honestly. A shot at $2,500 beats a guaranteed grand to me. I guess I just like the upside.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> Probably see it as a buying opportunity, you know? I'd put more in while prices are low. It doesn't really scare me, I guess.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Maybe around nine percent of my income goes to debt payments. It's manageable, and I don't stress about it much. I'd rather focus on investing.

**Q4.** When markets are falling, how often do you think you'd check your account?

> Probably a lot more, to be honest. I'd want to see how far it's dropping—maybe to see if it’s a good time to add more. I guess I just get curious.

**Q5.** If your investments fell 25% and stayed down for a whole year, how would that feel day to day?

> It wouldn't really bother me, I think. I'd just see it as a chance to buy more while it's cheap. It's all about the long game, right?

**Q6.** You mentioned that maybe around nine percent of your income goes to debt payments - could you tell us more clearly what percentage of your income goes toward debt payments each month?

> Right, it's about nine percent—maybe a little under. That's all I've got, really. It's not a big deal for me.

**Q7.** Roughly how many years from now do you think you'll need most of this money?

> Probably around 25 years or so. I'm not looking to touch it anytime soon. That's plenty of time for growth, I guess.

**Q8.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> I’ve got about 18 months of expenses saved up. So I’d be fine for a while, no panic. I guess that gives me some comfort.

**Q9.** If the news kept saying a big crash might be coming, what would you do?

> I’d probably keep investing like normal, maybe even a bit more aggressive. The news always predicts crashes, and I’m not fazed by that talk. I’m in it for the long haul.

**Q10.** How steady is your income from month to month?

> It's pretty steady, I'd say. Being a physician, my income is consistent and on the higher side. I don't worry about month-to-month swings.


---

## C10

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Oh, I’d take the coin flip, no question. I mean, a thousand bucks is nice, but the chance at two and a half grand is way more exciting. And if it lands on nothing, well, that’s just part of the game. I’m not scared of losing a bet like that—I usually see it as a chance to go bigger next time. Yeah, I’d flip that coin every time.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> Hmm, that’s a tough one, honestly. I mean, on paper, I’d say I’d just ride it out, you know? But when it actually happens, it’s a bit different in the moment. I’d probably look at my numbers and think about whether it’s a good time to add more. But yeah, I can’t say for sure until I’m in that spot. I guess I’d just see how I feel.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Not a lot, really. It’s about 5% of my income, so it’s pretty manageable. I don’t carry much debt at all—just a small car payment and some monthly stuff like that. I’ve got it under control, so it doesn’t stress me out. It leaves me plenty of room to invest and save.

**Q4.** Just to be clear, is it right that debt payments take up about 5% of your income each month, or is the amount different?

> Yeah, that’s about right. It’s roughly 5% of my monthly income, maybe a little less. I keep it pretty steady, so I don’t see it changing much. It’s not a big deal for me, honestly. I’ve got it all planned out, and it leaves me plenty of breathing room.

**Q5.** Roughly how many years from now do you think you'll need most of this money?

> Oh, I’m thinking long-term here. I’d say about 30 years out, maybe a bit more. I want to grow it for retirement, not touch it anytime soon. That gives me a lot of time to let it ride through ups and downs. I’m not in a hurry, you know? Just want it to build up over the decades.

**Q6.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> Oh, you know, I’ve got a nice cushion tucked away. It’s enough that I wouldn’t have to panic right away, that’s for sure. I try to keep a solid buffer, but I don’t really count down the months exactly. I just like knowing it’s there if I need it. It gives me peace of mind, even if I don’t think about the precise number.

**Q7.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> Honestly, I’d go for the last one—between $7,000 and $13,500. I know that sounds risky, but I like the idea of big upside. I mean, if it drops to $7,000, that just looks like a bargain to me. I’d probably put even more in at that point. I’m not scared of the swings, and I’ve got time to recover. Yeah, that’s my pick.

**Q8.** How steady is your income from month to month?

> It’s very steady, actually. I’m a civil engineer, and my job is pretty stable—government and infrastructure projects don’t just stop overnight. I get a solid paycheck every month, and I don’t worry about it changing much. It’s a good feeling, knowing that the money’s coming in regularly. That stability lets me take bigger risks with my investments, honestly.

**Q9.** If you had to make a rough guess, about how many months of your essential expenses could your savings cover?

> I’d say about two years’ worth, maybe a little more. I’ve built up a nice emergency fund over time, and I try not to dip into it unless it’s really necessary. It’s more than enough to keep me comfortable if something unexpected happens. Honestly, I don’t stress about it—I’ve got that covered.

**Q10.** Earlier you mentioned you weren't sure of the exact number, but also said your savings could cover about two years of essential expenses—roughly how many months would you say it is?

> Oh, right, I guess I did say that. Let me think—yeah, I’d say it’s around 24 months, maybe a bit more. I’ve been saving up for a while and keep it in a separate account so I don’t touch it. It’s a good safety net, and I don’t really worry about running out. Two years feels like a solid cushion to me.


---

## C11

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> I'd take the coin flip. I like the chance to get more, even if it might not work out. That's how I think about growing money.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d probably just stay put and wait it out. I haven’t really been through a big drop before, but I think I’d keep my cool and not sell anything.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Roughly nine percent of my income goes to debt payments. It’s not too heavy, so I feel like I have room to save more.

**Q4.** You mentioned about nine percent of your income goes to debt payments — is that still about right, or has that share changed?

> It’s probably still around that ballpark. Things flex a little month to month, but nothing major has changed that I know of.

**Q5.** When markets are falling, how often do you think you'd check your account?

> Probably not too often, maybe once a week. I’m not the type to watch every tick, even when things get rough.

**Q6.** Roughly how many years from now do you think you'll need most of this money?

> I’m thinking about 12 years from now. That’s when we’re hoping to buy a bigger place, so I’d need the money around then.

**Q7.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> I’ve got about eight months of expenses saved up. That feels like a decent cushion if something unexpected happens.

**Q8.** How steady is your income from month to month?

> My income is pretty steady, honestly. It’s a regular office job, so I don’t worry much about big ups and downs.

**Q9.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> I’d go with the wider range, like between $8,500 and $11,800. That gives me a real shot at growth, and I can handle some ups and downs.

**Q10.** When you hear 'investment risk', what's the first thing that comes to mind?

> I think of it as the chance you might lose some money, but also the chance you could make more. I feel okay with that trade-off.


---

## C12

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> I'd take the sure $1,000. Big swings aren't my thing, even if the possible upside is bigger. A guaranteed amount feels safer to me.

**Q2.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> I'd pick the $9,900 to $10,300 range. That feels steady and predictable, which I like. The bigger ranges might offer more, but they'd make me uneasy.

**Q3.** Say your investments dropped 20% in a single month. What would you actually do?

> I'd probably hold steady and not panic. I know markets go up and down, and I wouldn't want to sell at a loss. I'd just wait it out and see if it recovers.

**Q4.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> About 9% of my income goes to debt payments each month. It's manageable and not a big burden.

**Q5.** When markets are falling, how often do you think you'd check your account?

> Probably not every day, maybe once a week or so. I'd want to keep an eye on it, but I wouldn't want to stress myself out checking constantly.

**Q6.** Roughly how many years from now do you think you'll need most of this money?

> I'm thinking about 25 years from now. That gives me plenty of time to let it grow steadily.

**Q7.** Just to make sure I have this right—is it about 9% of your income that goes to debt payments each month, or is that number different now?

> Yeah, that's still right—about 9% of my income goes to debt payments each month. It hasn't changed recently.

**Q8.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> I've got about 12 months of expenses saved, so that would cover us for a while. It's a good cushion if something unexpected happens.

**Q9.** How steady is your income from month to month?

> It’s very steady—I work in hospital administration, so my salary doesn’t fluctuate much. I don’t worry about sudden drops in income.

**Q10.** Just to make sure I have this right — do you expect to need most of this money in about 25 years, or is that timeframe still flexible?

> Yes, I’m aiming for about 25 years from now. That timeframe is pretty firm for my plans, though I’m open to adjusting if things change down the road.


---

## C13

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Oh, that's a tough one, I guess. I think I'd take the sure $1,000, honestly. The coin flip is tempting—$2,500 would be nice—but the thought of getting nothing just makes me uneasy. I'm not one for big gambles, even with the odds technically in my favor. I'd rather lock in something predictable.

**Q2.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> Hmm, that's a lot to think about. I guess the first one, the $9,900 to $10,300 range, is the most comfortable for me. The other options—especially the last two—have way too much downside for my taste. Even if the upside is bigger, seeing my $10,000 dip to $8,500 or $7,000 would really stress me out. I'd rather give up some potential gain to keep the swings small. It's just how I sleep at night.

**Q3.** Say your investments dropped 20% in a single month. What would you actually do?

> Oh, that would be rough, no question. I'd probably feel pretty anxious, maybe check my account more than I should. I might trim a little—sell a small slice just to feel like I'm doing something—but I wouldn't dump everything. Past experience tells me markets bounce back eventually, so I'd mostly hold on and wait. Still, I'd be second-guessing myself the whole time, I guess.

**Q4.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> I'd say roughly 15% of my income goes to debt payments each month. It's not crushing, but it's not negligible either. I keep it manageable, but I'm not in a rush to pay everything off early. I'd rather keep some cash available for emergencies, even if it's not much right now.

**Q5.** Roughly how many years from now do you think you'll need most of this money?

> Well, it's hard to pin down exactly, you know? I suppose it's somewhere down the road—maybe not too distant, but not tomorrow either. I'm thinking more along the lines of a few years, maybe around half a decade or so, but things can shift. It depends on how the job market goes and what life throws at me. I'd rather keep my options open than commit to a hard date.

**Q6.** Just so I have it right — do you expect to need most of this money in about five years, or is that still uncertain for you?

> Yeah, five years is probably a fair ballpark, I guess. It's not a hard deadline, but that's roughly when I'd start tapping into it for retirement planning. I mean, if things go sideways, I might need it sooner, but I'm not counting on that. So, let's say five years is the working assumption.

**Q7.** When markets are falling, how often do you think you'd check your account?

> Oh, I'd probably check it more than I should, honestly. Maybe a couple times a week, sometimes daily if things are really volatile. I know that's not great for my nerves, but I can't help it—I like to know where I stand. I wouldn't be making big moves, but I'd be watching. It's a bit of a bad habit, I guess, but there it is.

**Q8.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> Oh, that's a sobering thought. I'd say maybe half a month, if I'm being honest—it's not much at all. I've been meaning to build it up, but life keeps getting in the way. If my paycheck stopped, I'd probably be relying on credit cards or cutting expenses to almost nothing within a couple of weeks. It's not a comfortable situation, but I know I need to fix it eventually.

**Q9.** Just to make sure I have it right: could your savings cover about two weeks of essential expenses, or is it a different amount?

> Yeah, that's about right—roughly two weeks, maybe a little less. It's not where I'd like it to be, but it's reality right now. I've been focused on other things, so I haven't prioritized building a bigger cushion. I know it's a risk, but I can't change it overnight.

**Q10.** How steady is your income from month to month?

> It's pretty steady, I'd say. I'm a software developer with a regular salary, so it doesn't fluctuate much from month to month. There's always some uncertainty in any job, but I don't have to worry about commissions or gig-based income. That predictability helps me plan, even if my savings aren't where I'd like them to be.


---

## C14

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> I guess I'd take the sure $1,000. I don't like gambling with money I need.

**Q2.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> Probably the first one, the safest. I'd rather not see big swings.

**Q3.** Say your investments dropped 20% in a single month. What would you actually do?

> I'd probably pull a lot of it out, even if it meant locking in the loss. I just can't handle watching it fall.

**Q4.** When markets are falling, how often do you think you'd check your account?

> Probably every day, maybe more. I get nervous not knowing what's happening with my money.

**Q5.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> I'd say maybe 18% or so. It feels like a lot sometimes, but I manage.

**Q6.** Roughly how many years from now do you think you'll need most of this money?

> I guess about 12 years. That's when I'm hoping to slow down a bit.

**Q7.** Just to make sure we have it right, is about 18% of your income the share that goes toward debt payments each month, or is it a different amount?

> Yeah, that sounds about right. Around 18% of my paycheck goes to debt payments.

**Q8.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> Maybe half a month, if that. It's not a lot, but I'm working on it.

**Q9.** Just to be clear, would you say your savings could cover about half a month of essential expenses, or is it a different amount?

> Yeah, about half a month, maybe a little less. It's tight.

**Q10.** When you hear 'investment risk', what's the first thing that comes to mind?

> Losing money, honestly. I'd rather keep it safe than take chances.


---

## C15

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Honestly, I’d take the coin flip every time. The upside is two and a half times the sure thing, and I’m not afraid of a zero. In my book, that’s the kind of asymmetry you want when you’re building long-term wealth. I’d rather swing for the fences than play it safe with a guaranteed small win.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> Well, a 20% monthly drop—that’s a real gut check, no question. I’d like to think I’d stay disciplined, maybe reassess my allocation if something fundamentally changed. But honestly, markets are noisy, and I’ve got a long time horizon. I’d probably just… monitor things closely, see how the next few weeks play out. No need to overreact to a single data point.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Oh, you know, it’s manageable—nothing that keeps me up at night. We’ve got the usual stuff, car payment, a bit on a card, but it’s all within a range I’m comfortable with. I’d say it’s not eating into my ability to save aggressively, which is the main thing for me. Honestly, I don’t track it to the penny every month; I just make sure the payments are automatic and I’m not carrying any high-interest balances. That’s the part that matters.

**Q4.** Roughly what percent of your monthly income goes toward debt payments like the car loan and credit card?

> I’d say it’s only about 4% of my gross income—we’ve been pretty aggressive about paying down the car loan early, so it’s not a heavy lift. Credit card gets paid in full each month, so that’s just a cash-flow thing, not real debt. I like keeping that ratio low so I can pile more into investments without feeling stretched.

**Q5.** When markets are falling, how often do you think you'd check your account?

> Oh, you know, I’d probably peek a little more than usual—just to stay in the loop, not because I’m panicking. Markets are always moving, and I like to stay informed, but I don’t obsess over daily swings. I’d say I’d check when I’m doing my normal financial routine, maybe when I’m reviewing my budget or rebalancing. It’s more about staying aware than reacting to every headline.

**Q6.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> Give me the widest range—$7,000 to $13,500. I’m in it for the long game, and that kind of volatility is just the price of admission for serious upside. I don’t need the money anytime soon, and my emergency fund covers the short term. A bigger spread means a better shot at compounding big gains over the next 20 years. I can stomach the down months as long as the trajectory is upward over time.

**Q7.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> Oh, that’s a good question, but honestly I haven’t sat down to calculate it to the month. I’ve got a solid cushion built up, enough to give me breathing room if something unexpected happened. I keep it liquid, but I don’t obsess over the exact number because I’m more focused on growing my long-term assets. Let’s just say I wouldn’t lose sleep over a short-term job gap.

**Q8.** Roughly how many months of essential expenses do you think your savings could cover - even a ballpark number like 3, 6, or 12 months would help?

> I’d ballpark it around six months, maybe a touch more if we tightened the belt. My wife and I keep an emergency fund in a high-yield savings account, separate from our brokerage stuff, so it’s there specifically for that kind of scenario. It’s not meant to be huge—just enough to buy time without touching the investments. Six months feels like the sweet spot for my risk tolerance.

**Q9.** How steady is your income from month to month?

> Honestly, it’s pretty steady, but there’s always a little variability with shift differentials and overtime. Some months I pick up extra weekend shifts, others I don’t, so the take-home wiggles a bit. It’s not a straight salary, but it’s predictable enough that I don’t worry about covering the bills. I’d say it’s stable overall, maybe more like a slow wave than a flat line.

**Q10.** Just to clarify, roughly what percentage of your income goes toward debt payments each month—is it around 4%, or do you not have an exact figure in mind?

> Yeah, I’d stick with that 4% figure—it’s an estimate, but it’s close enough. The car loan is the only real debt, and we’re paying it down faster than the minimum, so the percentage will drop over the next year or two. Credit cards are paid in full monthly, so they don’t really count as debt in my mind. Overall, it’s a very manageable load, which is why I can funnel so much into investing.


---

## C16

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Hmm, I guess I'd take the coin flip. Worse case I get nothing, but that extra $1,500 is tempting. I'm all about going for it, you know?

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d probably just leave it all alone, honestly. I know markets go up and down, and I’m in it for the long game. No panic selling from me.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Maybe around 6% of my income, it's pretty manageable. I don't carry much debt besides a small car loan and stuff. It doesn't stress me out.

**Q4.** Just to make sure we have it right: is your total monthly debt payment about 6% of your income, or is it a different amount?

> Yeah, that’s right—about 6%. It’s not a huge chunk, so I’ve got room to save more. I like keeping things simple with payments.

**Q5.** When markets are falling, how often do you think you'd check your account?

> Probably more than I should, maybe a couple times a week. But seeing red numbers wouldn’t make me sell—I’d just wait it out. I know it’ll come back eventually.

**Q6.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> I’d go with the wildest one, between $7,000 and $13,500. I want maximum growth even if it means more swings. Losses don’t really scare me.

**Q7.** Roughly how many years from now do you think you'll need most of this money?

> Probably in about 25 years, maybe a bit sooner if things go well. I’m thinking long-term for sure. No rush to touch it anytime soon.

**Q8.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> I’ve got about a year saved up for emergencies, maybe a little more. So I’d be fine for quite a while, even if things got rough. That gives me some peace of mind.

**Q9.** How steady is your income from month to month?

> It’s super steady—I work for the city, so my paycheck is predictable every month. No surprises there. That makes planning easier.

**Q10.** You mentioned needing most of this money in about 25 years, but possibly sooner — roughly what year or age do you expect to actually need it?

> I’ll be around 50 in 25 years, so that’s probably when I’d want to stop working full-time. Maybe a bit before that if I can manage it. It’s kind of my target for financial independence.


---

## C17

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> Hmm, I mean, a sure $1,000 is nice, but that coin flip could double it and then some. I like to think I’d take the gamble, especially since I’ve got a good cushion saved up. If I lost, I’d be annoyed but not hurt. I guess I lean toward the coin flip because I’ve seen taking a chance pay off before, even when it felt risky at the time.

**Q2.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Oh, you know, it’s not too bad, honestly. I keep it pretty manageable—some months it feels a bit higher, some months lower. I’d say it’s maybe around a tenth or so, if I had to guess. It’s not something I stress about, but I do keep an eye on it. I think I’ve got a decent handle on things, so I don’t lose sleep over it.

**Q3.** Just to clarify, when you say around a tenth of your income goes to debt payments, is that roughly 10% each month, or does the amount vary quite a bit from month to month?

> Oh, it’s kind of one of those things that shifts around, you know? Some months it’s a little more, some months a little less, depending on what’s due and what’s been going on. I try not to get too hung up on the exact number because it’s not a huge worry for me. I’d say it’s in that general ballpark, but I couldn’t pin it down to the exact percentage if I tried. It’s just one of those things I handle as it comes up.

**Q4.** How would a close friend describe you when it comes to risk with money?

> Oh, you know, I think my friends would say I’m pretty laid-back about money, like I don’t get all worked up over the ups and downs. They’d probably say I’m the type who goes with the flow, but I’m not reckless or anything—just sort of steady, I guess. I mean, I’ve got my safety net, so maybe that makes me a little more relaxed than some people I know. They might even joke that I’m a bit of a mixed bag, not too bold but not too cautious either. Hard to say, honestly—I don’t usually talk numbers with them, just the general vibe.

**Q5.** Roughly how many years from now do you think you'll need most of this money?

> Oh, I mean, I’ve been thinking about this—probably around 30 years, maybe a bit less, to be honest. Retirement feels like a long way off, but I know time sneaks up on you. I’d rather say 25 years just to be safe, so I’m not caught off guard. That’s probably when I’ll want to start pulling from it, I think. Yeah, somewhere in that range seems right to me.

**Q6.** Say your investments dropped 20% in a single month. What would you actually do?

> Hmm, that’s a tough one because I don’t usually like to think about those big swings too much. I guess I’d probably just wait it out, maybe check my numbers but not do anything dramatic right away. Sometimes you just have to let things settle, you know? I’m not the type to panic sell or jump in headfirst—I like to take a breath and see how it plays out. But honestly, I might also see it as a chance to put a little more in, if I had the cash handy. I don’t know, it’s hard to say until you’re actually in the moment.

**Q7.** For this money, is it more important to protect what you have or to grow it?

> Oh, that’s a tricky one, isn’t it? I guess it depends on the day, you know? Some days I feel like I should just lock it up and be safe, and other days I think you’ve got to take a little risk to make it work for you. I’m not really sure I have a strong answer—I like to keep both options open, if that makes sense. Maybe it’s more about balance than picking one side. I don’t know, I guess I’d say both matter, but I’m not going to lose sleep over it either way.

**Q8.** If your paycheck stopped tomorrow, how many months could your emergency savings carry you?

> Oh, I’ve got a nice cushion built up, actually. I’d say I could get by for a good two years, maybe a little more if I really tightened my belt. I mean, I don’t like to brag, but I’ve always been one to stash away a bit extra just in case. So yeah, I’m pretty comfortable with that number. It’s not something I think about a lot, but it’s nice to know I’ve got that buffer.

**Q9.** Just to make sure I have this right — would you say your savings could cover about 24 months of essential expenses, or is it a different number?

> Oh, yeah, that sounds about right, I think. I mean, I’ve never really counted it out to the exact month, but 24 months sounds like a fair guess if I’m being honest with you. I just know I’ve got a decent amount set aside, and I don’t stress too much about running out. It’s one of those numbers I’ve got in my head, but I haven’t written it down anywhere. So sure, let’s go with that—24 months feels close enough to what I’m thinking.

**Q10.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> Hmm, that’s a real head-scratcher for me, because I don’t usually think in those kind of ranges, you know? I guess I’d lean toward the middle one—the $9,500 to $10,800—since it feels like a reasonable mix of safety and a little upside. The bigger swings make me a bit nervous, even if they could pay off more. I’m not the type to chase the highest number if it means I might lose a chunk. So yeah, I’d probably pick the middle one and just be happy with it.


---

## C18

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> I’d take the sure thing, probably. I don’t like taking chances with money.

**Q2.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> The first one—between $9,900 and $10,300. That feels safe enough.

**Q3.** When you hear 'investment risk', what's the first thing that comes to mind?

> Oh, I guess it just means things could go up or down. Hard to say more than that.

**Q4.** If a friend told you they'd made a lot on a risky investment, how would you react?

> I’d probably ask them how they did it, honestly. Sounds exciting if it works out.

**Q5.** What would bother you more, losing a lot of money or missing out on a big gain?

> Losing money, for sure. I can’t handle watching it disappear.

**Q6.** Say your investments dropped 20% in a single month. What would you actually do?

> I’d sell right away, before it drops more. I couldn’t sleep at night otherwise.

**Q7.** When markets are falling, how often do you think you'd check your account?

> Probably every day, maybe more. I’d want to know what’s happening.

**Q8.** If your investments fell 25% and stayed down for a whole year, how would that feel day to day?

> Honestly, that would eat at me. I’d be anxious and stressed the whole time.

**Q9.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> About 41% goes to debt payments. It’s a big chunk, but I manage.

**Q10.** Just to make sure I have it right — is about 41% of your income the correct figure for what goes toward debt payments each month?

> Yeah, something like that. Most months it’s not too bad. I mostly keep to myself about it.


---

## C19

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> I guess I’d take the coin flip. I mean, $2,500 sounds a lot better than a guaranteed grand, and I’m pretty aggressive about growing money fast.

**Q2.** Say your investments dropped 20% in a single month. What would you actually do?

> Well, I’d probably feel a little uneasy, but I’d try to hold on. I know you’re supposed to ride it out, so I’d maybe watch it for a bit before doing anything drastic.

**Q3.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Oh, that’s a big chunk, I guess. Maybe around half, or a little more, like 53% or so. It’s tight, but we manage.

**Q4.** Just to be clear, roughly what percentage of your income goes toward debt payments each month?

> I’m not exactly sure, but it’s a lot—maybe more than half, I think. It depends on the month, honestly, with commissions coming in different amounts.

**Q5.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> I’d go with the widest range, I guess—between $7,000 and $13,500. That gives me the best shot at maximum growth, and I’m not scared of a little loss.

**Q6.** When markets are falling, how often do you think you'd check your account?

> Oh, I’d probably check it pretty often, maybe daily, but it depends how busy I am with work and the kids. I guess I’d just keep an eye on it, but I wouldn’t overdo it.

**Q7.** If your investments fell 25% and stayed down for a whole year, how would that feel day to day?

> Yeah, that would be a tough year, I guess. I’d probably just try not to think about it too much and hope it bounces back. It’s hard to say, really.

**Q8.** If the news kept saying a big crash might be coming, what would you do?

> If the news kept saying a crash is coming, I’d probably pull out some of the money and wait until things settle. I mean, no point losing a bunch if everyone’s saying it’s going to tank, right?

**Q9.** Imagine six months have passed since a drop and you're still down 15%. What would you do?

> Hmm, I’d probably just keep it as is for now and see what happens. It’s hard to say, really—depends on how things look then.

**Q10.** Say you put in $10,000 and two weeks later it's worth $7,000. What would you do?

> Oh, that would sting. I’d probably sell a little to stop the bleeding, but I’d keep most of it in, hoping it comes back. It just feels safer to cut some losses.


---

## C20

**Q1.** Would you rather have a sure $1,000, or a coin flip between $2,500 and nothing?

> I'd take the sure $1,000. A guaranteed amount feels safer, even if the other option could give me more. I don't like the idea of losing everything.

**Q2.** Say you put in $10,000 for a year. Would you rather it end up somewhere between $9,900 and $10,300, between $9,500 and $10,800, between $8,500 and $11,800, or between $7,000 and $13,500?

> I'd go with the middle one—between $9,500 and $10,800. It's got a decent chance to grow, but I wouldn't lose too much if things go bad. That feels right for me.

**Q3.** When you hear 'investment risk', what's the first thing that comes to mind?

> It means my money could go down, maybe a lot. I know you have to take some risk to get growth, but I don't like seeing big drops. I just want a balance.

**Q4.** Say your investments dropped 20% in a single month. What would you actually do?

> I'd feel pretty uneasy, honestly. I might sell a little to stop the bleeding, but mostly I'd hold on and wait for it to bounce back. That's what I've done before.

**Q5.** If a friend told you they'd made a lot on a risky investment, how would you react?

> I'd be happy for them, but I wouldn't jump in myself. That kind of thing works for some people, but I need to sleep at night. I'd rather stick with a steady path.

**Q6.** About how much of your monthly income goes to paying off debts like loans or credit cards?

> Only about 2% of my income goes to debt payments. It's pretty manageable, so I don't stress about it much.

**Q7.** Roughly how many years from now do you think you'll need most of this money?

> Probably around 15 years from now. I'm planning for retirement, so I want it to grow decently but not be too wild.

**Q8.** Just to make sure I have this right — when you say about 2% of your income goes to debt payments, does that include all your debt payments (like credit cards, car loans, and any other loans), or only some of them?

> Yeah, that includes everything—credit cards, car, any loans. It's all together, and it's still just about 2% of my income.

**Q9.** When markets are falling, how often do you think you'd check your account?

> I'd probably check it a lot, maybe every day, when things are dropping. But since I'll need the money in about 3 years, I'd be extra careful not to panic and do something rash.

**Q10.** You mentioned two different timelines — about 15 years and about 3 years. When do you expect to need most of this money?

> Oh, I meant about 15 years—sorry if I confused things. The 3-year thing was a slip. I'm planning for retirement, so I don't need it for a while.
