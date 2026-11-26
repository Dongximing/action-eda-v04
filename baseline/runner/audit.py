"""Two-stage action audit of public ALFWorld TextWorld prefixes."""

from __future__ import annotations

import re
import time
from collections.abc import Callable

Choice = Callable[[dict, str, dict[str, str]], str]

# ALFWorld releases embed their action grammar in game.tw-pddl.
ACTION_GUIDE = (
    "ALFWorld TextWorld commands for this release: go to <receptacle>; take <item> from <receptacle>; "
    "move <item> to <receptacle>; open <receptacle>; close <receptacle>; "
    "clean <item> with <sinkbasin>; heat <item> with <microwave>; cool <item> with <fridge>; "
    "use <object>; slice <object> with <knife>; look; inventory; examine <entity>; help. "
    "Use exact observed entity names with their instance numbers. 'move ITEM to DEST' places the held item. "
    "'go to DEST' moves the agent. Each record pairs a past attempted command with environment feedback; "
    "the attempt alone does not establish success. A room listing only names visible fixtures. "
    "A successful go-to changes the agent's current location. To take an item the agent must "
    "be at its source and the item must be there. Successful take changes possession; successful placement ends it. "
    "Putting, cleaning, heating and cooling require holding the named item and being at the destination "
    "or appliance. Open/close requires being at the receptacle and its opposite initial open/closed state. "
    "Use requires reaching the object. Source and target IDs must match exactly. A task goal states what "
    "to achieve, not the current world state or a prerequisite of every intermediate action."
)
CHECK_VERBS = frozenset(("take", "put", "move", "clean", "heat", "cool", "open", "close", "use", "slice"))
YES_NO = {"yes": "Yes.", "no": "No.", "unknown": "This record is inconclusive."}
STATES = {
    "SUPPORTED": "Visible evidence establishes the condition and no later update undoes it.",
    "CONTRADICTED": "Visible evidence establishes the opposite, without a subsequent restoration.",
    "UNKNOWN": "Visible evidence is insufficient, ambiguous, or incomplete.",
}
SOURCE = (
    "Does this individual record affirmatively establish that the claim holds immediately after this step? "
    "Only answer yes with explicit evidence or a necessary consequence of observed success. "
    "Answer no for clear counterevidence and unknown for silence. Do not infer success from an attempted command."
)
DELTA = (
    "After this record, can the claim still be true? Answer no only if the environment feedback "
    "rules it out, including a successful change to a mutually exclusive state. Answer yes if it supports "
    "the claim or clearly leaves its truth possible, including a wholly unrelated update. Answer unknown "
    "if a potentially relevant effect is unresolved. An unsuccessful command alone does not change state."
)
HISTORY = (
    "Judge this action precondition at the end of these chronological records. Use observed evidence, "
    "track invalidation and re-establishment, and return UNKNOWN if missing or unresolved. "
    "An isolated attempt or task goal is not proof of success."
)


def checkpoint_action(action: str) -> bool:
    return (action.lower().split() or [""])[0] in CHECK_VERBS


def fixed_claims(action: str) -> list[dict]:
    """Small mandatory subset of public action preconditions, not an applicability oracle."""
    command = " ".join(action.lower().split())
    entity = r"([a-z][a-z0-9 _-]*? [0-9]+)"
    checks = []

    def add(predicate, claim, *anchors):
        checks.append({"id": predicate, "claim": claim, "anchors": list(anchors), "predicate": predicate})

    pair = re.fullmatch(r"(take|put|move|clean|heat|cool|slice) " + entity
                        + r" (from|in/on|into|in|on|to|with) " + entity, command)
    if pair:
        verb, item, link, target = pair.groups()
        grammar = {"take": ("from",), "put": ("in/on", "in", "on", "into"), "move": ("to",), "clean": ("with",),
                   "heat": ("with",), "cool": ("with",), "slice": ("with",)}
        if link not in grammar[verb]:
            return []
        if verb == "slice":
            add("holding", f"The agent is currently holding {target}.", target)
            add("reachable", f"The agent is currently at the location of {item}.", item)
        else:
            add("location", f"The agent is currently at {target}.", target)
            if verb == "take":
                add("contained", f"{item} is currently in or on {target}.", item, target)
            else:
                add("holding", f"The agent is currently holding {item}.", item)
        return checks
    single = re.fullmatch(r"(open|close|use) " + entity, command)
    if single:
        verb, target = single.groups()
        if verb == "use":
            add("reachable", f"The agent is currently at the location of {target}.", target)
        else:
            add("location", f"The agent is currently at {target}.", target)
            state = "closed" if verb == "open" else "open"
            add("openness", f"{target} is currently {state}.", target)
    return checks


