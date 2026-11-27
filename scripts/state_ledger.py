"""The agent's state kept by a decision model (OneJev / Jev), one record at a time: where the agent is, what it
carries, and which places it has looked inside. Shared by run_online.py (arm statejev) and jev_state_offline.py.

For each new record (command + feedback) one System One request asks five questions about that record alone:
  arrived   which of the places named in r0 did the command bring the agent to (or none)
  shown     which place's contents does the feedback show (or none)
  contents  yes/no: the feedback describes the contents of a place
  kind      the feedback lists contents / only says where the agent is / something else
  carry     what the command did to what the agent carries: picked up <one of the objects named in the record>,
            put it down, or nothing
A record counts as feedback about a place when kind is not "other", or when the carried object did not change and
contents is yes (kind alone calls some arrivals with contents, e.g. at a sinkbasin, "other"; picking up or putting
down changes what is carried). The answers are folded in order by code that knows no ALFWorld rules:
  location  the last place arrived at, from records about a place
  carrying  the last object picked up, cleared when the agent put down what it carried
  searched  places whose contents were shown: shown is a place, contents is yes, the record is about a place and
            the carried object did not change
Offline on the 12 d1 games (jev_state_offline.py) all three are right at 95.1% of the logged steps; the errors left
are the feedback of "look" ("You are facing X. Next to it ..."), counted as looking at X.
Every question names only things in the record or the places of r0; nothing about objects or tasks is written in.
"""
from __future__ import annotations

import re

ARRIVED_Q = ("The record is a command and the environment's feedback. Which of these places did the agent arrive at "
             "with this command? Choose none if it did not arrive at any of them.")
SHOWN_Q = ("The record is a command and the environment's feedback. Which of these places does the feedback show the "
           "contents of (what is in it or on it)? Choose none if it shows no place's contents.")
CONTENTS_Q = "This feedback describes the contents of a place."
KIND_Q = "What does the feedback of this record tell the agent?"
KIND_OPTS = {"contents": "it lists what is in or on a place, or says the place holds nothing",
             "arrived": "it says the agent is at a place but not what is in or on it",
             "other": "something else: the result of an action, an error, or what is around the agent"}
CARRY_Q = "What did this command do to what the agent carries?"
_ENTITY = re.compile(r"\b([a-z]+ \d+)\b")


def carry_options(record: dict) -> dict:
    ents = list(dict.fromkeys(_ENTITY.findall((record["action"] + " " + record["observation"]).lower())))
    opts = {f"picked up {e}": f"the agent picked up {e} and now carries it" for e in ents}
    opts["put down"] = "the agent moved, put or placed the object it was carrying somewhere, and no longer carries it"
    opts["nothing"] = "nothing changed in what the agent carries"
    return opts


def questions(record: dict, places: list[str]) -> dict:
    crit = {p: p for p in places}
    crit["none"] = "none of these places"
    return {"arrived": {"type": "choice", "instructions": ARRIVED_Q, "criteria": crit},
            "shown": {"type": "choice", "instructions": SHOWN_Q, "criteria": dict(crit)},
            "contents": {"type": "noul", "instructions": CONTENTS_Q},
            "kind": {"type": "choice", "instructions": KIND_Q, "criteria": KIND_OPTS},
            "carry": {"type": "choice", "instructions": CARRY_Q, "criteria": carry_options(record)}}


def _choice(answer: dict, labels: list[str]) -> str:
    p = answer.get("probabilities") if isinstance(answer, dict) else None
    if isinstance(p, dict) and p and set(p) <= set(labels):
        return max(p, key=lambda k: float(p[k]))
    if isinstance(p, list) and len(p) == len(labels):
        return labels[max(range(len(p)), key=lambda i: float(p[i]))]
    c = answer.get("choice") if isinstance(answer, dict) else None
    if isinstance(c, str) and c.strip() in labels:
        return c.strip()
    raise ValueError(f"no usable choice in {str(answer)[:160]}")


