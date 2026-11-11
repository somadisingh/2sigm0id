"""Belief engine: what the system believes about a person's risk profile, which question to
ask next, and when another question is unlikely to change the final band.

Code, not an LLM, holds the beliefs, picks each question and decides when to stop. Methods
C (adaptive form) and D (adaptive interviewer) share this engine, and A and B use it to
score their answers, so every method turns answers into a profile the same way. In method
D the LLM only does language: it turns each spoken answer into evidence and words the
clarifying questions. See BELIEF_ENGINE.md for the reasoning and the sources.

  willingness, behavioral  a probability distribution over a 0-1 grid (wide = unsure)
  capacity                 a distribution for each money fact; capacity.py's formula runs
                           on samples of the facts, so unasked facts stay uncertain
  final band               band probabilities from the lowest-of-three rule
  next question            the one whose answer tells us most about the final band
                           (expected information gain)
  stop                     when asking the rest of the budget has under a 5% chance of
                           changing the most likely final band (stochastic curtailment)

The evidence strengths (SIGMA) and LAPSE are starting guesses. Fit them on the 10 pilot
users and report how sensitive the results are to them.
"""

import numpy as np

import capacity as K
from prompts import band

DIMS = ("capacity", "willingness", "behavioral")
GRID = np.linspace(0, 1, 101)                      # willingness and behavioral values
GRID_BAND = np.array([band(x) for x in GRID])      # band of each grid value (1-5)

# Money facts and the values each can take. Income holds capacity.py's income sub-score.
FACT_GRIDS = {
    "horizon_yrs": np.arange(1, 41, dtype=float),
    "emergency_fund_months": np.arange(0, 24.01, 0.25),
    "income_stability": np.array(sorted(set(K.INCOME_SCORE.values()))),
    "debt_to_income": np.round(np.arange(0, 0.601, 0.01), 2),
    "dependents": np.arange(0, 6, dtype=float),
}
FACTS = tuple(FACT_GRIDS)

# How much one answer moves a score: the spread (standard deviation) of answers around the
# true score. Past actions are the strongest evidence, stated feelings next, and answers
# about imagined situations the weakest. Vague answers count VAGUE_FACTOR times wider.
SIGMA = {"stated": 0.20, "hypothetical": 0.25, "past": 0.15}
VAGUE_FACTOR = 2.0
PAST_ITEMS = {"BEH02", "BEH10"}   # behavior items about what the person actually did
# Chance that an answer is off (misread, careless, a contradiction). It keeps one answer
# from ruling anything out, so two answers that disagree leave both values possible.
LAPSE = 0.10
OUTSIDE = (LAPSE / 5) / (1 - LAPSE + LAPSE / 5)   # weight of a value a stated fact rules out
OUTSIDE_VAGUE = 0.30

STOP_CHANCE = 0.05     # stop when the final band has under this chance of changing
N_SAMPLES = 2000       # fact samples for the capacity distribution
N_ROLLOUTS = 100       # simulated futures for the stop rule
MAX_ASKS_PER_FACT = 3  # D may re-ask a fact to clarify it, up to this many times in all

# Two statements of a fact contradict each other when they are further apart than this
# (or 30% of the larger value). Income and past-loss scores use 0.5 on their 0-1 scale.
CONFLICT_GAP = {"horizon_yrs": 2, "emergency_fund_months": 1, "debt_to_income": 0.05,
                "dependents": 0.5}


def capacity_vec(h, e, inc, d, dep):
    """capacity.py's formula on arrays. inc is the income sub-score."""
    subs = {"horizon": np.minimum(1.0, h / K.HORIZON_FULL_YEARS),
            "emergency": np.minimum(1.0, e / K.EMERGENCY_FULL_MONTHS),
            "income": inc,
            "debt": np.maximum(0.0, 1 - d / K.DEBT_ZERO_SHARE),
            "dependents": np.maximum(0.0, 1 - K.DEPENDENT_PENALTY * dep)}
    score = sum(K.WEIGHTS[k] * subs[k] for k in K.WEIGHTS)
    f = {"horizon_yrs": h, "emergency_fund_months": e, "debt_to_income": d}
    for _, test, cap in K.CAPS:
        score = np.where(test(f), np.minimum(score, cap), score)
    return score


