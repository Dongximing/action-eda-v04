"""Prompt templates. Bump PROMPT_VERSION whenever any template changes.

Every decision question is a structured multiple-choice item (MCQ): a context
block, a question and lettered options. Backends that read a rendered prompt
(local HF models) use ``MCQ.render()``; a decision model with its own API (Jev)
receives the three parts separately through its adapter.
"""
from __future__ import annotations

from dataclasses import dataclass

from .schema import Claim, Record

# p1 initial; p2 optional preceding context; p3 E1 maps by choice; p4 E1 extraction covers requests;
# p5 structured MCQ (context / question / options) shared by all decision backends
PROMPT_VERSION = "v0.4-p6"

LETTERS3 = ["A", "B", "C"]
LETTERS2 = ["A", "B"]
KEY_LETTERS = [chr(ord("A") + i) for i in range(25)]  # A..Y; Z = none


@dataclass
class MCQ:
    context: str
    question: str
    options: list[tuple[str, str]]  # (letter, text)

    @property
    def letters(self) -> list[str]:
        return [l for l, _ in self.options]

    def render(self) -> str:
        opts = "\n".join(f"{l}. {t}" for l, t in self.options)
        return f"{self.context}\n\n{self.question}\n{opts}\nAnswer with a single letter."


def _rec(r: Record) -> str:
    return f"[#{r.rid} | {r.source}] {r.text}"


def _ctx_block(context: list[Record] | None, verb: str) -> str:
    if not context:
        return ""
    return (f"Preceding records (context only, to resolve what the record refers to; do NOT {verb} them):\n"
            + "\n".join(_rec(c) for c in context) + "\n")


def _examples_block(examples: list[dict] | None, scope: str = "record") -> str:
    if not examples:
        return ""
    what = "one record" if scope == "record" else "a history"
    out = [f"Worked examples (from other episodes; each judges {what} against one condition):"]
    for i, e in enumerate(examples, 1):
        out.append(f"Example {i}\nCondition: {e['condition']}\n{_rec_label(scope)}: {e['record']}\n"
                   f"Answer: {e['answer']}")
    return "\n\n".join(out) + "\n\nNow the real case.\n"


def record_judgment(task: str, action: str, claim: Claim, r: Record,
                    context: list[Record] | None = None, examples: list[dict] | None = None) -> MCQ:
    """Three-option per-record judgment used by D1 / D1f / D2 / U1 / P0 (doc §3.4).

    ``context`` = records immediately preceding ``r``, shown only to resolve
    references (e.g. "don't cancel yet"); the question is about ``r`` alone.
    ``examples`` = optional few-shot items {condition, record, answer} shown first.
    """
    return MCQ(
        context=(
            "You audit whether a condition holds, using ONE record from an agent's interaction history.\n"
            f"{_examples_block(examples)}"
            f"Task: {task}\n"
            f"Proposed action (not executed yet): {action}\n"
            f"Condition: {claim.text}\n"
            f"{_ctx_block(context, 'judge')}"
            f"Record{' to judge' if context else ''}: {_rec(r)}"
        ),
        question="Considering only this record, what does it do to the condition?",
        options=[("A", "Establishes it: right after this record, the condition holds."),
                 ("B", "Invalidates it: right after this record, the condition does not hold."),
                 ("C", "Neither: the record is unrelated, or this record alone cannot tell.")],
    )


def state_options(text: str, spec: dict | None, scope: str = "record") -> tuple[str, list[tuple[str, str]]]:
    """State question for one condition: A = condition holds, B = it does not,
    C = not shown (same meaning as record_judgment / holistic_judgment).
    scope "record": right after one record; "history": now, after the whole history."""
    when = "Right after this record" if scope == "record" else "Right now (after the last record)"
    src = "This record does" if scope == "record" else "The history does"
    t = (spec or {}).get("type")
    if t == "at":
        loc = spec["loc"]
        return (f"{when}, where is the agent?",
                [("A", f"At {loc}."), ("B", f"Somewhere other than {loc}."),
                 ("C", f"{src} not show where the agent is.")])
    if t == "holding":
        obj = spec["obj"]
        return (f"{when}, what is the agent holding?",
                [("A", f"{obj}."), ("B", f"Something other than {obj}, or nothing."),
                 ("C", f"{src} not show what the agent is holding.")])
    if t == "hand_empty":
        return (f"{when}, what is the agent holding?",
                [("A", "Nothing."), ("B", "Some object."),
                 ("C", f"{src} not show what the agent is holding.")])
    return (f"{when}, is this true: {text}?",
            [("A", "Yes."), ("B", "No."), ("C", f"{src} not show it.")])


def _rec_label(scope: str) -> str:
    return "Record" if scope == "record" else "History (oldest first)"


def _state_examples_block(examples: list[dict] | None, scope: str = "record") -> str:
    if not examples:
        return ""
    out = ["Worked examples (from other episodes):"]
    for i, e in enumerate(examples, 1):
        q, opts = state_options(e["condition"], e.get("spec"), scope)
        out.append(f"Example {i}\n{_rec_label(scope)}: {e['record']}\n{q}\n" +
                   "\n".join(f"{l}. {t}" for l, t in opts) + f"\nAnswer: {e['answer']}")
    return "\n\n".join(out) + "\n\nNow the real case.\n"


