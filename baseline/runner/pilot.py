"""Run ALFWorld actions, or compare five auditors on frozen pre-action observations."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
from collections import Counter
from pathlib import Path

from audit import ACTION_GUIDE, audit, checkpoint_action, prepare
from models import GPUChat, NativeJev
from providers import ProviderError
from state_baseline import predict as state_tracker

FAMILIES = {name: f"pick_{name}_then_place_in_recep" for name in ("clean", "heat", "cool")}
ARMS = {"jev_full": ("jev", "full"), "jev_retrieved": ("jev", "retrieved"),
        "jev_eda": ("jev", "eda"), "reviewer_full": ("reviewer", "full"),
        "reviewer_eda": ("reviewer", "eda")}


def dump_line(stream, row):
    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    stream.flush()


def public_checkpoint(view, action):
    return {"task": view["task"], "observation": view["observation"], "action": action,
            "history": [{k: r[k] for k in ("id", "action", "observation")} for r in view["history"]],
            "action_guide": ACTION_GUIDE}


def sample_games(split_dir, per_family, seed, all_tasks=False):
    if split_dir.name not in ("valid_seen", "valid_unseen"):
        raise ValueError("provide the path to a single valid_seen or valid_unseen split")
    games = [g for g in sorted(split_dir.glob("*/*/game.tw-pddl"))
             if "Sliced" not in g.parent.parent.name and json.loads(g.read_bytes()).get("solvable") is True]
    if all_tasks:
        if not games:
            raise ValueError(f"no eligible games found in {split_dir}")
        return games
    out = []
    for family, prefix in FAMILIES.items():
        matches = [g for g in games if g.relative_to(split_dir).parts[0].split("-")[0] == prefix]
        if len(matches) < per_family:
            raise ValueError(f"{family}: found {len(matches)} games, requested {per_family}")
        rng = random.Random(f"{seed}/{family}")
        out.extend(rng.sample(matches, per_family))
    random.Random(seed).shuffle(out)
    return out


def menu_for(cp, actor, jev, k):
    failure = None
    try:
        risks = actor.risks(cp, k=k)
    except ProviderError as exc:
        risks, failure = [], str(exc)
    prepared = prepare(cp, risks, jev.choice)
    if failure:
        prepared.update(menu_failed=True, generator_error=failure)
    return prepared


def review_action(env, cp, actor, jev, reviewer, k, max_steps, log, method="eda"):
    """At most one read and one replacement per proposal. Check each replacement again."""
    probed, revised = False, False
    original = cp["action"]
    while True:
        if not checkpoint_action(cp["action"]):
            # Only ordinary navigation and observation can skip review as a replacement.
            if not revised or cp["action"] in ("look", "inventory") or re.fullmatch(
                    r"(go to|examine) [a-z][a-z0-9 _-]* [0-9]+", cp["action"]):
                return cp["action"]
            return None
        frozen = menu_for(cp, actor, jev, k)
        judgment = audit(cp, frozen, jev.choice, method)
        log({"event": "audit", "action": cp["action"], "prepared": frozen, "judgment": judgment})
        if judgment["status"] == "SUPPORTED":
            return cp["action"]
        if revised:
            return None
        recommendation = reviewer.review(cp, frozen, judgment, allow_probe=not probed)
        log({"event": "review", **recommendation})
        kind, command = recommendation["kind"], recommendation["action"]
        if kind == "probe" and not probed and command in ("look", "inventory") and env.steps < max_steps:
            view = env.step(command)
            log({"event": "probe", "action": command, "observation": view["observation"]})
            if env.done or env.steps >= max_steps:
                return None
            cp = public_checkpoint(view, original)
            probed = True
        elif kind == "replace" and command != cp["action"]:
            if command in ("look", "inventory"):
                # Read-only commands consume the explicit probe budget.
                return None
            cp = public_checkpoint(env.view(), command)
            revised = True
        else:
            return None


def run_episodes(args, actor, jev, reviewer, root):
    from alf_env import Episode
    games = sample_games(args.split_dir, args.per_family, args.seed, args.all_tasks)
    manifest = [str(g.relative_to(args.split_dir)) for g in games]
    (root / "games.json").write_text(json.dumps(manifest, indent=2))
    counts = Counter()
    with (root / "prefixes.jsonl").open("x") as public, (root / "environment.jsonl").open("x") as private:
        for game, name in zip(games, manifest):
            episode = hashlib.sha256(name.encode()).hexdigest()[:16]
            episode_log = lambda data: dump_line(private, {"episode": episode, **data})
            env = Episode(game, show_admissible=False)
            try:
                env.reset()
                end = "step_limit"
                while env.steps < args.max_steps and not env.done:
                    view = env.view()
                    cp = public_checkpoint(view, actor.action(public_checkpoint(view, "")))
                    identity = f"{episode}:{env.steps}"
                    dump_line(public, {"id": identity, "episode": episode,
                                       "proposed_action": cp["action"], "prefix": view})
                    counts["proposed_actions"] += 1
                    counts["checkpoints"] += int(checkpoint_action(cp["action"]))
                    log = lambda data: episode_log({"id": identity, **data})
                    command = (review_action(env, cp, actor, jev, reviewer, args.k, args.max_steps, log, args.audit_method)
                               if args.mode == "online" else cp["action"])
                    if command is None:
                        end = "step_limit" if env.steps >= args.max_steps else "abstain"
                        break
                    new_view = env.step(command)
                    log({"event": "executed", "action": command, "observation": new_view["observation"]})
                if env.done:
                    end = "success" if env.won else "environment_end"
                counts["episodes"] += 1
                counts[end] += 1
                episode_log({"event": "end", "reason": end, "env_steps": env.steps})
            finally:
                env.close()
    return dict(counts)


def compare(args, actor, jev, reviewer, root):
    counts = Counter()
    seen = set()
    with args.input.open() as source, (root / "judgments.jsonl").open("x") as output:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row["id"] in seen:
                raise ValueError("duplicate checkpoint ID")
            seen.add(row["id"])
            cp = public_checkpoint(row["prefix"], row["proposed_action"])
            counts["prefixes"] += 1
            if not checkpoint_action(cp["action"]):
                continue
            frozen = menu_for(cp, actor, jev, args.k)
            groups = {"jev": jev, "reviewer": reviewer}
            arms = {}
            for arm, (role, method) in ARMS.items():
                client = groups[role]
                before = len(client.calls)
                arms[arm] = audit(cp, frozen, client.choice, method)
                arms[arm]["physical_calls"] = client.calls[before:]
            dump_line(output, {"id": row["id"], "prepared": frozen, "arms": arms,
                               "state_tracker": state_tracker(cp["action"], cp["history"])})
            counts["checkpoints"] += 1
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("collect", "compare", "online"):
        p = sub.add_parser(name)
        p.add_argument("--out", type=Path, required=True)
        p.add_argument("--k", type=int, choices=range(1, 9), default=3)
        if name == "compare":
            p.add_argument("--input", type=Path, required=True)
        else:
            p.add_argument("--split-dir", type=Path, required=True)
            selection = p.add_mutually_exclusive_group()
            selection.add_argument("--per-family", type=int, default=4)
            selection.add_argument("--all-tasks", action="store_true", help="all eligible games across every task family")
            p.add_argument("--seed", type=int, default=42)
            p.add_argument("--max-steps", type=int, default=50)
            if name == "online":
                p.add_argument("--audit-method", choices=("full", "retrieved", "eda"), default="eda")
    args = parser.parse_args()
    if args.mode != "compare" and (args.per_family < 1 or args.max_steps < 1):
        parser.error("per-family and max-steps must be positive")
    actor_url = os.getenv("ACTOR_URL", "http://127.0.0.1:8000/v1")
    actor = GPUChat(actor_url, os.getenv("ACTOR_MODEL", "Qwen/Qwen3.5-9B"), os.getenv("ACTOR_API_KEY"))
    clients = {"actor": actor}
    jev = reviewer = None
    if args.mode != "collect":
        jev = NativeJev(os.getenv("JEV_MODEL", "jev-1.14.0"))
        reviewer_url = os.getenv("REVIEWER_URL", actor_url)
        reviewer_key = os.getenv("REVIEWER_API_KEY")
        if reviewer_url == actor_url and not reviewer_key:
            reviewer_key = os.getenv("ACTOR_API_KEY")
        reviewer = GPUChat(reviewer_url, os.getenv("REVIEWER_MODEL", actor.model), reviewer_key)
        clients.update(jev=jev, reviewer=reviewer)
    root = args.out
    root.mkdir(parents=True, exist_ok=False)
    metadata = {"mode": args.mode, "arguments": vars(args), "models": {k: c.model for k,c in clients.items()},
                "thinking": False, "admissible_command_list": False, "completed": False}
    try:
        if jev is not None:
            # A rejected credential or unusable model fails before collecting paid audit judgments.
            smoke = jev.choice({"record":"The box is closed."}, "What state is directly reported?",
                               {"closed":"Closed","open":"Open","unknown":"Not specified"})
            metadata["jev_readiness_choice"] = smoke
        metadata["counts"] = (compare(args, actor, jev, reviewer, root) if args.mode == "compare"
                              else run_episodes(args, actor, jev, reviewer, root))
        metadata["completed"] = True
    finally:
        metadata["usage"] = {k: c.usage() for k,c in clients.items()}
        with (root / "model_calls.jsonl").open("x") as raw:
            for role, client in clients.items():
                for index, call in enumerate(client.calls, 1):
                    dump_line(raw, {"role": role, "role_call_index": index, **call})
        (root / "run.json").write_text(json.dumps(metadata, indent=2, default=str))
    print(json.dumps(metadata["counts"], indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ProviderError, ValueError, OSError) as error:
        raise SystemExit(str(error)) from None
