"""Export completed ALFWorld rollouts without model or simulator calls."""
import argparse
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from paired_store import load


def trajectory_rows(fork, result, game):
    prefix = fork["prefix"]
    history = prefix["history"] + result["suffix"]
    if result["prefix_hash"] != fork["hash"] or len(history) != result["total_env_steps"] + 1:
        raise ValueError("Trajectory result disagrees with its saved prefix or step count.")
    yield {"event": "reset", "game": game, "arm": result["arm"], "task": prefix["task"],
           **{k: fork[k] for k in ("action_example_id", "action_example_sha256") if k in fork},
           "prefix_hash": fork["hash"], "prefix_steps": fork["step"],
           "step": 0, "observation": history[0]["observation"], "record_id": history[0]["id"]}
    step = 0

    def execute(event, proposal, command, review=None):
        nonlocal step
        step += 1
        record = history[step]
        if record["action"] != command:
            raise ValueError(f"Step {step}: saved action disagrees with environment history.")
        row = {"event": event, "step": step, "record_id": record["id"], "proposed_action": proposal,
               "executed_action": command, "observation": record["observation"]}
        if review is not None:
            row["review"] = review
        return row

    for decision in result["decisions"]:
        if not step <= decision["step"] <= result["total_env_steps"]:
            raise ValueError("Decision is outside the recorded trajectory or out of order.")
        while step < decision["step"]:
            action = history[step + 1]["action"]
            yield execute("action", action, action)
        proposal, chosen = decision["proposal"], decision["chosen"]
        review = []
        for entry in result["intervention"][decision["trace_start"]:decision["trace_end"]]:
            if "probe" in entry:
                if entry["probe"] != history[step + 1]:
                    raise ValueError("Read-only probe disagrees with environment history.")
                yield execute("probe", proposal, entry["probe"]["action"], review)
                review = []
            else:
                review.append(entry)
        if chosen is None:
            yield {"event": "not_executed", "step": step, "proposed_action": proposal,
                   "executed_action": None, "review": review}
        else:
            yield execute("action", proposal, chosen, review)
    while step < result["total_env_steps"]:
        action = history[step + 1]["action"]
        yield execute("action", action, action)
    yield {"event": "end", "step": step, "won": result["won"], "reason": result["end"],
           "token_usage": result["token_usage"]}


def export(out):
    count = 0
    for prefix_path in sorted(out.glob("game*/*/prefix.json")):
        folder = prefix_path.parent
        for arm in ("direct", "llm_eda"):
            result_path = folder / f"{arm}.json"
            if not result_path.is_file():
                continue
            rows = trajectory_rows(load(prefix_path), load(result_path), folder.parent.name)
            with NamedTemporaryFile("w", dir=folder, encoding="utf-8", delete=False) as f:
                tmp = Path(f.name)
                try:
                    for row in rows:
                        f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                    tmp.replace(folder / f"{arm}.trajectory.jsonl")
                finally:
                    tmp.unlink(missing_ok=True)
            count += 1
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    if not args.out.is_dir():
        parser.error(f"Run directory does not exist: {args.out}")
    print(f"Exported {export(args.out)} completed trajectories in {args.out}.")