def evidence_kind(item):
    if item["dimension"] == "willingness":
        return "stated"
    return "past" if item["id"] in PAST_ITEMS else "hypothetical"


def item_target(item):
    """What an answer to this bank item is evidence about: a money fact or a score."""
    if item["dimension"] == "capacity":
        return ("fact", item["fact"]) if item.get("fact") in FACT_GRIDS else None
    return ("dim", item["dimension"])


def option_model(item):
    """P(option | true value) for each option and grid value, shape (options, grid).
    Options with a null score ("it's never happened to me") carry no information and are
    left out, so the rows follow scored_options(item)."""
    kind, name = item_target(item)
    opts = scored_options(item)
    n = len(opts)
    if kind == "dim":
        sigma = SIGMA[evidence_kind(item)]
        s = np.array([o["score"] for o in opts])[:, None]
        g = np.exp(-(s - GRID[None, :]) ** 2 / (2 * sigma ** 2))
        p = g / g.sum(axis=0)
    else:
        grid = FACT_GRIDS[name]
        if name == "income_stability":
            inside = np.array([np.isclose(grid, o["score"], atol=0.01) for o in opts], float)
        else:
            inside = np.array([(grid >= o["range"][0]) &
                               (grid < (o["range"][1] if o["range"][1] is not None else np.inf))
                               for o in opts], float)
        col = inside.sum(axis=0)
        p = np.where(col > 0, inside / np.maximum(col, 1), 1 / n)
    return (1 - LAPSE) * p + LAPSE / n


def scored_options(item):
    return [o for o in item["options"] if o["score"] is not None]


def entropy(p):
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def _normal(p):
    return p / p.sum()


