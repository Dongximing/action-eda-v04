"""Narrow public-state baseline for ALFWorld processing-action checkpoints."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


# Entity numbers distinguish objects of the same type in ALFWorld.
ENTITY = r"[a-z][a-z0-9_-]*(?: [a-z][a-z0-9_-]*)* [0-9]+"
PROCESS = re.compile(rf"(clean|heat|cool) ({ENTITY}) with ({ENTITY})")
ARRIVED = re.compile(rf"You arrive at (?:the )?({ENTITY})\.")
PICKED = re.compile(rf"You pick up the ({ENTITY}) from the ({ENTITY})\.")
PLACED = re.compile(rf"You (?:put|place|move) the ({ENTITY}) (?:to|in/on|in|on) the ({ENTITY})\.")
APPLIANCES = {"clean": "sinkbasin", "heat": "microwave", "cool": "fridge"}


def predict(proposal: str, history: list[dict]) -> dict:
    """Assess the two necessary conditions from public observations preceding the proposal."""
    parsed = PROCESS.fullmatch(proposal.strip().lower())
    if parsed is None:
        return {"decision": "unknown", "scope": "unsupported_action"}
    verb, item, target = parsed.groups()
    if target.rsplit(" ", 1)[0] != APPLIANCES[verb]:
        return {"decision": "unknown", "scope": "unsupported_appliance"}

    location = None
    held = None
    location_record = holding_record = None
    for record in history:
        action = record["action"].lower().strip()
        observation = record["observation"].strip()
        if action == "reset":
            location = held = location_record = holding_record = None
        if observation == "Nothing happens.":
            continue
        arrival = ARRIVED.match(observation)
        pickup = PICKED.fullmatch(observation)
        placement = PLACED.fullmatch(observation)
        if arrival:
            location, location_record = arrival[1], record["id"]
        elif action.startswith("go to "):
            # An unrecognized navigation outcome invalidates the old location.
            location = location_record = None
        if pickup and pickup[1] == item:
            held, holding_record = True, record["id"]
        elif placement and placement[1] == item:
            held, holding_record = False, record["id"]
        elif not pickup and not placement and re.match(rf"(?:take|put|drop|move|place) {re.escape(item)}(?: |$)", action):
            held = holding_record = None

    status = "unknown"
    if (location is not None and location != target) or held is False:
        status = "contradicted"
    elif location == target and held is True:
        status = "supported"
    return {"decision": status, "scope": "location_and_holding", "current_location": location,
            "required_location": target, "location_record": location_record, "held_item": item,
            "holding": held, "holding_record": holding_record}


def evaluate(prefixes: Path, outcomes: Path | None) -> dict:
    rows = [json.loads(line) for line in prefixes.read_text().splitlines() if line.strip()]
    ids = [row["id"] for row in rows]
    if not rows or len(set(ids)) != len(ids):
        raise ValueError("prefixes must have unique case IDs and at least one row")
    predictions = [{"id": row["id"], **predict(row["proposed_action"], row["prefix"]["history"])} for row in rows]
    report = {"method": "public location and holding tracker for clean / heat / cool",
              "model_requests": 0, "counts": dict(Counter(p["decision"] for p in predictions)),
              "predictions": predictions}
    if outcomes is None:
        return report
    # Label side is opened only after every prediction has been materialized.
    labels = json.loads(outcomes.read_text())
    effects = labels["outcomes"]
    by_id = {r["id"]: r["observed_effect"] for r in effects}
    if len(by_id) != len(effects) or set(ids) != set(by_id):
        raise ValueError("outcome IDs must match prefix IDs exactly once")
    expected = {"cleaned": "supported", "no_effect": "contradicted"}
    concordant = 0
    comparable = 0
    for row, prediction in zip(rows, predictions):
        effect = by_id[row["id"]]
        prediction["observed_effect"] = effect
        if row["proposed_action"].startswith("clean ") and effect in expected:
            comparable += 1
            agrees = prediction["decision"] == expected[effect]
            prediction["agrees_with_observed_effect"] = agrees
            concordant += agrees
    report["posthoc_agreement"] = {"agree": concordant, "comparable": comparable,
                                   "interpretation": "Only describes scripted clean-action outcomes in this probe."}
    report["data_source"] = labels.get("source")
    report["game_sha256"] = labels.get("game_sha256")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefixes", required=True, type=Path)
    parser.add_argument("--outcomes", type=Path, help="Optional scripted-probe observations for post-hoc agreement")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = evaluate(args.prefixes, args.outcomes)
    with args.output.open("x", encoding="utf-8") as stream:
        print(json.dumps(result, indent=2), file=stream)
    print(json.dumps({k: v for k, v in result.items() if k != "predictions"}))
