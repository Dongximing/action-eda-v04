"""Prompt templates. Bump PROMPT_VERSION whenever any template changes."""
from __future__ import annotations

from .schema import Claim, Record

PROMPT_VERSION = "v0.4-p2"  # p2: optional preceding-context block; with context_k=0 identical to p1

LETTERS3 = ["A", "B", "C"]
LETTERS2 = ["A", "B"]


def _rec(r: Record) -> str:
    return f"[#{r.rid} | {r.source}] {r.text}"


def record_judgment(task: str, action: str, claim: Claim, r: Record,
                    context: list[Record] | None = None) -> str:
    """Three-option per-record judgment used by D1 / D1-f / D2 / U1 / P0 (doc §3.4).

    ``context`` = the records immediately preceding ``r``. They are shown only so
    the model can resolve references (e.g. "don't cancel yet"); the question is
    still about the effect of ``r`` alone. Without context the text equals p1.
    """
    ctx = ""
    if context:
        ctx = ("Preceding records (context only, to resolve what the record refers to; "
               "do NOT judge them):\n" + "\n".join(_rec(c) for c in context) + "\n")
    return (
        "You audit whether a condition holds, using ONE record from an agent's interaction history.\n"
        f"Task: {task}\n"
        f"Proposed action (not executed yet): {action}\n"
        f"Condition: {claim.text}\n"
        f"{ctx}"
        f"Record{' to judge' if context else ''}: {_rec(r)}\n\n"
        "Considering only this record, what does it do to the condition?\n"
        "A. Establishes it: right after this record, the condition holds.\n"
        "B. Invalidates it: right after this record, the condition does not hold.\n"
        "C. Neither: the record is unrelated, or this record alone cannot tell.\n"
        "Answer with a single letter."
    )


def pair_judgment(task: str, action: str, claim: Claim, r1: Record, r2: Record) -> str:
    """Pairwise repair for composition-type invalidation (doc §3.4, D2)."""
    return (
        "You audit whether a condition holds, using TWO records from an agent's interaction history "
        "(listed in time order).\n"
        f"Task: {task}\n"
        f"Proposed action (not executed yet): {action}\n"
        f"Condition: {claim.text}\n"
        f"Record 1: {_rec(r1)}\n"
        f"Record 2: {_rec(r2)}\n\n"
        "Taken together, do these two records mean the condition does not hold right after Record 2?\n"
        "A. Yes, together they invalidate the condition.\n"
        "B. No.\n"
        "C. These two records cannot tell.\n"
        "Answer with a single letter."
    )


def holistic_judgment(task: str, action: str, claim: Claim, records: list[Record]) -> str:
    """One-shot judgment over a list of records (H1 / H2)."""
    hist = "\n".join(_rec(r) for r in records) if records else "(no records)"
    return (
        "You audit whether a condition holds now, before an agent executes an action.\n"
        f"Task: {task}\n"
        "History (oldest first):\n"
        f"{hist}\n\n"
        f"Proposed action (not executed yet): {action}\n"
        f"Condition: {claim.text}\n\n"
        "Based on the history, does the condition hold right now?\n"
        "A. Yes, it holds.\n"
        "B. No, it does not hold.\n"
        "C. The history is insufficient to tell.\n"
        "Answer with a single letter."
    )


def q_source(task: str, action: str, claim: Claim, r: Record) -> str:
    """Original EDA Q-source (binary), used by Q0."""
    return (
        f"Task: {task}\nCondition: {claim.text}\nRecord: {_rec(r)}\n\n"
        "Does this record show that the condition holds right after it?\n"
        "A. Yes\nB. No\nAnswer with a single letter."
    )


def q_delta(task: str, action: str, claim: Claim, r: Record) -> str:
    """Original EDA Q-delta (binary), used by Q0."""
    return (
        f"Task: {task}\nCondition: {claim.text}\nRecord: {_rec(r)}\n\n"
        "After this record, could the condition still be true?\n"
        "A. Yes\nB. No\nAnswer with a single letter."
    )


def extract_state(task: str, r: Record) -> str:
    """E1: claim-agnostic state extraction from one record."""
    return (
        "Extract every state fact that this record establishes or changes.\n"
        f"Task context: {task}\n"
        f"Record: {_rec(r)}\n\n"
        'Return a JSON list of objects {"entity": str, "attribute": str, "value": str}. '
        "Use short lowercase names. Return [] if the record states no fact. Output JSON only."
    )


def map_claim(claim: Claim, keys: list[tuple[str, str]]) -> str:
    """E1: map a claim onto one tracked (entity, attribute) key."""
    key_list = "\n".join(f"- {e} | {a}" for e, a in keys) or "(none)"
    return (
        f"Condition: {claim.text}\n"
        "Tracked state keys (entity | attribute):\n"
        f"{key_list}\n\n"
        "Which key decides this condition, and which value makes the condition true? "
        'Return JSON {"entity": str, "attribute": str, "value": str}, '
        "or null if no key matches. Output JSON only."
    )
