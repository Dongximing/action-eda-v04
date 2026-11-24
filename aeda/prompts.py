"""Prompt templates. Bump PROMPT_VERSION whenever any template changes."""
from __future__ import annotations

from .schema import Claim, Record

PROMPT_VERSION = "v0.4-p4"  # p2: optional preceding-context block (k=0 identical to p1); p3: E1 maps by choice; p4: E1 extraction covers requests

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


def extract_state(task: str, r: Record, context: list[Record] | None = None) -> str:
    """E1: claim-agnostic state extraction from one record (p4: covers user requests and
    instructions, optional preceding context like the per-record judgment)."""
    ctx = ""
    if context:
        ctx = ("Preceding records (context only, to resolve references; do NOT extract from them):\n"
               + "\n".join(_rec(c) for c in context) + "\n")
    return (
        "Extract every fact that this record establishes or changes about the current state of the world, "
        "including object locations and statuses, and the user's current requests, instructions or "
        "permissions (use entity \"user\" for those).\n"
        f"Task context: {task}\n"
        f"{ctx}"
        f"Record: {_rec(r)}\n\n"
        'Return a JSON list of objects {"entity": str, "attribute": str, "value": str}. '
        'Example: "please cancel order X1" -> [{"entity": "user", "attribute": "request on x1", '
        '"value": "cancel"}]; "file f.txt moved to /a" -> [{"entity": "f.txt", "attribute": "location", '
        '"value": "/a"}]. Use short lowercase names and reuse the same entity/attribute names for the same '
        "thing. Return [] only if the record changes nothing. Output JSON only."
    )


KEY_LETTERS = [chr(ord("A") + i) for i in range(25)]  # A..Y; Z = none


def map_claim_choice(claim: Claim, keys: list[tuple[str, str]]) -> tuple[str, list[str]]:
    """E1 (p3): pick which tracked key decides the claim, as a single-letter choice.
    Returns (prompt, letters); the last letter means 'none of these'."""
    letters = KEY_LETTERS[: len(keys)] + ["Z"]
    opts = "\n".join(f"{l}. {e} | {a}" for l, (e, a) in zip(letters, keys))
    prompt = (
        f"Condition: {claim.text}\n"
        "Which tracked state key (entity | attribute) decides whether this condition holds?\n"
        f"{opts}\n"
        "Z. None of these keys is relevant.\n"
        "Answer with a single letter."
    )
    return prompt, letters


def value_check(claim: Claim, entity: str, attribute: str, value: str, rid: int) -> str:
    """E1 (p3): does the tracked latest value make the claim true?"""
    return (
        f"Condition: {claim.text}\n"
        f"Latest tracked state: {entity} | {attribute} = {value} (from record #{rid})\n\n"
        "Given this state, does the condition hold?\n"
        "A. Yes.\nB. No.\nC. Cannot tell from this state.\n"
        "Answer with a single letter."
    )
