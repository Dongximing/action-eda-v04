#!/usr/bin/env python3
"""Online D1 on the ALFWorld games of a finished paired run (doc v0.4 §3.5, §6.3).

The main agent, environment, demonstrations, step budget and actor cache are the
ones of the baseline run (alfworld-action-eda-oneshot-altprovider, `direct` arm):
  * the actor (qwen/qwen3.5-9b via OpenRouter, route from routing.json, one-shot
    demo per family, temperature 0) proposes each action exactly as in the baseline;
    its calls go through the same CallBook cache (copied, never modified in --src),
    so until D1 first intervenes the trajectory is the baseline trajectory;
  * before a state-changing action, D1 checks its fixed preconditions against the
    visible history (aeda.alfworld.build_sample, identical to the offline data);
  * disposition for reversible actions (all ALFWorld actions):
      CONTRADICTED  -> blocked; the agent revises with the failed conditions and the
                       record ids that overturned them (models.GPUChat.revise); the
                       revision is checked again; at most --max-revisions revisions,
                       after which the last candidate is executed (counted separately)
      UNKNOWN / SUPPORTED / no preconditions -> executed
  * 50 environment steps per game, as in the baseline. A revision costs no env step.

Run with the ALFWorld venv (it has alfworld/textworld), from this repo:

  export OPENROUTER_API_KEY=...
  ~/state-audit-pilot/.venv/bin/python scripts/run_online.py \\
      --src ~/Documents/Codex/2026-11-21/yo/outputs/alfworld-9b-oneshot-alternate --out runs/online/d1

Results: <out>/gameXX/d1.json per game, <out>/summary.json and summary.md (wins of
D1 vs the baseline's natural.json on the same games).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aeda import alfworld as A  # noqa: E402
from aeda.schema import Sample  # noqa: E402
from aeda.verifiers import Config, run  # noqa: E402

YO = Path.home() / "Documents/Codex/2026-11-21/yo/outputs"
DEFAULT_RUNNER = YO / "alfworld-action-eda-oneshot-altprovider"
DEFAULT_SPLIT = Path.home() / "state-audit-pilot/data/alfworld/json_2.1.1/valid_seen"


# ---------------------------------------------------------------- checking and disposition (no env, testable)

@dataclass
class Check:
    status: str                      # CONTRADICTED / UNKNOWN / SUPPORTED / NONE (no preconditions)
    claims: list = field(default_factory=list)
    calls: int = 0

    def as_dict(self):
        return {"status": self.status, "claims": self.claims, "calls": self.calls}


def check_action(view: dict, action: str, episode_id: str, backend, cfg: Config) -> Check:
    hist = view["history"]
    steps = [(h["action"], h["observation"]) for h in hist[1:]]
    sd = A.build_sample(episode_id, view["task"], hist[0]["observation"], steps, len(steps), action)
    if sd is None:
        return Check("NONE")
    rows = run([Sample.from_dict(sd)], ["D1"], backend, cfg)
    errors = [r["error"] for r in rows if "error" in r]
    if errors:
        raise RuntimeError(f"D1 failed on {sd['sid']}: {errors[0]}")
    text = {c["cid"]: c["text"] for c in sd["claims"]}
    claims = [{"claim": text[r["cid"]], "verdict": r["verdict"],
               "evidence_records": [f"r{rid}" for rid in r["evidence"]]} for r in rows]
    verdicts = {c["verdict"] for c in claims}
    status = ("CONTRADICTED" if "CONTRADICTED" in verdicts else "UNKNOWN" if "UNKNOWN" in verdicts
              else "SUPPORTED")
    return Check(status, claims, sum(r["calls"] for r in rows))


def feedback(chk: Check) -> dict:
    """What the agent sees when blocked: the failed conditions and the records behind them."""
    return {"status": "CONTRADICTED",
            "conditions": [{"claim": c["claim"], "status": c["verdict"], "source_id": (c["evidence_records"] or [None])[0]}
                           for c in chk.claims if c["verdict"] == "CONTRADICTED"]}


def decide(view: dict, proposal: str, check, revise, max_revisions: int) -> tuple[str, dict | None]:
    """check(action) -> Check; revise(action, feedback) -> new action. Returns (action to execute, record)."""
    chk = check(proposal)
    if chk.status != "CONTRADICTED":
        return proposal, {"proposal": proposal, "check": chk.as_dict(), "blocked": False} if chk.status != "NONE" else None
    rec = {"proposal": proposal, "check": chk.as_dict(), "blocked": True, "revisions": []}
    cand = proposal
    for _ in range(max_revisions):
        new = revise(cand, feedback(chk))
        if new == cand:  # the agent keeps its action
            rec["revisions"].append({"action": new, "same_as_before": True})
            break
        cand = new
        chk = check(cand)
        rec["revisions"].append({"action": cand, "check": chk.as_dict()})
        if chk.status != "CONTRADICTED":
            break
    rec["executed"] = cand
    rec["executed_status"] = chk.status
    rec["executed_despite_contradiction"] = chk.status == "CONTRADICTED"
    return cand, rec


# ---------------------------------------------------------------- one game (needs alfworld + the runner modules)

def play(job: dict) -> dict:
    sys.path.insert(0, job["runner"])
    from alf_env import Episode
    from models import GPUChat
    from paired_store import CallBook, digest, load, save
    from pilot import public_checkpoint
    from aeda.backends import AdapterBackend

    folder = Path(job["out"]) / job["id"]
    out_path = folder / f"{job['arm']}.json"
    if out_path.exists():
        return json.loads(out_path.read_text())
    folder.mkdir(parents=True, exist_ok=True)
    src = Path(job["src"]) / job["id"]
    if not (folder / "calls.sqlite").exists():
        shutil.copy2(src / "calls.sqlite", folder / "calls.sqlite")   # actor cache of the baseline, copied
    natural = load(src / "natural.json")

    actor = GPUChat("https://openrouter.ai/api/v1", "qwen/qwen3.5-9b", os.environ["OPENROUTER_API_KEY"], openrouter=True)
    actor.openrouter_route = job["route"]
    example = load(Path(job["src"]) / "one_shot_examples.json")["examples"][job["family"]]
    if digest(example) != job["action_example_sha256"]:
        raise ValueError(f"{job['id']}: demonstration differs from the frozen protocol")
    actor.action_example = example
    backend = AdapterBackend(job["adapter"])
    cfg = Config(fewshot=job["fewshot"], record_style=job["record_style"])
    book = CallBook(folder / "calls.sqlite")
    env = Episode(Path(job["split"]) / job["game"])
    t0, first_request = time.time(), book.last_request_id()
    try:
        view = env.reset()
        if view["task"] != natural["task"] or view["history"][0] != natural["history"][0]:
            raise ValueError(f"{job['id']}: reset differs from the baseline")
        decisions = []
        while env.steps < job["max_steps"] and not env.done:
            cp = public_checkpoint(view, "")
            inputs = [cp, digest(example)]
            proposal = book.ask("d1", "qwen", "actor", inputs, actor, lambda: actor.action(cp))
            step = env.steps

            def revise(action, fb, view=view):
                c = public_checkpoint(view, action)
                return book.ask("d1", "qwen", "revise", [c, fb], actor, lambda: actor.revise(c, fb))
            chosen, rec = decide(view, proposal, lambda a, view=view: check_action(view, a, job["id"], backend, cfg),
                                 revise, job["max_revisions"])
            view = env.step(chosen)
            if rec is not None:
                obs = view["history"][-1]["observation"]
                rec.update(step=step, observation=obs, succeeded=A.succeeded(obs))
                decisions.append(rec)
        hist = view["history"]
        diverged = next((i for i, (a, b) in enumerate(zip(hist, natural["history"])) if a != b),
                        None if len(hist) == len(natural["history"]) else min(len(hist), len(natural["history"])))
        new_actor = book.db.execute("SELECT COUNT(*) FROM requests WHERE id>? AND reused=0 AND ok=1",
                                    (first_request,)).fetchone()[0]
        result = {"id": job["id"], "family": job["family"], "task": view["task"], "arm": job["arm"],
                  "won": env.won, "steps": env.steps,
                  "end": "success" if env.won else "environment_end" if env.done else "step_limit",
                  "baseline_won": natural["won"], "baseline_steps": natural["steps"],
                  "diverged_from_baseline_at": diverged, "history": hist, "decisions": decisions,
                  "usage": {"judge": backend.usage.as_dict(), "new_actor_requests": new_actor,
                            "seconds": round(time.time() - t0, 1)},
                  "config": {k: job[k] for k in ("adapter", "fewshot", "record_style", "max_revisions",
                                                 "max_steps", "route")}}
        save(out_path, result)
        return result
    finally:
        env.close()
        book.close()


# ---------------------------------------------------------------- summary

def summarize(results: list[dict], out: Path) -> dict:
    results = sorted(results, key=lambda r: r["id"])
    rows, tot = [], {"blocked": 0, "revised": 0, "kept": 0, "despite": 0, "false_block": 0}
    for r in results:
        blocks = [d for d in r["decisions"] if d["blocked"]]
        fb = 0
        for d in blocks:  # tracker on the same visible prefix: was any blocked claim actually true?
            steps = [(h["action"], h["observation"]) for h in r["history"][1:d["step"] + 1]]
            st = A.replay(steps)
            specs = {p["text"]: p["spec"] for p in A.preconditions(d["proposal"])}
            if not any(A.evaluate_spec(specs[c["claim"]], st) == "CONTRADICTED"
                       for c in d["check"]["claims"] if c["verdict"] == "CONTRADICTED"):
                fb += 1
        row = {"id": r["id"], "family": r["family"], "baseline_won": r["baseline_won"], "d1_won": r["won"],
               "baseline_steps": r["baseline_steps"], "d1_steps": r["steps"], "checks": len(r["decisions"]),
               "blocked": len(blocks), "revised": sum(any(not v.get("same_as_before") for v in d["revisions"]) for d in blocks),
               "agent_kept_action": sum(any(v.get("same_as_before") for v in d["revisions"]) for d in blocks),
               "executed_despite_contradiction": sum(d["executed_despite_contradiction"] for d in blocks),
               "false_blocks_vs_tracker": fb, "diverged_at": r["diverged_from_baseline_at"],
               "judge_calls": r["usage"]["judge"]["calls"], "new_actor_requests": r["usage"]["new_actor_requests"]}
        rows.append(row)
        tot["blocked"] += row["blocked"]
        tot["revised"] += row["revised"]
        tot["kept"] += row["agent_kept_action"]
        tot["despite"] += row["executed_despite_contradiction"]
        tot["false_block"] += fb
    s = {"games": len(rows), "baseline_wins": sum(r["baseline_won"] for r in rows),
         "d1_wins": sum(r["d1_won"] for r in rows),
         "rescued": [r["id"] for r in rows if r["d1_won"] and not r["baseline_won"]],
         "lost": [r["id"] for r in rows if r["baseline_won"] and not r["d1_won"]],
         "totals": tot, "per_game": rows}
    (out / "summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
    lines = [f"# Online D1 vs baseline on {s['games']} ALFWorld games", "",
             f"Wins: baseline {s['baseline_wins']}/{s['games']}, D1 {s['d1_wins']}/{s['games']}. "
             f"Rescued: {', '.join(s['rescued']) or '-'}. Lost: {', '.join(s['lost']) or '-'}.", "",
             f"Blocked {tot['blocked']} proposals; agent revised {tot['revised']}, kept its action {tot['kept']}; "
             f"executed despite contradiction {tot['despite']}; blocks the tracker calls wrong: {tot['false_block']}.", "",
             "| game | family | baseline | D1 | steps b/D1 | checks | blocked | revised | kept | despite | false blocks | diverged at |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['family'].replace('_then_place_in_recep', '')} | "
                     f"{'win' if r['baseline_won'] else '-'} | {'win' if r['d1_won'] else '-'} | "
                     f"{r['baseline_steps']}/{r['d1_steps']} | {r['checks']} | {r['blocked']} | {r['revised']} | "
                     f"{r['agent_kept_action']} | {r['executed_despite_contradiction']} | {r['false_blocks_vs_tracker']} | "
                     f"{r['diverged_at'] if r['diverged_at'] is not None else '-'} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="finished paired run with protocol.json, routing.json, gameXX/")
    ap.add_argument("--out", required=True)
    ap.add_argument("--runner", default=str(DEFAULT_RUNNER), help="dir with alf_env.py, models.py, paired_store.py, pilot.py")
    ap.add_argument("--split-dir", default=str(DEFAULT_SPLIT))
    ap.add_argument("--games", default="", help="comma list, e.g. game01,game02 (default: all in protocol.json)")
    ap.add_argument("--adapter", default="adapters.openrouter_chat:choose", help="decision model for D1")
    ap.add_argument("--fewshot", default=str(ROOT / "data/fewshot/alfworld_record_fewshot.json"))
    ap.add_argument("--record-style", default="state", choices=["effect", "state"])
    ap.add_argument("--max-revisions", type=int, default=1)
    ap.add_argument("--max-steps", type=int, default=50)
    ap.add_argument("--workers", type=int, default=4, help="games in parallel")
    ap.add_argument("--arm", default="d1")
    a = ap.parse_args()
    if not os.getenv("OPENROUTER_API_KEY"):
        ap.error("set OPENROUTER_API_KEY in this terminal")
    src = Path(a.src).expanduser()
    protocol = json.loads((src / "protocol.json").read_text())
    if protocol.get("max_steps") != a.max_steps:
        print(f"note: baseline used max_steps={protocol.get('max_steps')}, this run {a.max_steps}", flush=True)
    route = json.loads((src / "routing.json").read_text())["selected"]
    want = {g for g in a.games.split(",") if g}
    games = [g for g in protocol["games"] if not want or g["id"] in want]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_config.json").write_text(json.dumps({**vars(a), "route": route, "baseline_protocol": str(src / "protocol.json")}, indent=1))
    jobs = [{"id": g["id"], "game": g["game"], "family": g["family"], "action_example_sha256": g["action_example_sha256"],
             "src": str(src), "out": str(out), "runner": str(Path(a.runner).expanduser()), "split": str(Path(a.split_dir).expanduser()),
             "route": route, "adapter": a.adapter, "fewshot": a.fewshot, "record_style": a.record_style,
             "max_revisions": a.max_revisions, "max_steps": a.max_steps, "arm": a.arm} for g in games]
    results, failed = [], []
    with ProcessPoolExecutor(max_workers=max(1, a.workers)) as ex:
        futs = {ex.submit(play, j): j["id"] for j in jobs}
        for f in as_completed(futs):
            gid = futs[f]
            try:
                r = f.result()
                results.append(r)
                print(f"{gid}: {'WIN' if r['won'] else r['end']} in {r['steps']} steps "
                      f"(baseline {'win' if r['baseline_won'] else 'loss'}), "
                      f"{sum(d['blocked'] for d in r['decisions'])} blocked", flush=True)
            except Exception as e:  # report and keep the other games; rerun resumes finished games from disk
                failed.append(gid)
                print(f"{gid}: FAILED {type(e).__name__}: {e}", flush=True)
    s = summarize(results, out)
    print(f"\nbaseline {s['baseline_wins']}/{s['games']}  D1 {s['d1_wins']}/{s['games']}  -> {out / 'summary.md'}")
    if failed:
        print(f"failed games (rerun the same command to resume): {', '.join(sorted(failed))}")
        sys.exit(2)


if __name__ == "__main__":
    main()