def records(checkpoint: dict) -> list[dict]:
    """Whitelist fields so evaluator labels and post-action feedback are never serialized."""
    rows = []
    seen_ids = set()
    for row in checkpoint["history"]:
        key = str(row["id"])
        if not key or key in seen_ids:
            raise ValueError("History needs distinct record IDs in chronological order")
        rows.append({"id": key, "action": row["action"], "observation": row["observation"]})
        seen_ids.add(key)
    current = checkpoint.get("observation", "")
    if current and (not rows or current != rows[-1]["observation"]):
        key = "current"
        while key in seen_ids:
            key += "_"
        rows.append({"id": key, "action": "", "observation": current})
    return rows


def candidates(claim: dict, rows: list[dict]) -> list[dict]:
    """Use exact anchors and change events for known predicates. Fall back to all rows for untyped claims."""
    predicate = claim.get("predicate", "dynamic")
    if predicate == "dynamic":
        text = claim["claim"].lower()
        if re.search(r"\b(holding|carrying|in hand|inventory|empty hands)\b", text):
            predicate = "holding"
        elif re.search(r"\b(the agent|player|you)\b.*\b(at|near|next to|in front of)\b", text):
            predicate = "location"
        elif re.search(r"\b(open|closed|clean|hot|cool|cold|switched on|turned on)\b", text):
            predicate = "attribute"
        else:
            return list(rows)
        # Unanchored terms such as "the tool" do not identify the entity being changed.
        if not any(re.search(r"\b\w+\s+\d+\b", term) for term in claim["anchors"]):
            return list(rows)
    anchors = [re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.I) for term in claim["anchors"]]
    selected = []
    for row in rows:
        command = row["action"].strip().lower()
        text = f"{command} {row['observation']}"
        update = False
        if predicate in ("location", "reachable"):
            # A successful action at another site can also establish location. Include
            # all such actions even when the navigation/location target changes IDs.
            update = command.startswith("go to ") or checkpoint_action(command) or command == "look"
        elif predicate == "holding":
            update = command.startswith(("take ", "put ", "move ")) or command == "inventory"
        elif predicate == "attribute":
            update = command.split(" ", 1)[0] in {"open", "close", "clean", "heat", "cool", "use"}
        if update or any(pattern.search(text) for pattern in anchors):
            selected.append(row)
    return selected


def _call(choose, state, instruction, options, calls, stage, claim_id=None, record_ids=()):
    start = time.monotonic()
    trace = {"stage": stage, "claim_id": claim_id, "record_ids": list(record_ids)}
    try:
        value = choose(state, instruction, options)
        if value not in options:
            raise ValueError("Invalid choice")
        trace["answer"] = value
        return value
    except (ValueError, RuntimeError, OSError) as error:
        # Providers handle transport retries. Keep model failure separate from semantic uncertainty.
        trace["error"] = type(error).__name__
        return None
    finally:
        trace["seconds"] = round(time.monotonic() - start, 6)
        calls.append(trace)


