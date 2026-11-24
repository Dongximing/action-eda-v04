"""Add LLM-generated dynamic suspicions (doc v0.4 §3.2) to samples.

For each sample, a generative model reads the task, the visible history and the
proposed action and lists up to K conditions that, if false, would make the action
wrong. Each must name a concrete entity/parameter of the action. The new claims
are appended with origin="dynamic". They have no gold label: a labelling
template is written to <out>/to_label.jsonl (fill "gold", then merge into labels).

  python scripts/generate_claims.py --samples data/x/samples.jsonl --out data/x_dyn \
      --model Qwen/Qwen3-4B --k 3
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aeda.backends import HFOptionBackend, Query  # noqa: E402
from aeda.schema import read_jsonl, write_jsonl  # noqa: E402

PROMPT = """An agent is about to execute an action. List up to {k} conditions that must hold right now
for this action to be correct, and that could plausibly be false given the history.
Each condition must refer to a concrete entity or parameter of the proposed action.
Do not repeat these already-checked conditions:
{fixed}

Task: {task}
History (oldest first):
{hist}
Proposed action (not executed yet): {action}

Return a JSON list of objects {{"text": str, "kind": "state" | "default", "entities": [str]}}.
Use "default" for conditions of the form "X has not happened". Output JSON only."""


def parse_list(text: str):
    mt = re.search(r"\[.*\]", text or "", re.S)
    if not mt:
        return []
    try:
        out = json.loads(mt.group(0))
    except json.JSONDecodeError:
        return []
    return [x for x in out if isinstance(x, dict) and isinstance(x.get("text"), str)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="Qwen/Qwen3-4B")
    ap.add_argument("--device", default=None)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--max-new-tokens", type=int, default=400)
    a = ap.parse_args()

    gen = HFOptionBackend(a.model, device=a.device)
    rows, todo = [], []
    for s in read_jsonl(a.samples):
        hist = "\n".join(f"[#{r['rid']} | {r['source']}] {r['text']}" for r in s["records"]) or "(none)"
        fixed = "\n".join(f"- {c['text']}" for c in s["claims"]) or "(none)"
        prompt = PROMPT.format(k=a.k, fixed=fixed, task=s["task"], hist=hist, action=s["proposed_action"])
        items = parse_list(gen.generate(Query("gen_claims", prompt, sid=s["sid"]), a.max_new_tokens))[: a.k]
        for i, it in enumerate(items):
            cid = f"{s['sid']}/d{i}"
            kind = it.get("kind") if it.get("kind") in ("state", "default") else "state"
            ents = [e for e in it.get("entities", []) if isinstance(e, str)]
            s["claims"].append({"cid": cid, "text": it["text"], "kind": kind, "origin": "dynamic", "entities": ents})
            todo.append({"sid": s["sid"], "cid": cid, "claim": it["text"], "action": s["proposed_action"],
                         "gold": "", "order_sensitive": None, "composition": None, "indirect": None,
                         "synthetic": False})
        rows.append(s)
    out = Path(a.out)
    write_jsonl(out / "samples.jsonl", rows)
    write_jsonl(out / "to_label.jsonl", todo)
    meta = {"model": a.model, "k": a.k, "usage": gen.usage.as_dict(), "n_dynamic": len(todo)}
    (out / "gen_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