class Belief:
    """One person's profile as probability distributions. Copy it to try out an answer."""

    def __init__(self, seed=0):
        self.dim = {d: np.full(len(GRID), 1 / len(GRID)) for d in ("willingness", "behavioral")}
        self.fact = {f: np.full(len(g), 1 / len(g)) for f, g in FACT_GRIDS.items()}
        # fixed random numbers: the same belief always gives the same capacity samples
        self.u = np.random.default_rng(seed).random((len(FACTS), N_SAMPLES))
        self.said = []   # every stated fact or past-loss score, for contradiction checks
        self._models = {}

    def copy(self):
        b = Belief.__new__(Belief)
        b.dim = {k: v.copy() for k, v in self.dim.items()}
        b.fact = {k: v.copy() for k, v in self.fact.items()}
        b.u, b.said, b._models = self.u, list(self.said), self._models
        return b

    def model(self, item):
        if item["id"] not in self._models:
            self._models[item["id"]] = option_model(item)
        return self._models[item["id"]]

    # ------------------------------------------------------------ evidence in

    def update(self, target, lik):
        kind, name = target
        store = self.dim if kind == "dim" else self.fact
        store[name] = _normal(store[name] * lik)

    def observe_option(self, item, choice):
        """A form answer: option number `choice` (1-based) of a bank item."""
        target = item_target(item)
        opt = item["options"][choice - 1] if choice else None
        if target is None or opt is None or opt["score"] is None:
            return
        row = scored_options(item).index(opt)
        self.update(target, self.model(item)[row])

    def observe_soft(self, item, q, turn=None):
        """Soft evidence: q = the probability of each of the item's options (all options, in
        order), for example from an LLM's token probabilities. A sure q acts like a form
        answer; a spread-out q moves the belief less. Returns contradiction turns."""
        target = item_target(item)
        if target is None:
            return []
        scored = [i for i, o in enumerate(item["options"]) if o["score"] is not None]
        q = np.asarray(q, float)
        null = q.sum() - q[scored].sum()   # "never happened": no information
        self.update(target, q[scored] @ self.model(item) + null / len(scored))
        top = scored[int(np.argmax(q[scored]))]
        if q[top] < 0.6:
            return []
        name = target[1]
        if item["id"] in PAST_ITEMS:
            s = float((q[scored] * [item["options"][i]["score"] for i in scored]).sum() / q[scored].sum())
            return self._conflicts("past_loss_reaction", s, s, False, turn)
        if target[0] != "fact":
            return []
        opt = item["options"][top]
        if name == "income_stability":
            return self._conflicts(name, opt["score"], opt["score"], False, turn)
        lo, hi = opt["range"]
        hi = FACT_GRIDS[name][-1] if hi is None else hi - 1e-6
        return self._conflicts(name, lo, hi, False, turn)

    def observe_fact(self, fact, low, high, vague=False, turn=None):
        """A spoken fact, as a range of values (income: its sub-score as low = high)."""
        grid = FACT_GRIDS[fact]
        inside = (grid >= low - 1e-9) & (grid <= high + 1e-9)
        if not inside.any():   # range falls between grid values: use the nearest one
            inside = np.abs(grid - (low + high) / 2) == np.abs(grid - (low + high) / 2).min()
        self.update(("fact", fact), np.where(inside, 1.0, OUTSIDE_VAGUE if vague else OUTSIDE))
        return self._conflicts(fact, low, high, vague, turn)

    def observe_score(self, dim, score, kind, vague=False, turn=None):
        """A spoken attitude (willingness) or behavior, scored 0-1 by the extractor."""
        sigma = SIGMA[kind] * (VAGUE_FACTOR if vague else 1)
        g = np.exp(-(score - GRID) ** 2 / (2 * sigma ** 2))
        self.update(("dim", dim), (1 - LAPSE) * g + LAPSE / 5)
        if dim == "behavioral" and kind == "past":
            return self._conflicts("past_loss_reaction", score, score, vague, turn)
        return []

    def _conflicts(self, fact, low, high, vague, turn):
        """Earlier clear statements of the same fact that this one contradicts. Flagged only
        when it disagrees with most of them, so once a false statement has been corrected,
        later answers that agree with the correction don't raise the flag again."""
        if vague:
            return []
        earlier = [(lo, hi, t) for f, lo, hi, t in self.said if f == fact]
        self.said.append((fact, low, high, turn))
        limit = 0.5   # income sub-score or past-loss score
        found = []
        for lo, hi, t in earlier:
            if fact in CONFLICT_GAP:
                limit = max(CONFLICT_GAP[fact], 0.3 * max(high, hi))
            if max(low - hi, lo - high) > limit:
                found.append(t)
        return found if 2 * len(found) > len(earlier) else []

    # ------------------------------------------------------------ beliefs out

    def capacity_samples(self, fact=None, p=None):
        """Capacity for N_SAMPLES draws of the facts. Pass fact and p to try a new
        distribution for one fact."""
        vals = []
        for i, f in enumerate(FACTS):
            q = p if f == fact else self.fact[f]
            idx = np.minimum(np.searchsorted(np.cumsum(q), self.u[i]), len(q) - 1)
            vals.append(FACT_GRIDS[f][idx])
        return capacity_vec(*vals)

    def band_pmfs(self, cap=None):
        """Band probabilities (index 0 = band 1) for each dimension."""
        cap = self.capacity_samples() if cap is None else cap
        out = {d: np.bincount(GRID_BAND - 1, weights=self.dim[d], minlength=5)
               for d in ("willingness", "behavioral")}
        out["capacity"] = np.bincount(np.minimum(5, np.floor(cap * 5).astype(int) + 1) - 1,
                                      minlength=5) / len(cap)
        return out

    @staticmethod
    def final_pmf(pmfs):
        """Final band = lowest of three. Dimensions are independent in this model."""
        at_least = np.ones(6)   # at_least[k] = P(final band >= k + 1)
        for p in pmfs.values():
            at_least[:5] *= np.cumsum(p[::-1])[::-1]
        at_least[5] = 0
        return at_least[:5] - at_least[1:]

    def profile(self):
        cap = self.capacity_samples()
        return {"capacity": round(float(cap.mean()), 4),
                **{d: round(float((GRID * self.dim[d]).sum()), 4) for d in ("willingness", "behavioral")}}

    def variances(self, cap=None):
        cap = self.capacity_samples() if cap is None else cap
        out = {"capacity": float(cap.var())}
        for d in ("willingness", "behavioral"):
            m = (GRID * self.dim[d]).sum()
            out[d] = float(((GRID - m) ** 2 * self.dim[d]).sum())
        return out

    def mismatch_chance(self, pmfs=None):
        """Chance that two dimensions are 2+ bands apart (the contract's mismatch rule)."""
        pmfs = pmfs or self.band_pmfs()
        c, w, b = pmfs["capacity"], pmfs["willingness"], pmfs["behavioral"]
        joint = c[:, None, None] * w[None, :, None] * b[None, None, :]
        i, j, k = np.indices((5, 5, 5))
        spread = np.maximum(np.maximum(i, j), k) - np.minimum(np.minimum(i, j), k)
        return float(joint[spread >= 2].sum())

    def mismatch(self):
        """The contract's mismatch flag: the estimated scores are 2+ bands apart, and the
        engine is fairly sure of it. (With nothing known the chance alone is 77%.)"""
        bands = [band(v) for v in self.profile().values()]
        return max(bands) - min(bands) >= 2 and self.mismatch_chance() >= 0.6

    # ------------------------------------------------------------ choosing questions

    def outcomes(self, item, base):
        """For each possible answer: its chance, and the band pmfs and variance after it.
        base = the current band pmfs."""
        kind, name = item_target(item)
        L = self.model(item)
        prior = self.dim[name] if kind == "dim" else self.fact[name]
        chance = L @ prior
        out = []
        for o in range(len(L)):
            post = _normal(prior * L[o])
            pmfs = dict(base)
            if kind == "dim":
                pmfs[name] = np.bincount(GRID_BAND - 1, weights=post, minlength=5)
                m = (GRID * post).sum()
                var = float(((GRID - m) ** 2 * post).sum())
            else:
                c = self.capacity_samples(name, post)
                pmfs = self.band_pmfs(c)
                var = float(c.var())
            out.append((float(chance[o]), pmfs, var))
        return out

    def score_items(self, items):
        """Expected information gain about the final band, and expected cut in the variance
        of the dimension the item is about, for each candidate item."""
        cap = self.capacity_samples()
        base = self.band_pmfs(cap)
        h_now, var_now = entropy(self.final_pmf(base)), self.variances(cap)
        scores = {}
        for it in items:
            outs = self.outcomes(it, base)
            gain = h_now - sum(c * entropy(self.final_pmf(p)) for c, p, _ in outs)
            var_cut = var_now[it["dimension"]] - sum(c * v for c, _, v in outs)
            scores[it["id"]] = {"gain": max(0.0, gain), "var_cut": max(0.0, var_cut)}
        return scores

    def change_chance(self, plan, seed=0):
        """Stochastic curtailment: the chance that asking every item in `plan` would change
        the most likely final band. Draws a 'true' person from the current belief, simulates
        their answers, updates a copy, and checks the band at the end."""
        now = int(np.argmax(self.final_pmf(self.band_pmfs())))
        if not plan:
            return 0.0
        rng = np.random.default_rng(seed)
        changed = 0
        for _ in range(N_ROLLOUTS):
            truth = {d: rng.choice(len(GRID), p=self.dim[d]) for d in self.dim}
            truth.update({f: rng.choice(len(FACT_GRIDS[f]), p=self.fact[f]) for f in FACTS})
            b = self.copy()
            for it in plan:
                kind, name = item_target(it)
                L = self.model(it)
                col = L[:, truth[name]]
                o = rng.choice(len(L), p=col / col.sum())
                b.update((kind, name), L[o])
            changed += int(np.argmax(b.final_pmf(b.band_pmfs()))) != now
        return changed / N_ROLLOUTS

    def choose(self, candidates, left, settled=False, seed=0):
        """Pick the next item among `candidates` with `left` questions still to ask.

        Until the band is settled, pick the item with the most expected information about
        the final band. Once asking the rest of the budget has under STOP_CHANCE of changing
        the band (where a real system would stop), the study keeps asking: pick the item
        that most cuts the uncertainty of its own dimension, to lower the error per score.
        """
        pmf = self.final_pmf(self.band_pmfs())
        scores = self.score_items(candidates)
        ranked = sorted(candidates, key=lambda it: -scores[it["id"]]["gain"])
        plan = list({it["id"]: it for it in ranked}.values())[:left]
        p_change = self.change_chance(plan, seed)
        settled = settled or p_change < STOP_CHANCE
        key = "var_cut" if settled else "gain"
        best = max(candidates, key=lambda it: scores[it["id"]][key])
        return best, {"phase": "sharpen" if settled else "settle band",
                      "value": round(scores[best["id"]][key], 5),
                      "top_band": int(np.argmax(pmf)) + 1, "top_band_chance": round(float(pmf.max()), 3),
                      "change_chance": round(p_change, 3), "settled": settled}