def prepare(checkpoint: dict, risks: list[dict], choose: Choice) -> dict:
    """Select a risk with the supplied judge and assemble the conditions for evidence checking."""
    rows = records(checkpoint)
    fixed = fixed_claims(checkpoint["action"])
    menu = {f"R{i}": risk["risk"] for i, risk in enumerate(risks, 1)}
    menu.update(none="No listed issue identified.", insufficient="Available information is insufficient.")
    state = {"task": checkpoint["task"], "action": checkpoint["action"], "history": rows, "action_guide": ACTION_GUIDE}
    calls = []
    selection = _call(choose, state, "Which possible issue with the proposed action should be checked first? "
                      "Evaluate the options against the visible prefix and public action semantics.",
                      menu, calls, "risk_menu", record_ids=[r["id"] for r in rows])
    claims = list(fixed)
    dynamic = {f"R{i}": candidate for i, candidate in enumerate(risks, 1)}
    if selection in dynamic:
        risk = dynamic[selection]
        if all(c["claim"].strip().casefold() != risk["claim"].strip().casefold() for c in claims):
            claims.append({"id": selection, "claim": risk["claim"], "anchors": risk["anchors"], "predicate": "dynamic"})
    return {"selection": selection, "menu": menu, "risks": risks, "claims": claims, "calls": calls,
            "menu_failed": selection is None, "fixed_conditions_available": bool(fixed)}


def _eda(claim: dict, rows: list[dict], choose: Choice, calls: list) -> dict:
    def judge(row, stage):
        public = {"action_semantics": ACTION_GUIDE, "claim": claim["claim"], "record": row}
        return _call(choose, public, SOURCE if stage == "source" else DELTA, YES_NO, calls,
                     stage, claim["id"], [row["id"]])

    # Search backwards. A positive source also needs a compatible delta on the same record.
    source_id = None
    status, witness = "UNKNOWN", None
    start = 0
    source_answers = {}
    deltas = {}
    for i in range(len(rows) - 1, -1, -1):
        row = rows[i]
        answer = judge(row, "source")
        source_answers[row["id"]] = answer
        if answer != "yes":
            continue
        delta = judge(row, "delta")
        deltas[row["id"]] = delta
        if delta == "yes":
            status, source_id, witness = "SUPPORTED", row["id"], row["id"]
            start = i + 1
            break

    # With no source, an explicit negative delta can still establish a contradiction.
    for row in rows[start:]:
        key = row["id"]
        delta = deltas[key] if key in deltas else judge(row, "delta")
        source = source_answers[key]
        inconsistent = (source == "yes" and delta == "no") or (source == "no" and delta == "yes")
        if source is None or delta in (None, "unknown") or inconsistent:
            status, witness = "UNKNOWN", key
        elif delta == "no":
            status, witness = "CONTRADICTED", key
        # A later "still possible" is not positive evidence that restores the claim.
    return {"status": status, "source_id": source_id, "witness_id": witness}


def audit(checkpoint: dict, prepared: dict, choose: Choice, method: str = "eda") -> dict:
    """Judge exactly the same frozen claims independently with full, retrieved, or EDA evidence."""
    if method not in {"eda", "full", "retrieved"}:
        raise ValueError(f"Unknown audit method {method}")
    rows = records(checkpoint)
    calls = []
    outcomes = []
    for claim in prepared["claims"]:
        selected = rows if method == "full" else candidates(claim, rows)
        ids = [row["id"] for row in selected]
        if method == "eda":
            result = _eda(claim, selected, choose, calls)
        else:
            state = {"task": checkpoint["task"], "action": checkpoint["action"], "claim": claim["claim"],
                     "history": selected, "action_guide": ACTION_GUIDE}
            value = _call(choose, state, HISTORY, STATES, calls, method, claim["id"], ids)
            result = {"status": value or "UNKNOWN", "source_id": None, "witness_id": None}
            if not selected:
                result["status"] = "UNKNOWN"
        outcomes.append({**claim, **result, "candidate_ids": ids})
    labels = {outcome["status"] for outcome in outcomes}
    if "CONTRADICTED" in labels:
        status = "CONTRADICTED"
    elif labels == {"SUPPORTED"} and prepared["fixed_conditions_available"] and not prepared["menu_failed"]:
        status = "SUPPORTED"
    else:
        status = "UNKNOWN"
    return {"method": method, "status": status, "claims": outcomes, "calls": calls}
