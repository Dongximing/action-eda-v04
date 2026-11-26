"""Condition writers for model-written preconditions (the mw arm).

A writer gets the public checkpoint (task, visible history, the proposed command and the
public action guide, exactly what the agent itself sees) and returns free-text conditions
[{"claim": str, "anchors": [entity ids]}] that D1 then verifies against the history.

  risks  the baseline project's own models.GPUChat.risks() (first mw pilot)
  v2     a precondition-only instruction with no task-specific content: conditions that must already
         hold right before the command; no effects, no goal, no later steps; most-likely-false first
  v2demo v2 plus the same one-shot demonstration the agent itself gets for this task family
         (the baseline's one_shot_examples.json, identical text and wording). No condition lists
         or other content are added: every input comes from what the baseline already has.

The writer is the agent model (qwen/qwen3.5-9b), called through its own client so the call
is cached and metered like every actor call.
"""
from __future__ import annotations

import re

WRITERS = ("risks", "v2", "v2demo")

V2 = (
    "You check a proposed ALFWorld command before it is executed. Write the conditions that must "
    "ALREADY be true right now, just before the command, for the command to succeed. Each condition is "
    "one short present-tense sentence about the current state. Use the exact entity IDs. "
    "Do not write what the command will cause (its effects), the task goal, or anything about later steps. "
    "Follow the public action guide for what each command needs; do not add requirements it does not state. "
    "Write at most {k} conditions, starting with the one most likely to be false now. "
    'Return only {{"conditions": ["...", "..."]}} as valid JSON.'
)

# Same wording as models.GPUChat.action() uses to show the agent its one-shot demonstration.
DEMO = ("\n\nWorked example from a different game in this task family. "
        "Use it as an example of the procedure. The next user message contains the current "
        "task, entities and observations.\n<example>\n{text}\n</example>")


def instruction(variant: str, k: int, demo: str | None = None) -> str:
    if variant not in ("v2", "v2demo"):
        raise ValueError(f"no instruction for writer {variant!r}")
    text = V2.format(k=k)
    if variant == "v2demo":
        if not demo:
            raise ValueError("writer v2demo needs the agent's one-shot demonstration")
        text += DEMO.format(text=demo)
    return text


ENTITY = re.compile(r"\b([a-z]+ [0-9]+)\b")


def anchors(text: str) -> list[str]:
    return list(dict.fromkeys(ENTITY.findall(text.lower())))


def parse(result: object, k: int) -> list[dict]:
    """{"conditions": [str, ...]} -> [{"claim", "anchors"}], deduplicated, at most k."""
    if not isinstance(result, dict) or not isinstance(result.get("conditions"), list):
        raise ValueError("condition writer must return {\"conditions\": [...]}")
    out, seen = [], set()
    for c in result["conditions"]:
        if not isinstance(c, str) or not c.strip():
            continue
        c = " ".join(c.split())
        if c.casefold() in seen:
            continue
        seen.add(c.casefold())
        out.append({"claim": c, "anchors": anchors(c)})
        if len(out) == k:
            break
    return out


def write(actor, checkpoint: dict, variant: str, k: int, public_checkpoint=None) -> list[dict]:
    """Call the writer through the actor client. ``public_checkpoint`` is models.public_checkpoint
    (the same visible state the agent gets); ``risks`` delegates to the baseline's own method."""
    if variant == "risks":
        return actor.risks(checkpoint, k=k)
    state = public_checkpoint(checkpoint) if public_checkpoint else dict(checkpoint)
    demo = (getattr(actor, "action_example", None) or {}).get("text") if variant == "v2demo" else None
    result = actor._respond(state, instruction(variant, k, demo), max_tokens=60 + 60 * k)
    return parse(result, k)