def _yes(answer: dict) -> bool:
    v = answer.get("noul") if isinstance(answer, dict) else None
    if isinstance(v, dict):
        v = v.get("yes", v.get("probability"))
    if not isinstance(v, (int, float)):
        raise ValueError(f"no yes-probability in {str(answer)[:160]}")
    return float(v) >= 0.5


def read(response: dict, record: dict, places: list[str]) -> dict:
    """One record's answers -> event {arrived, searched, carry, unusable}; an unusable answer counts as none/no."""
    ans = response.get("answers", {}) if isinstance(response, dict) else {}
    ev, bad = {"arrived": None, "searched": None, "carry": None}, []
    labels = places + ["none"]
    try:
        opts = carry_options(record)
        c = _choice(ans["carry"], list(opts))
        ev["carry"] = None if c == "nothing" else ("put",) if c == "put down" else ("pick", c[len("picked up "):])
    except (KeyError, ValueError):
        bad.append("carry")
    try:
        contents = _yes(ans["contents"])
        kind = _choice(ans["kind"], list(KIND_OPTS))
        about_place = kind != "other" or (ev["carry"] is None and contents)
    except (KeyError, ValueError):
        contents, about_place = False, False
        bad.append("kind")
    try:
        a = _choice(ans["arrived"], labels)
        ev["arrived"] = a if a != "none" and about_place else None
    except (KeyError, ValueError):
        bad.append("arrived")
    try:
        shown = _choice(ans["shown"], labels)
        if shown != "none" and contents and about_place and ev["carry"] is None:
            ev["searched"] = shown
    except (KeyError, ValueError):
        bad.append("searched")
    ev["unusable"] = bad
    return ev


def fold(events: list[dict]) -> dict:
    """Events of records 1..k in order -> the state after record k."""
    loc, carrying, searched, arrived = None, None, [], []
    for ev in events:
        if ev["arrived"]:
            loc = ev["arrived"]
            if loc not in arrived:
                arrived.append(loc)
        if ev["searched"] and ev["searched"] not in searched:
            searched.append(ev["searched"])
        if ev["carry"]:
            carrying = ev["carry"][1] if ev["carry"][0] == "pick" else None
    return {"location": loc, "carrying": carrying, "searched": searched, "arrived": arrived}


def note(state: dict, places: list[str]) -> str:
    left = [p for p in places if p not in state["searched"]]
    unopened = [p for p in state["arrived"] if p not in state["searched"]]
    return (f" [You are at: {state['location'] or 'the starting position'}. You carry: {state['carrying'] or 'nothing'}. "
            f"Not looked inside or on yet ({len(left)} of {len(places)} places listed at the start): "
            f"{', '.join(left) if left else 'none'}. Reached but not looked inside or on: "
            f"{', '.join(unopened) if unopened else 'none'}.]")


# ------------------------------------------------------------------ answer key from the feedback text (scoring only)

def code_event(record: dict) -> dict:
    o = record["observation"].strip().lower()
    ev = {"arrived": None, "searched": None, "carry": None}
    m = re.match(r"you arrive at ([a-z]+ \d+)", o)
    if m:
        ev["arrived"] = m.group(1)
    for p in (r"^you arrive at ([a-z]+ \d+)\. on the \1, you see", r"^you arrive at ([a-z]+ \d+)\. the \1 is open\. in it, you see",
              r"^you open the ([a-z]+ \d+)\. the \1 is open\. in it, you see", r"^on the ([a-z]+ \d+), you see"):
        m = re.match(p, o)
        if m:
            ev["searched"] = m.group(1)
            break
    m = re.match(r"you pick up the ([a-z]+ \d+) from", o)
    if m:
        ev["carry"] = ("pick", m.group(1))
    elif re.match(r"you (move|put) the ", o):
        ev["carry"] = ("put",)
    return ev
