#!/usr/bin/env python3
"""Replay one finished game of one arm and record every model input and output.

  python scripts/replay_io.py --folder runs/online/d1 --game game02 --arm jevexplore

The game is played again from a copy of its folder (the original is not touched), with the answer cache of the
finished run, so every model answer comes from that run and nothing is sent to a provider: the network is closed
and a missing answer stops the replay. For every request the run makes (agent model and decision model alike), the
exact request is rebuilt the way the run's code builds it (system prompt, user message / System One payload) and
written beside the answer:
  <folder>/readable/<game>_<arm>_io.jsonl   one JSON line per request
  <folder>/readable/<game>_<arm>_io.md      the same, readable; the demonstration is printed once
The replayed result is checked against the finished run's (same actions and outcome).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", default=str(ROOT / "runs/online/d1"))
    ap.add_argument("--game", required=True)
    ap.add_argument("--arm", required=True)
    a = ap.parse_args()
    os.environ["https_proxy"] = os.environ["HTTPS_PROXY"] = "http://127.0.0.1:9"   # no provider is reached
    os.environ.setdefault("OPENROUTER_API_KEY", "replay-only")
    import run_online as R
    sys.path.insert(0, str(R.DEFAULT_RUNNER))
    import models
    import paired_store

    folder = Path(a.folder)
    done = json.loads((folder / a.game / f"{a.arm}.json").read_text())
    tmp = Path(tempfile.mkdtemp(prefix="replay_io_"))
    shutil.copytree(folder / a.game, tmp / a.game)
    (tmp / a.game / f"{a.arm}.json").unlink()

    log: list[dict] = []
    orig_ask = paired_store.CallBook.ask

    def ask(self, scope, role, operation, inputs, client, perform):
        before = self.db.execute("SELECT COUNT(*) FROM answers").fetchone()[0]
        answer = orig_ask(self, scope, role, operation, inputs, client, perform)
        new = self.db.execute("SELECT COUNT(*) FROM answers").fetchone()[0] != before
        captured = {}
        saved = (models.GPUChat._respond, R.JevPlaces.ask)

        def cap_respond(_self, state, instruction, max_tokens, **kw):
            captured.update(kind="chat", system=instruction, user=state, max_tokens=max_tokens)
            return answer if isinstance(answer, dict) else {"action": answer}

        def cap_jev(_self, state, questions):
            captured.update(kind="system_one", state=state, questions=questions)
            return answer
        models.GPUChat._respond, R.JevPlaces.ask = cap_respond, cap_jev
        try:
            perform()          # rebuilds the request; the patched calls return the recorded answer
        except Exception as e:  # noqa: BLE001  (the request is what matters here)
            captured.setdefault("rebuild_error", f"{type(e).__name__}: {e}")
        finally:
            models.GPUChat._respond, R.JevPlaces.ask = saved
        log.append({"n": len(log) + 1, "who": "decision model (OneJev)" if role == "jev" else "agent model (qwen3.5-9b)",
                    "operation": operation, "from_cache": not new, "request": captured, "answer": answer})
        return answer
    paired_store.CallBook.ask = ask

    src = R.DEFAULT_SRC
    g = next(x for x in json.loads((src / "protocol.json").read_text())["games"] if x["id"] == a.game) \
        if (src / a.game).exists() else next(x for x in json.loads((folder / "protocol.json").read_text())["games"] if x["id"] == a.game)
    cfg = done.get("config", {})
    job = {"id": a.game, "game": g["game"], "family": g["family"], "action_example_sha256": g["action_example_sha256"],
           "src": str(src), "out": str(tmp), "runner": str(R.DEFAULT_RUNNER), "split": str(R.DEFAULT_SPLIT),
           "route": cfg.get("route", "parasail"), "adapter": cfg.get("adapter", ""), "fewshot": cfg.get("fewshot", ""),
           "record_style": cfg.get("record_style", "state"), "max_revisions": cfg.get("max_revisions", 1),
           "max_steps": cfg.get("max_steps", 50), "arm": a.arm, "tag": a.arm, "mw_k": 3, "mw_writer": "risks",
           "jev_url": cfg.get("jev_url", "http://127.0.0.1:8000/v1/systemone"), "jev_model": cfg.get("jev_model", "OneJev1.6-4B")}
    job["replay_cache"] = True   # rebuild from the stored answers; nothing is sent
    r = R.play(job)
    same = [h["action"] for h in r["history"]] == [h["action"] for h in done["history"]] and r["won"] == done["won"]

    out = folder / "readable"
    out.mkdir(exist_ok=True)
    base = out / f"{a.game}_{a.arm}_io"
    with open(f"{base}.jsonl", "w", encoding="utf-8") as fh:
        for x in log:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    md = [f"# {a.game} / {a.arm}: every model input and output", "",
          f"Task: {done['task']}  |  result: {'won' if r['won'] else 'lost'} in {r['steps']} steps  |  "
          f"replay identical to the finished run: {same}  |  requests: {len(log)} "
          f"({sum(not x['from_cache'] for x in log)} not in the cache)", ""]
    demo_shown = False
    step_of = {}
    for x in log:
        req = x["request"]
        md += [f"## Request {x['n']}: {x['who']}, {x['operation']}", ""]
        if req.get("kind") == "chat":
            system = req["system"]
            if "<example>" in system and demo_shown:
                system = system[:system.index("<example>")] + "<example> ... (the same demonstration as in the first request) </example>"
            demo_shown = demo_shown or "<example>" in req["system"]
            md += ["**System message**", "", "```", system, "```", "", "**User message (JSON)**", "", "```json",
                   json.dumps(req["user"], ensure_ascii=False, indent=1), "```", ""]
        elif req.get("kind") == "system_one":
            md += ["**System One request**", "", "```json", json.dumps({"state": req["state"], "questions": req["questions"]},
                                                                      ensure_ascii=False, indent=1), "```", ""]
        if req.get("rebuild_error"):
            md += [f"(request rebuild note: {req['rebuild_error']})", ""]
        md += ["**Answer**", "", "```json", json.dumps(x["answer"], ensure_ascii=False, indent=1), "```", ""]
    Path(f"{base}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    shutil.rmtree(tmp)
    print(f"{base}.md  ({len(log)} requests; replay identical: {same})")


if __name__ == "__main__":
    main()
