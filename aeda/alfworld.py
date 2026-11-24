"""ALFWorld helpers: parse text actions, replay a trajectory with a deterministic
tracker (T0), and derive fixed preconditions for state-changing actions.

ALFWorld is the negative control in doc v0.4 §5.3: location and held object are
fully determined by the agent's own logged actions, so T0 should be near ceiling.

Input trajectory format (one episode per JSONL line):
  {"episode_id": "...", "task": "put a clean knife in countertop",
   "init_obs": "You are in the middle of a room. ...",
   "steps": [{"action": "go to countertop 2", "observation": "You arrive at ..."}, ...]}
"""
from __future__ import annotations

import re
from dataclasses import dataclass

NOTHING = "nothing happens"

_PATTERNS = [
    ("goto", re.compile(r"^go to (.+)$")),
    ("take", re.compile(r"^take (.+?) from (.+)$")),
    ("put", re.compile(r"^(?:put|move) (.+?) (?:in/on|in|on|to) (.+)$")),
    ("open", re.compile(r"^open (.+)$")),
    ("close", re.compile(r"^close (.+)$")),
    ("clean", re.compile(r"^clean (.+?) with (.+)$")),
    ("heat", re.compile(r"^heat (.+?) with (.+)$")),
    ("cool", re.compile(r"^cool (.+?) with (.+)$")),
]

STATE_CHANGING = {"take", "put", "open", "close", "clean", "heat", "cool"}


def parse_action(action: str) -> tuple[str, tuple[str, ...]]:
    a = action.strip().lower()
    for name, pat in _PATTERNS:
        mt = pat.match(a)
        if mt:
            return name, tuple(g.strip() for g in mt.groups())
    return "other", (a,)


def succeeded(observation: str) -> bool:
    return not observation.strip().lower().startswith(NOTHING)


@dataclass
class TrackerState:
    loc: str | None = None
    holding: str | None = None


def replay(steps: list[tuple[str, str]]) -> TrackerState:
    """Apply (action, observation) pairs; failed actions ("Nothing happens") change nothing."""
    st = TrackerState()
    for action, obs in steps:
        if not succeeded(obs):
            continue
        name, args = parse_action(action)
        if name == "goto":
            st.loc = args[0]
        elif name == "take":
            st.holding = args[0]
        elif name == "put":
            st.holding = None
    return st


def preconditions(action: str) -> list[dict]:
    """Fixed preconditions from the public action semantics. Each item has a
    natural-language text and a machine spec that T0 can evaluate."""
    name, args = parse_action(action)
    out = []

    def at(loc):
        out.append({"text": f"The agent is currently at {loc}", "spec": {"type": "at", "loc": loc}, "entities": [loc]})

    def holds(obj):
        out.append({"text": f"The agent is currently holding {obj}", "spec": {"type": "holding", "obj": obj}, "entities": [obj]})

    if name == "take":
        at(args[1])
        out.append({"text": "The agent is currently holding nothing", "spec": {"type": "hand_empty"}, "entities": []})
    elif name == "put":
        holds(args[0])
        at(args[1])
    elif name in ("open", "close"):
        at(args[0])
    elif name in ("clean", "heat", "cool"):
        holds(args[0])
        at(args[1])
    return out


def evaluate_spec(spec: dict, st: TrackerState) -> str:
    t = spec.get("type")
    if t == "at":
        # loc None = still at the starting point, i.e. not at any receptacle
        return "SUPPORTED" if st.loc == spec["loc"] else "CONTRADICTED"
    if t == "holding":
        return "SUPPORTED" if st.holding == spec["obj"] else "CONTRADICTED"
    if t == "hand_empty":
        return "SUPPORTED" if st.holding is None else "CONTRADICTED"
    return "UNKNOWN"


ACTION_PREFIX = "> "


def record_text(action: str, observation: str) -> str:
    return f"{ACTION_PREFIX}{action}\n{observation}"


def steps_from_records(texts: list[str]) -> list[tuple[str, str]]:
    """Inverse of record_text for records produced by the converter."""
    steps = []
    for t in texts:
        if t.startswith(ACTION_PREFIX):
            head, _, obs = t[len(ACTION_PREFIX):].partition("\n")
            steps.append((head, obs))
    return steps