def record_state(task: str, action: str, claim: Claim, r: Record,
                 context: list[Record] | None = None, examples: list[dict] | None = None) -> MCQ:
    """Per-record judgment asked as a state question (``--record-style state``).
    Same A/B/C meaning as record_judgment, so D1/D1f/D2/U1/P0 use it unchanged."""
    q, opts = state_options(claim.text, claim.spec)
    return MCQ(
        context=(
            "You track the state of an agent from ONE record of its interaction history.\n"
            f"{_state_examples_block(examples)}"
            f"Task: {task}\n"
            f"Proposed action (not executed yet): {action}\n"
            f"{_ctx_block(context, 'judge')}"
            f"Record{' to judge' if context else ''}: {_rec(r)}"
        ),
        question=q,
        options=opts,
    )


def pair_judgment(task: str, action: str, claim: Claim, r1: Record, r2: Record) -> MCQ:
    """Pairwise repair for composition-type invalidation (doc §3.4, D2)."""
    return MCQ(
        context=(
            "You audit whether a condition holds, using TWO records from an agent's interaction history "
            "(listed in time order).\n"
            f"Task: {task}\n"
            f"Proposed action (not executed yet): {action}\n"
            f"Condition: {claim.text}\n"
            f"Record 1: {_rec(r1)}\n"
            f"Record 2: {_rec(r2)}"
        ),
        question="Taken together, do these two records mean the condition does not hold right after Record 2?",
        options=[("A", "Yes, together they invalidate the condition."),
                 ("B", "No."),
                 ("C", "These two records cannot tell.")],
    )


def holistic_judgment(task: str, action: str, claim: Claim, records: list[Record],
                      examples: list[dict] | None = None, style: str = "effect") -> MCQ:
    """One judgment over a list of records (H1 / H2). ``style`` and ``examples``
    mirror the per-record judgment so H1/H2 and D1 see the same question form and
    the same worked examples (a one-record example is shown as a one-record history)."""
    hist = "\n".join(_rec(r) for r in records) if records else "(no records)"
    if style == "state":
        q, opts = state_options(claim.text, claim.spec, "history")
        return MCQ(
            context=(
                "You track the current state of an agent from its interaction history.\n"
                f"{_state_examples_block(examples, 'history')}"
                f"Task: {task}\n"
                "History (oldest first):\n"
                f"{hist}\n\n"
                f"Proposed action (not executed yet): {action}"
            ),
            question=q,
            options=opts,
        )
    return MCQ(
        context=(
            "You audit whether a condition holds now, before an agent executes an action.\n"
            f"{_examples_block(examples, 'history')}"
            f"Task: {task}\n"
            "History (oldest first):\n"
            f"{hist}\n\n"
            f"Proposed action (not executed yet): {action}\n"
            f"Condition: {claim.text}"
        ),
        question="Based on the history, does the condition hold right now?",
        options=[("A", "Yes, it holds."),
                 ("B", "No, it does not hold."),
                 ("C", "The history is insufficient to tell.")],
    )


def q_source(task: str, action: str, claim: Claim, r: Record) -> MCQ:
    """Original EDA Q-source (binary), used by Q0."""
    return MCQ(context=f"Task: {task}\nCondition: {claim.text}\nRecord: {_rec(r)}",
               question="Does this record show that the condition holds right after it?",
               options=[("A", "Yes"), ("B", "No")])


def q_delta(task: str, action: str, claim: Claim, r: Record) -> MCQ:
    """Original EDA Q-delta (binary), used by Q0."""
    return MCQ(context=f"Task: {task}\nCondition: {claim.text}\nRecord: {_rec(r)}",
               question="After this record, could the condition still be true?",
               options=[("A", "Yes"), ("B", "No")])


def map_claim_choice(claim: Claim, keys: list[tuple[str, str]]) -> MCQ:
    """E1: pick which tracked key decides the claim; the last option means 'none'."""
    opts = [(l, f"{e} | {a}") for l, (e, a) in zip(KEY_LETTERS, keys)]
    opts.append(("Z", "None of these keys is relevant."))
    return MCQ(context=f"Condition: {claim.text}",
               question="Which tracked state key (entity | attribute) decides whether this condition holds?",
               options=opts)


def value_check(claim: Claim, entity: str, attribute: str, value: str, rid: int) -> MCQ:
    """E1: does the tracked latest value make the claim true?"""
    return MCQ(context=(f"Condition: {claim.text}\n"
                        f"Latest tracked state: {entity} | {attribute} = {value} (from record #{rid})"),
               question="Given this state, does the condition hold?",
               options=[("A", "Yes."), ("B", "No."), ("C", "Cannot tell from this state.")])


# ---------------------------------------------------------------- generation (not decision) prompts

def extract_state(task: str, r: Record, context: list[Record] | None = None) -> str:
    """E1: claim-agnostic state extraction from one record (needs a generative model)."""
    return (
        "Extract every fact that this record establishes or changes about the current state of the world, "
        "including object locations and statuses, and the user's current requests, instructions or "
        "permissions (use entity \"user\" for those).\n"
        f"Task context: {task}\n"
        f"{_ctx_block(context, 'extract from')}"
        f"Record: {_rec(r)}\n\n"
        'Return a JSON list of objects {"entity": str, "attribute": str, "value": str}. '
        'Example: "please cancel order X1" -> [{"entity": "user", "attribute": "request on x1", '
        '"value": "cancel"}]; "file f.txt moved to /a" -> [{"entity": "f.txt", "attribute": "location", '
        '"value": "/a"}]. Use short lowercase names and reuse the same entity/attribute names for the same '
        "thing. Return [] only if the record changes nothing. Output JSON only."
    )
