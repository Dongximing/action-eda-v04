#!/usr/bin/env python3
"""Compare ALFWorld decision policies on the same twelve fixed games using measured API token usage."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import itertools
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from getpass import getpass
from importlib.metadata import version
from pathlib import Path

from alf_env import Episode
from audit import DELTA, SOURCE, audit, checkpoint_action, prepare
from models import GPUChat, NativeJev
from paired_store import CallBook, digest, freeze, load, physical_usage, save, token_totals
from pilot import public_checkpoint
from providers import ProviderError

HERE = Path(__file__).resolve().parent
GAMES = HERE / "smoke/dev_availability.json"
EXAMPLES = HERE / "one_shot_examples.json"
ROUTES = ("parasail", "siliconflow", "darkbloom", "together")
ARMS = ("direct", "llm_eda", "self_revise", "jev_full", "jev_eda")
TWO_ARMS = ("direct", "llm_eda")
SLOTS = ("first_other_write", "first_process")
PROCESS_VERBS = {"clean", "heat", "cool"}


def resources(provider):
    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("Set OPENROUTER_API_KEY in the terminal running this experiment.")
        client = GPUChat("https://openrouter.ai/api/v1", "qwen/qwen3.5-9b", key, openrouter=True)
        client.openrouter_route = os.getenv("ALFWORLD_SELECTED_ROUTE")
        return client
    url = os.getenv("ACTOR_URL", "http://127.0.0.1:8000/v1")
    return GPUChat(url, "Qwen/Qwen3.5-9B", os.getenv("ACTOR_API_KEY"))


def slot_for(action):
    if not checkpoint_action(action):
        return None
    return SLOTS[1] if action.lower().split()[0] in PROCESS_VERBS else SLOTS[0]


def next_action(book, scope, actor, view):
    cp = public_checkpoint(view, "")
    example = getattr(actor, "action_example", None)
    inputs = [cp, digest(example)] if example else cp
    return book.ask(scope, "qwen", "actor", inputs, actor, lambda: actor.action(cp))


def replay(env, fork):
    before = fork["prefix"]
    view = env.reset()
    rows = before["history"]
    if not rows or view["task"] != before["task"] or view["history"] != rows[:1]:
        raise ValueError("Replay diverged at reset.")
    for record in rows[1:]:
        if env.done:
            raise ValueError("Episode terminated before the frozen checkpoint.")
        view = env.step(record["action"])
        if view["history"][-1] != record:
            raise ValueError(f"Replay observation mismatch at {record['id']}.")
    if view != before or env.done or env.steps != fork["step"] or digest([view, fork["proposal"]]) != fork["hash"]:
        raise ValueError("Replay did not recover the frozen public prefix and proposal.")
    return view


def natural_rollout(folder, game, row, actor, book, maximum, design="prefix"):
    path = folder / "natural.json"
    if path.exists():
        return load(path)
    env = Episode(game)
    try:
        view = env.reset()
        selected, actor_request_ids = [], []
        while not env.done and env.steps < maximum:
            scope = "direct" if design == "episode" else "natural"
            action = next_action(book, scope, actor, view)
            actor_request_ids.append(book.last_request_id())
            if design == "episode":
                slot = "episode_start" if env.steps == 0 else None
            else:
                slot = slot_for(action)
            if slot and slot not in selected:
                # Freeze solely from the public state and proposed action, before receiving its outcome.
                fork = {"step": env.steps, "proposal": action, "prefix": view, "hash": digest([view, action])}
                if "action_example_id" in row:
                    fork["action_example_id"] = row["action_example_id"]
                    fork["action_example_sha256"] = row["action_example_sha256"]
                freeze(folder / slot / "prefix.json", fork)
                selected.append(slot)
            view = env.step(action)
        result = {"game": row["game"], "family": row["family"], "task": view["task"], "selected": selected,
                  "won": env.won, "steps": env.steps, "history": view["history"], "actor_request_ids": actor_request_ids,
                  "token_usage": book.standalone_tokens(actor_request_ids),
                  "end": "success" if env.won else "environment_end" if env.done else "step_limit"}
        save(path, result)
        print(f"{folder.name}: natural {env.steps} steps, {len(selected)} prefix(es), {result['end']}", flush=True)
        return result
    finally:
        env.close()


def replacement_gate(action, history):
    """Check non-mutating replacement commands against the public command syntax and observed target."""
    if action in ("inventory", "look", "help"):
        return {"status": "SUPPORTED", "source_id": None, "rule": "public read-only command"}
    match = re.fullmatch(r"(?:go to|examine) ([a-z][a-z0-9 _-]* [0-9]+)", action, re.I)
    if match:
        pattern = re.compile(r"(?<!\w)" + re.escape(match.group(1)) + r"(?!\w)", re.I)
        for row in reversed(history):
            if pattern.search(row["observation"]):
                return {"status": "SUPPORTED", "source_id": row["id"], "rule": "target in a public observation"}
    return {"status": "UNKNOWN", "source_id": None, "rule": "unrecognized command or unobserved target"}


def judged_action(cp, arm, actor, jev, book, trace, query=None):
    """The llm_eda arm uses the acting 9B for risk selection, single-record judgments and revision."""
    if arm == "direct":
        return cp["action"]
    if arm == "self_revise":
        revised = book.ask(arm, "qwen", "revise", [cp, None], actor, lambda: actor.revise(cp, None))
        trace.append({"revision": revised})
        return revised
    judge = actor if arm == "llm_eda" else jev
    judge_role = "qwen" if arm == "llm_eda" else "jev"

    def choose(stage):
        def call(state, instruction, options):
            args = [state, instruction, options]
            operation = {SOURCE: "eda_source", DELTA: "eda_delta"}.get(instruction, stage)
            return book.ask(arm, judge_role, operation, args, judge, lambda: judge.choice(*args))
        return call

    def check(candidate):
        risks = book.ask(arm, "qwen", "risk_menu", candidate, actor, lambda: actor.risks(candidate, k=3))
        frozen = prepare(candidate, risks, choose("select_risk"))
        judgment = audit(candidate, frozen, choose(arm), "full" if arm == "jev_full" else "eda")
        if any("error" in r for r in frozen["calls"] + judgment["calls"]):
            raise ProviderError("The audit model did not return a valid decision. The run can be resumed.")
        trace.append({"action": candidate["action"], "prepared": frozen, "audit": judgment})
        return frozen, judgment

    used_query = False
    while True:
        frozen, judgment = check(cp)
        if judgment["status"] == "SUPPORTED":
            return cp["action"]
        selection = {"selection": frozen["selection"], "menu": frozen["menu"]}
        evidence = {"status": judgment["status"], "conditions": [
            {k: item[k] for k in ("claim", "status", "source_id", "witness_id")} for item in judgment["claims"]]}
        if query is None:
            # The earlier single-intervention design permits one replacement and no intermediate read.
            feedback = {**selection, **evidence}
            revised = book.ask(arm, "qwen", "revise", [cp, feedback], actor, lambda: actor.revise(cp, feedback))
            trace.append({"revision": revised})
            break
        allow_probe = judgment["status"] == "UNKNOWN" and not used_query
        args = [cp, selection, evidence, allow_probe]
        recommendation = book.ask(arm, "qwen", "review", args, actor, lambda: actor.review(*args))
        trace.append({"review": recommendation})
        if recommendation["kind"] == "abstain":
            return None
        if recommendation["kind"] == "replace":
            revised = recommendation["action"]
            break
        if not allow_probe or recommendation["kind"] != "probe" or recommendation["action"] not in ("look", "inventory"):
            raise ProviderError("Reviewer returned a command outside the read-only query budget.")
        view, ended = query(recommendation["action"])
        trace.append({"probe": view["history"][-1]})
        if ended:
            return None
        used_query = True
        cp = public_checkpoint(view, cp["action"])
    if revised == cp["action"]:
        trace.append({"replacement_gate": {"status": "unresolved", "action": revised}})
        return None
    if checkpoint_action(revised):
        _, second = check({**cp, "action": revised})
        return revised if second["status"] == "SUPPORTED" else None
    gate = replacement_gate(revised, cp["history"])
    trace.append({"replacement_gate": {**gate, "action": revised}})
    return revised if gate["status"] == "SUPPORTED" else None


def rollout_branch(folder, game, fork, natural, arm, actor, jev, book, maximum, design="prefix"):
    path = folder / f"{arm}.json"
    if path.exists():
        return
    env = Episode(game)
    try:
        view = replay(env, fork)
        mark = book.last_request_id()
        trace, decisions = [], []
        first_action = None
        abstained = False

        def query(action):
            observed = env.step(action)
            return observed, env.done or env.steps >= maximum

        while env.steps < maximum and not env.done:
            first = env.steps == fork["step"]
            proposal = fork["proposal"] if first else next_action(book, arm, actor, view)
            check = checkpoint_action(proposal) if design == "episode" else first
            chosen = proposal
            if arm != "direct" and check:
                start, proposal_step = len(trace), env.steps
                chosen = judged_action(public_checkpoint(view, proposal), arm, actor, jev, book, trace,
                                       query=query if design == "episode" else None)
                view = env.view()
                decisions.append({"step": proposal_step, "proposal": proposal, "chosen": chosen,
                                  "trace_start": start, "trace_end": len(trace)})
            if first:
                first_action = chosen
            if chosen is None:
                abstained = True
                break
            view = env.step(chosen)
        if arm == "direct" and (view["history"] != natural["history"] or env.won != natural["won"]):
            raise ValueError("Direct branch differs from the natural trajectory; no paired score was saved.")
        status = "abstain" if abstained and env.steps < maximum else "step_limit"
        if env.done:
            status = "success" if env.won else "environment_end"
        # Both policies needed the actor proposals up to and including the fork.
        shared = natural["actor_request_ids"][:fork["step"] + 1]
        tokens = book.standalone_tokens(shared, after=mark)
        save(path, {"arm": arm, "prefix_hash": fork["hash"], "replay_verified": True,
                    "prefix_steps": fork["step"], "remaining_step_budget": maximum - fork["step"],
                    "proposal": fork["proposal"], "chosen": first_action, "won": env.won, "end": status,
                    "total_env_steps": env.steps, "suffix": view["history"][fork["step"] + 1:],
                    "intervention": trace, "decisions": decisions, "token_usage": tokens})
    finally:
        env.close()


def run_game(job):
    out, split, row, arms, provider, maximum, jev_model, design = job
    game = split / row["game"]
    folder = out / row["id"]
    folder.mkdir(exist_ok=True)
    book = CallBook(folder / "calls.sqlite")
    try:
        actor = resources(provider)
        if "action_example_sha256" in row:
            actor.action_example = load(EXAMPLES)["examples"][row["family"]]
            if digest(actor.action_example) != row["action_example_sha256"]:
                raise ValueError("The action demonstration differs from the frozen game manifest.")
        jev = NativeJev(jev_model) if any(a.startswith("jev_") for a in arms) else None
        natural = natural_rollout(folder, game, row, actor, book, maximum, design)
        for slot in natural["selected"]:
            work = folder / slot
            fork = load(work / "prefix.json")
            for arm in arms:
                rollout_branch(work, game, fork, natural, arm, actor, jev, book, maximum, design)
        print(f"{row['id']}: paired branches finished", flush=True)
    finally:
        book.close()


def summarize(out, games, requested, design="prefix"):
    natural, pairs = [], []
    usage = defaultdict(Counter)
    all_arms = set(requested)
    for g in games:
        folder = out / g["id"]
        if (folder / "calls.sqlite").is_file():
            for group, count in physical_usage(folder / "calls.sqlite").items():
                usage[group].update(count)
        if not (folder / "natural.json").is_file():
            continue
        trunk = load(folder / "natural.json")
        natural.append({"game_id": g["id"], "family": g["family"], "won": trunk["won"],
                        "steps": trunk["steps"], "selected": trunk["selected"]})
        for slot in trunk["selected"]:
            branch = {"game_id": g["id"], "family": g["family"], "slot": slot, "outcomes": {}}
            for arm in ARMS:
                path = folder / slot / f"{arm}.json"
                if path.is_file():
                    result = load(path)
                    all_arms.add(arm)
                    branch["outcomes"][arm] = {"won": result["won"], "end": result["end"],
                                               "changed_actions": sum(d["chosen"] != d["proposal"] for d in result["decisions"]),
                                               "checkpoints_reviewed": len(result["decisions"]),
                                               "token_usage": result["token_usage"]}
            pairs.append(branch)
    results = {}
    for arm in ARMS:
        if arm not in all_arms:
            continue
        rows = [r for r in pairs if arm in r["outcomes"]]
        measured = [r["outcomes"][arm]["token_usage"] for r in rows]
        stages = sorted({stage for group in measured for stage in group["by_operation"]})
        results[arm] = {"prefixes": len(rows), "different_games": len({r["game_id"] for r in rows}),
                        "successes": sum(r["outcomes"][arm]["won"] for r in rows),
                        "actions_reviewed": sum(r["outcomes"][arm]["checkpoints_reviewed"] for r in rows),
                        "action_changes_or_abstentions": sum(r["outcomes"][arm]["changed_actions"] for r in rows),
                        "standalone_tokens": token_totals(m["totals"] for m in measured),
                        "tokens_by_operation": {s: token_totals(m["by_operation"][s] for m in measured
                                                                if s in m["by_operation"]) for s in stages}}
    contrasts = {}
    for reference, treatment in itertools.combinations([a for a in ARMS if a in all_arms], 2):
        counts = Counter(dict.fromkeys(("rescued", "lost", "both_won", "both_failed"), 0))
        win_games, loss_games = set(), set()
        costs_a, costs_b = [], []
        for r in pairs:
            o = r["outcomes"]
            if reference not in o or treatment not in o:
                continue
            a, b = o[reference]["won"], o[treatment]["won"]
            costs_a.append(o[reference]["token_usage"]["totals"])
            costs_b.append(o[treatment]["token_usage"]["totals"])
            counts["both_won" if a and b else "lost" if a else "rescued" if b else "both_failed"] += 1
            if a != b:
                (win_games if b else loss_games).add(r["game_id"])
        totals_a, totals_b = token_totals(costs_a), token_totals(costs_b)
        ta, tb = totals_a["total_tokens"], totals_b["total_tokens"]
        contrasts[f"{treatment}_vs_{reference}"] = {**counts, "paired_prefixes": sum(counts.values()),
                "standalone_tokens_on_matched_units": {reference: totals_a, treatment: totals_b},
                "extra_total_tokens": tb - ta if costs_a and ta is not None and tb is not None else None,
                "games_with_a_rescue": sorted(win_games), "games_with_a_loss": sorted(loss_games)}
    physical = []
    for (scope, role), count in sorted(usage.items()):
        record = dict(count)
        record["reported_usd"] = round(record["reported_usd"], 8) if record["cost_reports"] else None
        for side in ("input", "output", "total"):
            record[f"observed_{side}_tokens"] = record[f"{side}_tokens"] if record[f"{side}_reports"] else None
            if not record[f"{side}_reports"] or record[f"{side}_reports"] != record["attempts"]:
                record[f"{side}_tokens"] = None
        record["seconds"] = round(record["seconds"], 2)
        physical.append({"scope": scope, "model_role": role, **record})
    slots = ("episode_start",) if design == "episode" else SLOTS
    summary = {"design": design, "paired_unit": "whole game" if design == "episode" else "selected prefix",
               "games_planned": len(games), "natural_games_finished": len(natural),
               "natural_games_won": sum(r["won"] for r in natural), "prefixes_selected": len(pairs),
               "missing_slots_among_finished_games": {s: sum(s not in r["selected"] for r in natural) for s in slots},
               "results": results, "paired_contrasts": contrasts, "physical_api_usage": physical,
               "natural_games": natural, "paired_samples": pairs}
    summary["requested_arms_complete"] = (len(natural) == len(games) and
                all(results[a]["prefixes"] == len(pairs) for a in requested))
    save(out / "summary.json", summary)
    return summary


def manifest(split):
    rows = load(GAMES)["games"]
    if split.name != "valid_seen" or len(rows) != 12 or len({r["game"] for r in rows}) != 12:
        raise ValueError("Use the valid_seen directory containing the twelve pilot games.")
    result = []
    for i, r in enumerate(rows, 1):
        path = split / r["game"]
        if not path.is_file():
            raise ValueError(f"Missing pilot game: {path}")
        result.append({"id": f"game{i:02}", "game": r["game"], "family": r["family"],
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def select_route(out, actor, game, routes=("deepinfra", "siliconflow", "parasail", "darkbloom", "together")):
    """Use one tested provider for both arms; preflight usage is recorded outside the evaluation."""
    path = out / "routing.json"
    report = load(path) if path.exists() else {"selected": None, "checks": []}
    if report["selected"]:
        if report["selected"] not in routes:
            raise ValueError("Saved route differs from the requested provider.")
        return report["selected"]
    env = Episode(game)
    try:
        cp = public_checkpoint(env.reset(), "")
    finally:
        env.close()
    actor.retry_incomplete = False
    for route in routes:
        actor.openrouter_route = route
        start = len(actor.calls)
        try:
            actor.action(cp)
            actor.choice({"record": cp["history"][0]}, "Does this record describe the initial room?",
                         {"yes": "Yes.", "no": "No.", "unknown": "Insufficient evidence."})
            calls = actor.calls[start:]
            if any(c.get("upstream_provider", "").replace(" ", "").casefold() != route for c in calls):
                raise ProviderError("Reply did not confirm the pinned provider.")
            if any(any(c.get(k) is None for k in ("input_tokens", "output_tokens", "total_tokens")) for c in calls):
                raise ProviderError("Provider omitted token usage.")
            if any(c.get("reasoning_tokens", 0) > 0 or c.get("returned_reasoning") for c in calls):
                raise ProviderError("Reasoning present despite explicit disable.")
            report["selected"] = route
            error = None
        except ProviderError as exc:
            error = str(exc)
        report["checks"].append({"route": route, "error": error, "calls": actor.calls[start:]})
        save(path, report)
        if report["selected"]:
            return route
        if error in ("Provider returned HTTP 401.", "Provider returned HTTP 402."):
            raise ProviderError(error)
    raise ProviderError(f"No provider passed the action and choice checks. See {path}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--split-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--provider", choices=("openrouter", "vllm"), default="openrouter")
    p.add_argument("--arms", nargs="+", choices=ARMS, default=list(TWO_ARMS))
    p.add_argument("--design", choices=("episode", "prefix"),
                   help="episode checks every eligible action; prefix checks just the selected fork")
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--max-steps", type=int, default=50)
    args = p.parse_args()
    if args.max_steps < 1 or args.workers < 1:
        p.error("workers and max-steps must be positive")
    arms = tuple(dict.fromkeys(args.arms))
    design = args.design or ("episode" if set(arms) <= set(TWO_ARMS) else "prefix")
    split, out = args.split_dir.resolve(), args.out.resolve()
    games = manifest(split)
    examples = load(EXAMPLES)
    for game in games:
        example = examples["examples"][game["family"]]
        game.update(action_example_id=example["id"], action_example_sha256=digest(example))
    if args.provider == "openrouter" and not os.getenv("OPENROUTER_API_KEY") and sys.stdin.isatty():
        os.environ["OPENROUTER_API_KEY"] = getpass("OpenRouter API key (hidden): ").strip()
    actor = resources(args.provider)
    jev_model = os.getenv("JEV_MODEL", "jev-1.14.0")
    has_jev = any(a.startswith("jev_") for a in arms)
    if has_jev:
        NativeJev(jev_model)
    out.mkdir(parents=True, exist_ok=True)
    with (out / ".run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError(f"Another process is using {out}") from None
        route = None
        freeze(out / "one_shot_examples.json", examples)
        if args.provider == "openrouter":
            actor.action_example = examples["examples"][games[0]["family"]]
            route = select_route(out, actor, split / games[0]["game"], routes=ROUTES)
            os.environ["ALFWORLD_SELECTED_ROUTE"] = route
            print(f"Using OpenRouter provider {route} for all arms.", flush=True)
        freeze(out / "protocol.json", {"format": 2, "games": games, "design": design,
                "prefix_slots": ["episode_start"] if design == "episode" else list(SLOTS),
                "max_steps": args.max_steps, "actor_model": actor.model, "endpoint": actor.endpoint,
                "openrouter_provider": route,
                "demonstrations": {"per_family": 1, "scope": "main actor, both arms, every proposal",
                                   "source": examples["source"], "bank_sha256": digest(examples)},
                "thinking_requested": False, "temperature": 0, "revisions_per_checked_action": 1,
                "read_only_queries_per_checked_action": int(design == "episode"),
                "max_risks_per_action": 3, "llm_eda_judge": actor.model, "llm_eda_reviewer": actor.model,
                "llm_eda_readout": "complete JSON choice", "admissible_list": False,
                "source_sha256": {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest()
                    for n in ("paired.py", "paired_store.py", "alf_env.py", "models.py", "providers.py", "audit.py", "pilot.py")},
                "alfworld": version("alfworld"), "textworld": version("textworld")})
        if has_jev:
            freeze(out / "jev_protocol.json", {"model": jev_model, "api": "TypeSafe native Choice", "max_risks": 3})
        jobs = [(out, split, g, arms, args.provider, args.max_steps, jev_model, design) for g in games]
        try:
            if args.workers == 1:
                unresolved = []
                # Complete the other games before retrying a previously interrupted game.
                # This ordering does not change any case inputs or labels.
                def previous_failure(job):
                    db = out / job[2]["id"] / "calls.sqlite"
                    if len(arms) != 1 or not db.exists():
                        return False
                    with sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True) as conn:
                        return bool(conn.execute("SELECT 1 FROM requests WHERE ok=0 AND scope=? LIMIT 1", arms).fetchone())
                for job in sorted(jobs, key=previous_failure):
                    try:
                        run_game(job)
                    except ProviderError as exc:
                        if "HTTP 40" in str(exc) or "HTTP 429" in str(exc):
                            raise
                        unresolved.append(job[2]["id"])
                        print(f"{job[2]['id']}: incomplete model reply ({exc}); kept pending.", flush=True)
                    summarize(out, games, arms, design)
                if unresolved:
                    raise ProviderError("Unfinished games: " + ", ".join(unresolved))
            else:
                with ProcessPoolExecutor(max_workers=min(len(jobs), args.workers)) as pool:
                    iterator = iter(jobs)
                    pending = {pool.submit(run_game, j) for j in itertools.islice(iterator, args.workers)}
                    while pending:
                        finished, pending = wait(pending, return_when=FIRST_COMPLETED)
                        for future in finished:
                            future.result()
                        summarize(out, games, arms, design)
                        pending.update(pool.submit(run_game, j) for j in itertools.islice(iterator, len(finished)))
        finally:
            summary = summarize(out, games, arms, design)
            if arms == ("direct",) and summary["requested_arms_complete"]:
                save(out / "baseline.summary.json", summary)
        print(f"Finished {summary['natural_games_finished']}/{len(games)} games; "
              f"{summary['prefixes_selected']} paired units. See {out / 'summary.json'}", flush=True)
        if design == "episode":
            for arm in arms:
                result = summary["results"][arm]
                tokens = result["standalone_tokens"]
                print(f"{arm}: {result['successes']}/{result['different_games']} games won | "
                      f"input {tokens['input_tokens']}, output {tokens['output_tokens']}, "
                      f"total {tokens['total_tokens']} tokens", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ProviderError) as error:
        sys.exit(str(error))
