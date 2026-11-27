#!/usr/bin/env python3
"""Offline check of the full state kept by the decision model (scripts/state_ledger.py). No game is played.

On the selfexplore trajectories of the 68 games (the same records as jev_places_offline.py), every record up to the
last logged step gets one System One request with the five state questions; the answers are folded into the
state (location, carrying, places looked inside) and compared at every logged step with the same fold of the
answer key read from the feedback text (state_ledger.code_event).

  python3 scripts/jev_state_offline.py [--limit-games N] [--url ...]
Answers cached in runs/jev_state/cache.jsonl; report.md and steps.jsonl beside it.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state_ledger as L  # noqa: E402
from jev_places_offline import DIRS, ROOT, Client, code_places, load_games  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=os.getenv("JEV_URL", "http://127.0.0.1:8000/v1/systemone"))
    ap.add_argument("--model", default=os.getenv("JEV_MODEL") or None)
    ap.add_argument("--limit-games", type=int, default=0)
    ap.add_argument("--out", default=str(ROOT / "runs/jev_state"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    client = Client(a.url, a.model, out / "cache.jsonl")
    games = load_games(DIRS, a.limit_games)
    rec = collections.Counter()
    rows = []
    for gi, g in enumerate(games, 1):
        hist = g["history"]
        places, _ = code_places(hist[:1])
        last = max([e["step"] for e in g["place_lists"]], default=0)
        model_ev, key_ev = [], []
        for k in range(1, last + 1):
            r = {"action": hist[k]["action"], "observation": hist[k]["observation"]}
            ev = L.read(client.ask({"record": r}, L.questions(r, places)), r, places)
            kv = L.code_event(r)
            kv = {**kv, "arrived": kv["arrived"] if kv["arrived"] in places else None,
                  "searched": kv["searched"] if kv["searched"] in places else None}
            model_ev.append(ev)
            key_ev.append(kv)
            for q in ("arrived", "searched", "carry"):
                rec[(q, "n")] += 1
                rec[(q, "right")] += ev[q] == kv[q]
            rec["unusable"] += bool(ev["unusable"])
        for e in g["place_lists"]:
            s, t = L.fold(model_ev[:e["step"]]), L.fold(key_ev[:e["step"]])
            row = {"folder": g["folder"], "id": g["id"], "step": e["step"],
                   "location": s["location"] == t["location"], "carrying": s["carrying"] == t["carrying"],
                   "not_searched": set(p for p in places if p not in s["searched"]) == set(p for p in places if p not in t["searched"]),
                   "missed": len(set(t["searched"]) - set(s["searched"])), "extra": len(set(s["searched"]) - set(t["searched"]))}
            row["all"] = row["location"] and row["carrying"] and row["not_searched"]
            rows.append(row)
        print(f"[{gi}/{len(games)}] {g['folder']}/{g['id']}: all three right on "
              f"{sum(r['all'] for r in rows if r['id'] == g['id'] and r['folder'] == g['folder'])}/{len(g['place_lists'])} steps "
              f"(new requests {client.new}, {client.seconds / max(1, client.new):.1f}s each)", flush=True)
    n = len(rows)
    pct = lambda k: f"{sum(r[k] for r in rows)}/{n} ({100 * sum(r[k] for r in rows) / max(1, n):.1f}%)"
    lines = [f"# Full state kept by the decision model, offline: {len(games)} games, {n} logged steps", "",
             f"Server {a.url}. Answer key: the same fold over the feedback text (state_ledger.code_event).", "",
             "| at every logged step | right |", "|---|---|",
             f"| location | {pct('location')} |", f"| carrying | {pct('carrying')} |",
             f"| places not looked inside (exact list) | {pct('not_searched')} |", f"| all three | {pct('all')} |", "",
             f"Looked-inside places missed (summed over steps): {sum(r['missed'] for r in rows)}; wrongly counted as looked "
             f"inside: {sum(r['extra'] for r in rows)}.", "",
             "| per record | right |", "|---|---|"]
    for q in ("arrived", "searched", "carry"):
        lines.append(f"| {q} | {rec[(q, 'right')]}/{rec[(q, 'n')]} ({100 * rec[(q, 'right')] / max(1, rec[(q, 'n')]):.1f}%) |")
    lines += ["", f"Records with an unusable answer: {rec['unusable']}. Requests: {client.new} new, {client.reused} from cache, "
              f"{client.seconds:.0f}s in new requests."]
    with (out / "steps.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text, encoding="utf-8")
    print("\n" + text)


if __name__ == "__main__":
    main()
