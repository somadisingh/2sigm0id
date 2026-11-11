"""Retrieval for method DR: find labeled pilot answers that look like a new answer, and show
them to the extractor as worked examples (retrieval-augmented extraction).

The pool (pilot/pool.jsonl, built by `python pilot.py build`) holds spoken answers from the
10 pilot users, labeled from their TRUE profiles, never by an LLM. Pilot users are never
scored, so examples never leak a test user's answers.

Search is BM25 over the answer text, among pool answers to questions about the same thing
(the same money fact, or the same dimension). BM25 needs no model download. An embedding
model could replace score() later; nothing else would change.
"""

import json
import math
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL_PATH = HERE / "pilot" / "pool.jsonl"
WORD_RE = re.compile(r"[a-z0-9']+")
STOP = set("a an the and or but i i'm im it's its to of in on for with at my me is was be "
           "that this so just you your yeah well like really".split())
K1, B = 1.5, 0.75   # standard BM25 settings


def words(text):
    return [w for w in WORD_RE.findall(text.lower()) if w not in STOP]


def topic(item):
    """Answers are only compared with answers about the same thing."""
    return item.get("fact") or item["dimension"]


class Pool:
    def __init__(self, entries):
        self.entries = entries
        self.docs = [Counter(words(e["question"] + " " + e["answer"])) for e in entries]
        self.lens = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lens) / max(1, len(self.lens))
        df = Counter(w for d in self.docs for w in d)
        n = len(entries)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    @classmethod
    def load(cls, path=POOL_PATH):
        if not Path(path).exists():
            raise SystemExit(f"{Path(path).name} not found. Run `python pilot.py build` first.")
        return cls([json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()])

    def score(self, query, i):
        d, s = self.docs[i], 0.0
        for w in set(query):
            if w in d:
                tf = d[w]
                s += self.idf[w] * tf * (K1 + 1) / (tf + K1 * (1 - B + B * self.lens[i] / self.avg))
        return s

    def similar(self, item, question, answer, k=3, exclude_persona=None):
        """The k most similar labeled answers about the same topic."""
        q = words(question + " " + answer)
        same = [i for i, e in enumerate(self.entries)
                if e["topic"] == topic(item) and e["persona_id"] != exclude_persona]
        same.sort(key=lambda i: -self.score(q, i))
        return [self.entries[i] for i in same[:k]]


def reading(entry):
    """The correct reading of an example's main point, in the extractor's terms."""
    g = entry["gold"]
    if entry["topic"] == "income_stability":
        return f"income_stability = {g['value']}"
    if entry["dimension"] == "capacity":
        return f"{entry['topic']} = {g['value']}"
    kind = f", kind {g['kind']}" if entry["dimension"] == "behavioral" else ""
    return f"{entry['dimension']} score = {g['score']}{kind}"


def examples_block(examples):
    if not examples:
        return ""
    lines = ["Examples from other people, with the correct reading of the main point. "
             "Use them to calibrate your scores; read this answer on its own terms."]
    for e in examples:
        lines.append(f'- Question: {e["question"]}\n  Answer: "{e["answer"]}"\n  Correct: {reading(e)}')
    return "\n".join(lines) + "\n\n"
