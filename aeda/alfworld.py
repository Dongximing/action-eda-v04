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


def build_sample(episode_id: str, task: str, init_obs: str, steps: list[tuple[str, str]], t: int,
                 action: str) -> dict | None:
    """Visible sample for proposed ``action`` at step ``t``: records are the reset observation and
    steps[:t]; claims are the fixed preconditions of ``action``. Used by the offline converter and
    the online runner alike, so both build identical inputs. None if the action has no preconditions."""
    import re
    pres = preconditions(action)
    if not pres:
        return None
    records = [{"rid": 0, "source": "env", "text": init_obs, "entities": []}]
    records += [{"rid": i + 1, "source": "env", "text": record_text(a, o), "entities": []}
                for i, (a, o) in enumerate(steps[:t])]
    sid = f"{episode_id}-t{t}"
    claims = []
    for j, pre in enumerate(pres):
        for r in records:
            # whole-name match, so "countertop 1" does not match "countertop 10"
            if any(e and re.search(rf"(?<![A-Za-z0-9_]){re.escape(e)}(?![A-Za-z0-9_])", r["text"].lower())
                   for e in pre["entities"]):
                r["entities"] = sorted(set(r["entities"]) | set(pre["entities"]))
        # agents start empty-handed (public game rule): "holding nothing" is a default claim
        kind = "default" if pre["spec"]["type"] == "hand_empty" else "state"
        claims.append({"cid": f"{sid}/c{j}", "text": pre["text"], "kind": kind, "origin": "fixed",
                       "entities": pre["entities"], "spec": pre["spec"]})
    return {"sid": sid, "episode_id": episode_id, "task": task, "proposed_action": action,
            "action_reversible": True, "window_complete": True, "records": records, "claims": claims}
