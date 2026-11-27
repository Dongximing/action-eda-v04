#!/usr/bin/env python3
"""Demonstrations for arm think_copy: the thought demonstrations (data/fewshot/react_think_examples.json, ReAct's
react_<family>_0 games) with the state note added the way the agent sees it at run time, and each step's
{"state", "thought", "action"} whose state is the note copied. No state is written by hand: the notes come from
the decision model through scripts/state_ledger.py (the same questions and fold as the online arms), asked over a
System One endpoint (scripts/onejev_mac_server.py). ReAct's demonstrations use the older ALFWorld feedback ("The
fridge 1 is closed." without "You arrive at"), which state_ledger.code_event does not read, so the notes are not
scored against it here; they were checked by reading (all 25 steps right: location, carried object, places looked
inside, places reached but not looked inside).

  python3 scripts/make_copy_examples.py [--url http://127.0.0.1:8000/v1/systemone]
writes data/fewshot/react_think_copy_examples.json (answers cached in runs/jev_state/demo_cache.jsonl).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state_ledger as L  # noqa: E402
from jev_places_offline import ROOT, Client, code_places  # noqa: E402


def parse(text: str) -> tuple[str, str, list[dict]]:
    lines = text.split("\n")
    task, first = lines[0], lines[1][len("Initial observation: "):]
    steps = []
    for i in range(2, len(lines), 2):
        act = json.loads(lines[i][len("Action: "):])
        steps.append({"thought": act["thought"], "action": act["action"], "observation": lines[i + 1][len("Observation: "):]})
    return task, first, steps


def copy_of(note: str) -> str:
    return note.strip()[1:-1]   # the note without its brackets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=os.getenv("JEV_URL", "http://127.0.0.1:8000/v1/systemone"))
    ap.add_argument("--out", default=str(ROOT / "data/fewshot/react_think_copy_examples.json"))
    a = ap.parse_args()
    src = json.loads((ROOT / "data/fewshot/react_think_examples.json").read_text())
    client = Client(a.url, None, ROOT / "runs/jev_state/demo_cache.jsonl")
    out = {}
    for fam, ex in src["examples"].items():
        task, first, steps = parse(ex["text"])
        places, _ = code_places([{"observation": first}])
        events = []
        lines = [task, f"Initial observation: {first}{L.note(L.fold([]), places)}"]
        for k, st in enumerate(steps):
            note_before = L.note(L.fold(events), places)
            lines.append("Action: " + json.dumps({"state": copy_of(note_before), "thought": st["thought"], "action": st["action"]},
                                                  ensure_ascii=False, separators=(",", ":")))
            rec = {"action": st["action"], "observation": st["observation"]}
            events.append(L.read(client.ask({"record": rec}, L.questions(rec, places)), rec, places))
            lines.append(f"Observation: {st['observation']}{L.note(L.fold(events), places)}")
        out[fam] = {"id": ex["id"] + "+state", "text": "\n".join(lines), "steps": len(steps)}
        print(fam, len(steps), "steps")
    doc = {"source": "data/fewshot/react_think_examples.json (" + src["source"] + ")", "license": src["license"],
           "rule": "Each observation is followed by the state note the agent sees at run time (state_ledger.note), and each "
                   "step's state field is that note copied (the note after the previous record). The notes were written by "
                   "the decision model through state_ledger.py, not by hand.",
           "state_model": "OneJev1.6-4B via " + a.url, "notes_checked": "by reading, all 25 steps right", "examples": out}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(a.out, "| new requests", client.new)


if __name__ == "__main__":
    main()
