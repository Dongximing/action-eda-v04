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

More games (baseline + D1 on unused valid_seen games of the same three families):

  ~/state-audit-pilot/.venv/bin/python scripts/run_online.py \\
      --src ~/Documents/Codex/2026-11-21/yo/outputs/alfworld-9b-oneshot-alternate --out runs/online/more \\
      --new-per-family 8

Results: <out>/gameXX/d1.json per game, <out>/summary.json and summary.md (wins of
D1 vs the baseline's natural.json on the same games).

Control arms (--arm), run into the same --out folders; same actor, cache, games and budget:
  t0    the same block / revise loop, but the preconditions are decided by the rule
        tracker (aeda.alfworld.replay) instead of the LLM judge. No judge calls. Feedback
        names the record that last set the location / the hand. Answers whether the LLM
        judgment adds anything over rules on ALFWorld.
  hint  no check, nothing is blocked. Every failed step ("Nothing happens ...") is shown to
        the agent with HINT appended (the real environment history is unchanged).
        Answers whether a cheap failure reminder does the same job as blocking.
  mw    model-written conditions: before a checked command (the baseline's CHECK_VERBS: take,
        move, clean, heat, cool, open, close, use, slice ...), the agent model writes up to
        --mw-k conditions with the baseline's own models.GPUChat.risks() (cached like every
        actor call); D1 then verifies each free-text condition against the history (the judge
        sees only the text; the examples are shown in the same yes/no form). Same block / revise
        loop. Conditions that happen to be location / hand conditions are also scored by the
        tracker; every blocked proposal is replayed in a fresh env to see if it would have run.
  h1    same fixed conditions and loop as d1, judged by H1: the whole visible history in one
        multiple-choice question per condition (same model, examples and question form as d1).
  llm   same fixed conditions and loop, judged by the agent model reasoning freely over the whole
        visible history (one JSON call per check: reasoning, true / false / unknown, cited record).
        Generic instruction (LLM_JUDGE), no examples; "holding nothing" keeps the default rule.
  loop  no judge, no conditions, no task knowledge: a command is blocked when it was already run
        and nothing new has been observed since its last run (every later observation repeats an
        earlier one, or is "Nothing happens"; see loop_check). The agent gets the same revise call.
        Targets the repetition loops that end most lost games (scripts/analyze_losses.py).
  llmloop  loop first; a command that is not a blocked repeat then goes through the llm arm's check.
  explore  no check, nothing blocked. After the latest observation the agent sees the places listed in
        the opening observation r0 that it has not visited yet (and those it has), computed from the
        history only (explored). Lost games mostly visit 2-5 of ~40 places (analyze_losses.py).
  selfexplore  the same note as explore, but the visited / not-visited lists are written each step by the
        agent model itself from the history (SELF_PLACES, one extra call per step, cached). The code
        lists are logged beside it in "place_lists" for scoring only.
  onecall  ablation of selfexplore: no note and no extra call. The agent's own action call asks for the same
        two lists before the action (ONECALL_ACTION = the baseline prompt + the SELF_PLACES bookkeeping;
        answer {"visited", "not_visited", "action"}). The lists are logged and scored, never shown.
  onecall_use  onecall with one sentence changed: "Then propose the command." becomes "Then, based on these
        two lists, propose the command." (ONECALL_USE_ACTION). Nothing else differs.
Each arm writes <out>/<id>/<arm>.json and <out>/summary[_<arm>].{json,md}; d1 keeps summary.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
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
DEFAULT_SPLIT = ROOT / "data/alfworld/json_2.1.1/valid_seen"  # copy of ALFWorld json_2.1.1 valid_seen


# ---------------------------------------------------------------- checking and disposition (no env, testable)

@dataclass
class Check:
    status: str      # CONTRADICTED / UNKNOWN / SUPPORTED / NONE (not checked) / EMPTY (checked, no conditions)
    claims: list = field(default_factory=list)
    calls: int = 0
    error: str | None = None

    def as_dict(self):
        d = {"status": self.status, "claims": self.claims, "calls": self.calls}
        if self.error:
            d["error"] = self.error
        return d


def _status(claims: list[dict]) -> str:
    verdicts = {c["verdict"] for c in claims}
    return ("CONTRADICTED" if "CONTRADICTED" in verdicts else "UNKNOWN" if "UNKNOWN" in verdicts
            else "SUPPORTED")


def check_action(view: dict, action: str, episode_id: str, backend, cfg: Config, method: str = "D1") -> Check:
    hist = view["history"]
    steps = [(h["action"], h["observation"]) for h in hist[1:]]
    sd = A.build_sample(episode_id, view["task"], hist[0]["observation"], steps, len(steps), action)
    if sd is None:
        return Check("NONE")
    rows = run([Sample.from_dict(sd)], [method], backend, cfg)
    errors = [r["error"] for r in rows if "error" in r]
    if errors:
        raise RuntimeError(f"{method} failed on {sd['sid']}: {errors[0]}")
    text = {c["cid"]: c["text"] for c in sd["claims"]}
    claims = [{"claim": text[r["cid"]], "verdict": r["verdict"],
               "evidence_records": [f"r{rid}" for rid in r["evidence"]]} for r in rows]
    verdicts = {c["verdict"] for c in claims}
    status = ("CONTRADICTED" if "CONTRADICTED" in verdicts else "UNKNOWN" if "UNKNOWN" in verdicts
              else "SUPPORTED")
    return Check(status, claims, sum(r["calls"] for r in rows))


HINT = ("[Hint: that command had no effect. Before trying it again, make sure you are at the "
        "right place and holding the right object.]")


def tracker_check(view: dict, action: str) -> Check:
    """Control t0: the fixed preconditions decided by the rule tracker on the visible history.
    Evidence = the record that last set the location (at) / the hand (holding, hand_empty), r0 if none."""
    hist = view["history"]
    steps = [(h["action"], h["observation"]) for h in hist[1:]]
    pres = A.preconditions(action)
    if not pres:
        return Check("NONE")
    st = A.replay(steps)
    last = {"loc": 0, "hand": 0}
    for i, (a, o) in enumerate(steps, 1):
        if A.succeeded(o):
            name = A.parse_action(a)[0]
            if name == "goto":
                last["loc"] = i
            elif name in ("take", "put"):
                last["hand"] = i
    claims = []
    for p in pres:
        v = A.evaluate_spec(p["spec"], st)
        src = last["loc" if p["spec"]["type"] == "at" else "hand"]
        claims.append({"claim": p["text"], "verdict": v, "evidence_records": [f"r{src}"]})
    verdicts = {c["verdict"] for c in claims}
    status = ("CONTRADICTED" if "CONTRADICTED" in verdicts else "UNKNOWN" if "UNKNOWN" in verdicts
              else "SUPPORTED")
    return Check(status, claims, 0)


def model_check(view: dict, action: str, conditions: list[dict], episode_id: str, backend, cfg: Config) -> Check:
    """Control mw: D1 on model-written conditions ([{"claim", "anchors", ...}] from risks())."""
    if not conditions:
        return Check("EMPTY")
    hist = view["history"]
    steps = [(h["action"], h["observation"]) for h in hist[1:]]
    sd = A.build_model_sample(episode_id, view["task"], hist[0]["observation"], steps, action, conditions)
    rows = run([Sample.from_dict(sd)], ["D1"], backend, cfg)
    errors = [r["error"] for r in rows if "error" in r]
    if errors:
        raise RuntimeError(f"D1 failed on {sd['sid']}: {errors[0]}")
    st = A.replay(steps)
    text = {c["cid"]: c["text"] for c in sd["claims"]}
    claims = []
    for r in rows:
        spec = A.parse_claim(text[r["cid"]])
        claims.append({"claim": text[r["cid"]], "verdict": r["verdict"],
                       "evidence_records": [f"r{rid}" for rid in r["evidence"]],
                       "eval_spec": spec, "tracker": A.evaluate_spec(spec, st) if spec else None})
    return Check(_status(claims), claims, sum(r["calls"] for r in rows))


LLM_JUDGE = (
    "You check whether conditions hold right now, before an agent's proposed command is executed. "
    "Read the whole interaction history: each record is a command the agent tried and the environment's "
    "feedback, oldest first. For each condition, reason briefly about which records establish or overturn it, "
    "letting later records override earlier ones. Then decide: true (the history shows it holds now), "
    "false (the history shows it does not hold now) or unknown (the history does not settle it). "
    "Cite the id of the record your decision rests on. Return only JSON "
    '{"conditions": [{"condition": "...", "reasoning": "...", "verdict": "true|false|unknown", '
    '"record": "r<id> or null"}]} with one entry per condition, in the order given.'
)
_LLM_VERDICT = {"true": "SUPPORTED", "false": "CONTRADICTED", "unknown": "UNKNOWN"}


def llm_check(view: dict, action: str, ask) -> Check:
    """Control llm: the fixed conditions judged in one free-reasoning call over the whole visible
    history. ask(state) -> parsed JSON answer (the agent model through the cached actor client)."""
    pres = A.preconditions(action)
    if not pres:
        return Check("NONE")
    hist = view["history"]
    state = {"task": view["task"], "proposed_action": action,
             "history": [{k: h[k] for k in ("id", "action", "observation")} for h in hist],
             "conditions": [p["text"] for p in pres]}
    try:
        out = ask(state)
        rows = out["conditions"] if isinstance(out, dict) else None
        if not isinstance(rows, list) or len(rows) != len(pres):
            raise ValueError(f"expected {len(pres)} conditions, got {out!r:.200}")
        claims = []
        for p, r in zip(pres, rows):
            v = _LLM_VERDICT.get(str(r.get("verdict", "")).strip().lower()) if isinstance(r, dict) else None
            if v is None:
                raise ValueError(f"bad verdict {r!r:.120}")
            if v == "UNKNOWN" and p["spec"]["type"] == "hand_empty":
                v = "SUPPORTED_DEFAULT"  # agents start empty-handed: same default rule as D1
            rec = r.get("record")
            claims.append({"claim": p["text"], "verdict": v, "evidence_records": [rec] if isinstance(rec, str) and rec else [],
                           "reasoning": r.get("reasoning")})
    except (ValueError, KeyError, TypeError) as e:  # unusable answer: not blocked, counted
        return Check("UNKNOWN", [{"claim": p["text"], "verdict": "UNKNOWN", "evidence_records": []} for p in pres],
                     1, error=f"{type(e).__name__}: {e}")
    return Check(_status(claims), claims, 1)


def _norm(action: str) -> str:
    return " ".join(action.lower().split())


def loop_check(view: dict, action: str) -> Check:
    """Arm loop: block a command that was already run when nothing new has been observed since.

    Generic, no task knowledge: an observation is new if it is not "Nothing happens" and has not
    appeared earlier in the episode (r0 included). The proposed command is blocked when both hold:
      * it was last run at record r_k and no observation after r_k is new;
      * the situation is the same as when it was run at r_k: the latest record whose command did
        something (not "Nothing happens") is identical (command and observation) then and now.
    Running a command again from the same situation can only give the same result."""
    hist = view["history"]
    a = _norm(action)
    runs = [i for i in range(1, len(hist)) if _norm(hist[i]["action"]) == a]
    if not runs:
        return Check("NONE")
    last = runs[-1]
    seen, new = set(), []
    for h in hist:
        o = h["observation"]
        new.append(A.succeeded(o) and o not in seen)
        seen.add(o)
    if any(new[last + 1:]):
        return Check("NONE")

    def situation(upto):  # the latest record before `upto` whose command did something
        j = next(j for j in range(upto - 1, -1, -1) if j == 0 or A.succeeded(hist[j]["observation"]))
        return _norm(hist[j]["action"]), hist[j]["observation"]
    if situation(last) != situation(len(hist)):  # e.g. it failed at drawer 1, now it has walked there again
        return Check("NONE")
    rid = hist[last]["id"]
    if last == len(hist) - 1:
        claim = (f"You just ran '{action}' at {rid}; running it again now would give the same result.")
    else:
        claim = (f"You already ran '{action}' at {rid} (and {len(runs)} time{'s' if len(runs) > 1 else ''} in all), "
                 f"and nothing new has been observed since {rid}: every later observation repeats an earlier one. "
                 f"Running it again would give the same result.")
    claim += f" Choose a command you have not tried since {rid}."
    return Check("CONTRADICTED", [{"claim": claim, "verdict": "CONTRADICTED", "evidence_records": [rid],
                                   "kind": "repeat", "times_run": len(runs)}], 0)


_PLACE = re.compile(r"\b([a-z]+ \d+)\b")


def places(history: list[dict]) -> tuple[list[str], list[str]]:
    """(places listed in the opening observation r0, places visited so far), both from the history only.
    Visited = a command whose observation starts "You arrive at <place>"."""
    start = history[0]["observation"].lower().split("your task is to")[0]
    listed = list(dict.fromkeys(_PLACE.findall(start)))
    visited = []
    for h in history[1:]:
        m = re.match(r"you arrive at ([a-z]+ \d+)", h["observation"].strip().lower())
        if m and m.group(1) not in visited:
            visited.append(m.group(1))
    return listed, visited


def explored(view: dict) -> dict:
    """Arm explore: the agent's copy of the view, with the latest observation followed by the places from
    the opening observation it has not visited yet (env history unchanged; earlier records unchanged)."""
    listed, visited = places(view["history"])
    left = [p for p in listed if p not in visited]
    return with_note(view, place_note(left, visited))


def place_note(left: list[str], visited: list[str]) -> str:
    """The same note text for explore (code-derived lists) and selfexplore (model-derived lists)."""
    return (f" [Not visited yet ({len(left)} of {len(left) + len(visited)} places listed at the start): "
            f"{', '.join(left) if left else 'none'}. Visited: {', '.join(visited) if visited else 'none'}.]")


def with_note(view: dict, note: str) -> dict:
    hist = [dict(h) for h in view["history"]]
    hist[-1]["observation"] = hist[-1]["observation"] + note
    return {**view, "history": hist, "observation": hist[-1]["observation"]}


SELF_PLACES = (
    "Read the interaction history: each record is a command and the environment's feedback, oldest first; "
    "record r0 is the opening observation. List every place named in the opening observation r0, split into "
    "two groups: visited (the agent has arrived there in a later record) and not_visited (it has not). "
    "Use the exact names as written in r0, keep the order of r0, and put each place in exactly one group. "
    'Return only JSON {"visited": ["..."], "not_visited": ["..."]}.'
)


def parse_places(answer: object) -> tuple[list[str], list[str]]:
    if not isinstance(answer, dict):
        raise ValueError("place list must be a JSON object")
    out = []
    for key in ("visited", "not_visited"):
        v = answer.get(key)
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise ValueError(f"place list needs a list of strings under {key!r}")
        out.append(list(dict.fromkeys(" ".join(x.lower().split()) for x in v if x.strip())))
    visited, left = out
    return [p for p in left if p not in visited], visited


def self_explored(view: dict, ask, log: list) -> dict:
    """Arm selfexplore: the same note as explore, but the two lists are written by the agent model itself
    from the visible history (ask(state) -> JSON). The code-derived lists are logged next to it for
    scoring only. An unusable answer -> no note at this step (counted)."""
    hist = [{k: h[k] for k in ("id", "action", "observation")} for h in view["history"]]
    listed, visited = places(view["history"])
    entry = {"step": len(hist) - 1, "code_visited": visited, "code_not_visited": [p for p in listed if p not in visited]}
    try:
        left, vis = parse_places(ask({"history": hist}))
    except ValueError as e:
        entry["error"] = str(e)
        log.append(entry)
        return view
    entry.update(model_visited=vis, model_not_visited=left)
    log.append(entry)
    return with_note(view, place_note(left, vis))


# Arm onecall: the baseline's action prompt, word for word, except that the same bookkeeping as SELF_PLACES
# is asked inside the agent's own call, before the action, and the answer gains the two lists.
BASE_ACTION = (
    "You are the main agent in the ALFWorld text game. Based on the task, observations, commands "
    "already attempted and the public action guide, propose the next single ALFWorld command. "
    "Use the exact public entity IDs. ")
ONECALL_ACTION = BASE_ACTION + (
    "Before choosing the command, read the interaction history: each record is a command and the "
    "environment's feedback, oldest first; record r0 is the opening observation. List every place named in "
    "the opening observation r0, split into two groups: visited (the agent has arrived there in a later "
    "record) and not_visited (it has not). Use the exact names as written in r0, keep the order of r0, and "
    "put each place in exactly one group. Then propose the command. "
    'Return only a JSON object {"visited": ["..."], "not_visited": ["..."], "action": "..."} without explanation.')
# Arm onecall_use: the only change is that the action must be based on the two lists just written.
ONECALL_USE_ACTION = ONECALL_ACTION.replace("Then propose the command.",
                                            "Then, based on these two lists, propose the command.")
DEMO_TEXT = ("\n\nWorked example from a different game in this task family. "
             "Use it as an example of the procedure. The next user message contains the current "
             "task, entities and observations.\n<example>\n{text}\n</example>")


def onecall_prompt(example: dict | None, use: bool = False) -> str:
    return (ONECALL_USE_ACTION if use else ONECALL_ACTION) + (DEMO_TEXT.format(text=example["text"]) if example is not None else "")


def onecall_action(actor, cp: dict, example: dict | None, use: bool = False) -> dict:
    """One agent call: the baseline's public state (models.public_checkpoint, without "action") and
    ONECALL_ACTION. Returns the raw JSON answer (cached); the caller reads the action and the lists."""
    from models import public_checkpoint as model_cp
    from providers import ProviderError
    state = model_cp(cp)
    state.pop("action", None)
    result = actor._respond(state, onecall_prompt(example, use), max_tokens=1024)
    if not isinstance(result, dict) or not isinstance(result.get("action"), str):
        raise ProviderError("onecall output must be a JSON object with an action.")
    return result


def onecall_read(view: dict, answer: dict | None, log: list, error: str | None = None) -> str | None:
    """The action from a onecall answer; its lists are scored against the code lists (not shown anywhere).
    answer None (the call failed, e.g. the lists ran past the output limit): logged with `error`, returns None."""
    from models import command
    listed, visited = places(view["history"])
    entry = {"step": len(view["history"]) - 1, "code_visited": visited,
             "code_not_visited": [p for p in listed if p not in visited]}
    if answer is None:
        entry.update(error=error or "no answer", fallback="baseline action call")
        log.append(entry)
        return None
    try:
        left, vis = parse_places(answer)
        entry.update(model_visited=vis, model_not_visited=left)
    except ValueError as e:
        entry["error"] = str(e)
    log.append(entry)
    return command(answer["action"])


def hinted(view: dict) -> dict:
    """Control hint: the agent's copy of the view, with HINT after every failed step's observation."""
    hist = [dict(h) for h in view["history"]]
    for h in hist[1:]:
        if not A.succeeded(h["observation"]):
            h["observation"] = f"{h['observation']} {HINT}"
    return {**view, "history": hist, "observation": hist[-1]["observation"]}


def feedback(chk: Check, rejected: list[str] | None = None) -> dict:
    """What the agent sees when blocked: the failed conditions and the records behind them.
    From the second revision of one step on, also every command already rejected at this step
    (with --max-revisions 1 this never happens, so the feedback of earlier runs is unchanged)."""
    fb = {"status": "CONTRADICTED",
          "conditions": [{"claim": c["claim"], "status": c["verdict"], "source_id": (c["evidence_records"] or [None])[0]}
                         for c in chk.claims if c["verdict"] == "CONTRADICTED"]}
    if rejected and len(rejected) > 1:
        fb["rejected_at_this_step"] = list(rejected)
    return fb


def decide(view: dict, proposal: str, check, revise, max_revisions: int) -> tuple[str, dict | None]:
    """check(action) -> Check; revise(action, feedback) -> new action. Returns (action to execute, record)."""
    chk = check(proposal)
    if chk.status != "CONTRADICTED":
        return proposal, {"proposal": proposal, "check": chk.as_dict(), "blocked": False} if chk.status != "NONE" else None
    rec = {"proposal": proposal, "check": chk.as_dict(), "blocked": True, "revisions": []}
    cand, rejected = proposal, [proposal]
    for _ in range(max_revisions):
        new = revise(cand, feedback(chk, rejected))
        if new == cand:  # the agent keeps its action
            rec["revisions"].append({"action": new, "same_as_before": True})
            break
        cand = new
        chk = check(cand)
        rec["revisions"].append({"action": cand, "check": chk.as_dict()})
        if chk.status != "CONTRADICTED":
            break
        if cand not in rejected:
            rejected.append(cand)
    rec["executed"] = cand
    rec["executed_status"] = chk.status
    rec["executed_despite_contradiction"] = chk.status == "CONTRADICTED"
    return cand, rec


# ---------------------------------------------------------------- one game (needs alfworld + the runner modules)

def _episode(job, arm, env, book, actor, example, check=None, show=None, propose=None):
    """One episode. arm "direct": execute every proposal (the baseline). "d1"/"t0": check first.
    show(view) -> the agent's copy of the view (hinted / explored); the env history is unchanged."""
    from paired_store import digest
    from pilot import public_checkpoint
    view = env.reset()
    decisions = []
    while env.steps < job["max_steps"] and not env.done:
        seen = show(view) if show else view
        cp = public_checkpoint(seen, "")
        proposal = (propose(seen, cp) if propose else
                    book.ask(arm, "qwen", "actor", [cp, digest(example)], actor, lambda: actor.action(cp)))
        step = env.steps
        if check is None:
            chosen, rec = proposal, None
        else:
            def revise(action, fb, view=seen):
                c = public_checkpoint(view, action)
                return book.ask(arm, "qwen", "revise", [c, fb], actor, lambda: actor.revise(c, fb))
            chosen, rec = decide(view, proposal, lambda a, view=view: check(view, a), revise, job["max_revisions"])
        view = env.step(chosen)
        if rec is not None:
            obs = view["history"][-1]["observation"]
            rec.update(step=step, observation=obs, succeeded=A.succeeded(obs))
            decisions.append(rec)
    return view, decisions


def replay_proposal(Episode, game, prefix: list[dict], action: str) -> str | None:
    """The observation the blocked proposal would have produced (prefix replayed in a fresh env)."""
    env = Episode(game)
    try:
        env.reset()
        for h in prefix:
            env.step(h["action"])
        if env.done:
            return None
        return env.step(action)["history"][-1]["observation"]
    finally:
        env.close()



def play(job: dict) -> dict:
    sys.path.insert(0, job["runner"])
    from alf_env import Episode
    from models import GPUChat
    from paired_store import CallBook, digest, load, save
    from aeda.backends import AdapterBackend

    folder = Path(job["out"]) / job["id"]
    out_path = folder / f"{job.get('tag') or job['arm']}.json"
    if out_path.exists():
        return json.loads(out_path.read_text())
    folder.mkdir(parents=True, exist_ok=True)
    src_game = Path(job["src"]) / job["id"]
    has_src_baseline = (src_game / "natural.json").exists()
    if has_src_baseline and not (folder / "calls.sqlite").exists():
        shutil.copy2(src_game / "calls.sqlite", folder / "calls.sqlite")   # actor cache of the baseline, copied

    actor = GPUChat("https://openrouter.ai/api/v1", "qwen/qwen3.5-9b", os.environ["OPENROUTER_API_KEY"], openrouter=True)
    actor.openrouter_route = job["route"]
    example = load(Path(job["src"]) / "one_shot_examples.json")["examples"][job["family"]]
    if digest(example) != job["action_example_sha256"]:
        raise ValueError(f"{job['id']}: demonstration differs from the frozen protocol")
    actor.action_example = example
    book = CallBook(folder / "calls.sqlite")
    game = Path(job["split"]) / job["game"]
    try:
        # baseline: the finished run's natural.json, or run the direct arm here with the same actor and cache
        if has_src_baseline:
            natural = load(src_game / "natural.json")
        elif (folder / "direct.json").exists():
            natural = load(folder / "direct.json")
        else:
            env = Episode(game)
            try:
                t0 = time.time()
                view, _ = _episode(job, "direct", env, book, actor, example)
                natural = {"id": job["id"], "family": job["family"], "game": job["game"], "task": view["task"],
                           "won": env.won, "steps": env.steps, "history": view["history"],
                           "end": "success" if env.won else "environment_end" if env.done else "step_limit",
                           "seconds": round(time.time() - t0, 1)}
            finally:
                env.close()
            save(folder / "direct.json", natural)

        arm = job["arm"]
        backend = AdapterBackend(job["adapter"]) if arm == "d1" else None
        check = None
        if arm == "d1":
            cfg = Config(fewshot=job["fewshot"], record_style=job["record_style"])
            check = lambda v, a: check_action(v, a, job["id"], backend, cfg)  # noqa: E731
        elif arm == "t0":
            check = lambda v, a: tracker_check(v, a)  # noqa: E731
        elif arm == "h1":
            backend = AdapterBackend(job["adapter"])
            cfg = Config(fewshot=job["fewshot"], record_style=job["record_style"])
            check = lambda v, a: check_action(v, a, job["id"], backend, cfg, method="H1")  # noqa: E731
        elif arm == "loop":
            check = lambda v, a: loop_check(v, a)  # noqa: E731
        elif arm in ("llm", "llmloop"):
            from providers import ProviderError as _PE

            def ask(state):
                n = len(state["conditions"])
                try:
                    return book.ask(arm, "qwen", "judge-llm", [state], actor,
                                    lambda: actor._respond(state, LLM_JUDGE, max_tokens=120 + 200 * n))
                except _PE as e:
                    raise ValueError(f"provider: {e}") from None
            if arm == "llm":
                check = lambda v, a: llm_check(v, a, ask)  # noqa: E731
            else:  # repetition first (free); the LLM judge only if the command is not a blocked repeat
                def check(v, a):
                    c = loop_check(v, a)
                    return c if c.status == "CONTRADICTED" else llm_check(v, a, ask)
        elif arm in ("hint", "explore", "selfexplore", "onecall", "onecall_use"):
            check = None
        elif arm == "mw":
            from audit import checkpoint_action
            from pilot import public_checkpoint
            from providers import ProviderError
            backend = AdapterBackend(job["adapter"])
            cfg = Config(fewshot=job["fewshot"], record_style=job["record_style"])
            from models import public_checkpoint as model_cp
            from aeda import conditions as W
            k, writer = job["mw_k"], job["mw_writer"]
            op = "risks" if writer == "risks" else f"conditions-{writer}"  # same cache key as eval_conditions.py

            def check(v, a):
                if not checkpoint_action(a):
                    return Check("NONE")
                cp = public_checkpoint(v, a)
                try:
                    inputs = [cp, k] + ([digest(example)] if writer == "v2demo" else [])
                    conds = book.ask(arm, "qwen", op, inputs, actor, lambda: W.write(actor, cp, writer, k, model_cp))
                except (ProviderError, ValueError) as e:  # no usable conditions: the action is executed, counted
                    return Check("EMPTY", error=f"{op}: {e}")
                return model_check(v, a, conds, job["id"], backend, cfg)
        else:
            raise ValueError(f"unknown arm {arm!r} (d1, t0, hint, mw, h1, llm, loop, llmloop, explore, selfexplore, onecall, onecall_use)")
        show, place_log = {"hint": hinted, "explore": explored}.get(arm), []
        if arm == "selfexplore":
            from providers import ProviderError as _PE2

            def ask_places(state):
                try:
                    return book.ask(arm, "qwen", "judge-places", [state], actor,
                                    lambda: actor._respond(state, SELF_PLACES, max_tokens=900))
                except _PE2 as e:
                    raise ValueError(f"provider: {e}") from None
            show = lambda v: self_explored(v, ask_places, place_log)  # noqa: E731
        propose = None
        if arm in ("onecall", "onecall_use"):
            use, op = arm == "onecall_use", "actor-" + arm.replace("_", "-")
            from providers import ProviderError as _PE3

            def propose(v, cp):
                try:
                    ans = book.ask(arm, "qwen", op, [cp, digest(example)], actor,
                                   lambda: onecall_action(actor, cp, example, use))
                except _PE3 as e:  # no usable onecall answer: this step uses the baseline's own action call
                    onecall_read(v, None, place_log, f"{type(e).__name__}: {e}")
                    return book.ask(arm, "qwen", "actor", [cp, digest(example)], actor, lambda: actor.action(cp))
                return onecall_read(v, ans, place_log)
        env = Episode(game)
        t0, first_request = time.time(), book.last_request_id()
        try:
            view, decisions = _episode(job, arm, env, book, actor, example, check=check,
                                      show=show, propose=propose)
            won, steps, done = env.won, env.steps, env.done
        finally:
            env.close()
        if view["task"] != natural["task"] or view["history"][0] != natural["history"][0]:
            raise ValueError(f"{job['id']}: reset differs from the baseline")
        for d in decisions:  # would the blocked proposal have run? replay the prefix in a fresh env
            if d["blocked"] and "proposal_would_succeed" not in d:
                prefix = view["history"][:d["step"] + 1]
                obs = replay_proposal(Episode, game, prefix[1:], d["proposal"])
                d["proposal_would_succeed"] = None if obs is None else A.succeeded(obs)
                # new information? (not "Nothing happens" and not an observation already in the prefix)
                d["proposal_would_be_new"] = None if obs is None else (
                    A.succeeded(obs) and obs not in {h["observation"] for h in prefix})
        hist = view["history"]
        diverged = next((i for i, (a, b) in enumerate(zip(hist, natural["history"])) if a != b),
                        None if len(hist) == len(natural["history"]) else min(len(hist), len(natural["history"])))
        new_actor = book.db.execute("SELECT COUNT(*) FROM requests WHERE id>? AND reused=0 AND ok=1 "
                                    "AND operation NOT LIKE 'judge-%'", (first_request,)).fetchone()[0]
        llm_judge = dict(zip(("calls", "cache_hits"), book.db.execute(
            "SELECT SUM(reused=0), SUM(reused=1) FROM requests WHERE id>? AND operation LIKE 'judge-%'",
            (first_request,)).fetchone()))
        result = {"id": job["id"], "family": job["family"], "game": job["game"], "task": view["task"], "arm": job.get("tag") or job["arm"],
                  "won": won, "steps": steps, "end": "success" if won else "environment_end" if done else "step_limit",
                  "baseline_won": natural["won"], "baseline_steps": natural["steps"],
                  "baseline_source": "src natural.json" if has_src_baseline else "direct.json (this run)",
                  "diverged_from_baseline_at": diverged, "history": hist, "decisions": decisions, "place_lists": place_log,
                  "hints_shown": sum(not A.succeeded(h["observation"]) for h in hist[1:]) if arm == "hint" else 0,
                  "usage": {"judge": backend.usage.as_dict() if backend else
                            {"calls": llm_judge["calls"] or 0, "cache_hits": llm_judge["cache_hits"] or 0},
                            "new_actor_requests": new_actor,
                            "seconds": round(time.time() - t0, 1)},
                  "config": {k: job[k] for k in ("adapter", "fewshot", "record_style", "max_revisions",
                                                 "max_steps", "route")} if arm in ("d1", "h1") else
                            {k: job[k] for k in ("adapter", "fewshot", "record_style", "max_revisions",
                                                 "max_steps", "route", "mw_k", "mw_writer")} if arm == "mw" else
                            {k: job[k] for k in ("max_revisions", "max_steps", "route")} | (
                                {"hint": HINT} if arm == "hint" else {"note": "unvisited places (explored)"} if arm == "explore" else
                                {"note": "unvisited places written by the agent model (SELF_PLACES)"} if arm == "selfexplore" else
                                {"note": "place lists asked inside the agent's own call (ONECALL_ACTION), nothing shown"} if arm == "onecall" else
                                {"note": "place lists asked inside the agent's own call, action based on them (ONECALL_USE_ACTION), nothing shown"} if arm == "onecall_use" else {"judge": "agent model, LLM_JUDGE"} if arm == "llm"
                                else {"checker": "repetition (loop_check)"} if arm == "loop"
                                else {"checker": "repetition (loop_check), then agent model LLM_JUDGE"} if arm == "llmloop"
                                else {"checker": "aeda.alfworld tracker"})}
        save(out_path, result)
        return result
    finally:
        book.close()


def new_games(split: Path, src_protocol: dict, examples: dict, per_family: int, seed: int,
              exclude: set[str] = frozenset(), id_start: int = 1) -> list[dict]:
    """Unused solvable valid_seen games of the families that have a demonstration, sampled per family.
    `exclude`: games already run elsewhere (e.g. an earlier --new-per-family batch); ids start at new<id_start>."""
    import random
    sys.path.insert(0, str(DEFAULT_RUNNER))
    from paired_store import digest
    used = {g["game"] for g in src_protocol["games"]} | set(exclude)
    pools: dict[str, list[str]] = {f: [] for f in sorted(examples)}
    for p in sorted(split.glob("*/*/game.tw-pddl")):
        fam = p.parent.parent.name.partition("-")[0]
        rel = str(p.relative_to(split))
        if fam in pools and "Sliced" not in p.parent.parent.name and rel not in used \
                and json.loads(p.read_bytes()).get("solvable") is True:
            pools[fam].append(rel)
    games = []
    for fam, pool in pools.items():
        for rel in random.Random(f"{seed}-{fam}").sample(pool, min(per_family, len(pool))):
            games.append({"game": rel, "family": fam, "action_example_sha256": digest(examples[fam])})
    games.sort(key=lambda g: (g["family"], g["game"]))
    for i, g in enumerate(games, id_start):
        g["id"] = f"new{i:02d}"
    return games


# ---------------------------------------------------------------- summary

LABEL = {"d1": "D1", "t0": "T0 (rule tracker)", "hint": "failure hint", "mw": "MW (model-written conditions + D1)",
         "h1": "H1 (whole history, multiple choice)", "llm": "LLM judge (whole history, free reasoning)",
         "mw_v2": "MW-v2 (precondition writer + D1)",
         "loop": "LOOP (block repeats with no new observation)", "llmloop": "LLM judge + LOOP",
         "explore": "EXPLORE (unvisited places shown)", "selfexplore": "SELF-EXPLORE (model lists the places)", "onecall": "ONE-CALL (agent lists places, then acts, same call)", "onecall_use": "ONE-CALL-USE (lists, then an action based on them, same call)", "loop_r3": "LOOP, up to 3 revisions", "llmloop_r3": "LLM judge + LOOP, up to 3 revisions", "mw_v2demo": "MW-v2demo (precondition writer + agent's demo + D1)"}


def place_list_score(log: list[dict]) -> dict:
    """selfexplore: the model's not-visited list against the code list, per step."""
    ok = [e for e in log if "error" not in e]
    return {"place_list_steps": len(log), "place_list_errors": len(log) - len(ok),
            "place_list_exact": sum(set(e["model_not_visited"]) == set(e["code_not_visited"]) for e in ok),
            "place_list_missing": sum(len(set(e["code_not_visited"]) - set(e["model_not_visited"])) for e in ok),
            "place_list_extra": sum(len(set(e["model_not_visited"]) - set(e["code_not_visited"])) for e in ok)}


def summarize(results: list[dict], out: Path, arm: str = "d1") -> dict:
    results = sorted(results, key=lambda r: r["id"])
    rows, tot = [], {"blocked": 0, "revised": 0, "kept": 0, "despite": 0, "false_block": 0}
    for r in results:
        blocks = [d for d in r["decisions"] if d["blocked"]]
        fb = unch = 0
        for d in blocks:  # tracker on the same visible prefix: was any blocked claim actually true?
            steps = [(h["action"], h["observation"]) for h in r["history"][1:d["step"] + 1]]
            st = A.replay(steps)
            specs = {p["text"]: p["spec"] for p in A.preconditions(d["proposal"])}
            bad = [c.get("eval_spec") if "eval_spec" in c else specs.get(c["claim"])
                   for c in d["check"]["claims"] if c["verdict"] == "CONTRADICTED"]
            if not any(sp for sp in bad):
                unch += 1  # only free-text conditions the tracker cannot score
            elif not any(sp and A.evaluate_spec(sp, st) == "CONTRADICTED" for sp in bad):
                fb += 1
        row = {"id": r["id"], "family": r["family"], "baseline_won": r["baseline_won"], "d1_won": r["won"],
               "baseline_steps": r["baseline_steps"], "d1_steps": r["steps"], "checks": len(r["decisions"]),
               "blocked": len(blocks), "revised": sum(any(not v.get("same_as_before") for v in d["revisions"]) for d in blocks),
               "agent_kept_action": sum(any(v.get("same_as_before") for v in d["revisions"]) for d in blocks),
               "executed_despite_contradiction": sum(d["executed_despite_contradiction"] for d in blocks),
               "false_blocks_vs_tracker": fb, "diverged_at": r["diverged_from_baseline_at"],
               "judge_calls": r["usage"]["judge"]["calls"], "new_actor_requests": r["usage"]["new_actor_requests"],
               "hints_shown": r.get("hints_shown", 0), "blocks_tracker_cannot_score": unch,
               "blocked_would_have_run": sum(d.get("proposal_would_succeed") is True for d in blocks),
               "blocked_would_have_failed": sum(d.get("proposal_would_succeed") is False for d in blocks),
               "blocked_would_be_new": sum(d.get("proposal_would_be_new") is True for d in blocks),
               "checks_without_conditions": sum(d["check"]["status"] == "EMPTY" for d in r["decisions"]),
               **place_list_score(r.get("place_lists", []))}
        rows.append(row)
        tot["blocked"] += row["blocked"]
        tot["revised"] += row["revised"]
        tot["kept"] += row["agent_kept_action"]
        tot["despite"] += row["executed_despite_contradiction"]
        tot["false_block"] += fb
    for key in ("blocks_tracker_cannot_score", "blocked_would_have_run", "blocked_would_have_failed",
                "blocked_would_be_new", "checks_without_conditions", "place_list_steps", "place_list_exact",
                "place_list_errors", "place_list_missing", "place_list_extra"):
        tot[key] = sum(r[key] for r in rows)
    s = {"arm": arm, "games": len(rows), "baseline_wins": sum(r["baseline_won"] for r in rows),
         "d1_wins": sum(r["d1_won"] for r in rows),
         "rescued": [r["id"] for r in rows if r["d1_won"] and not r["baseline_won"]],
         "lost": [r["id"] for r in rows if r["baseline_won"] and not r["d1_won"]],
         "totals": tot, "per_game": rows}
    name, lab = ("summary" if arm == "d1" else f"summary_{arm}"), LABEL.get(arm, arm)
    (out / f"{name}.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
    lines = [f"# Online {lab} vs baseline on {s['games']} ALFWorld games", "",
             f"Wins: baseline {s['baseline_wins']}/{s['games']}, {lab} {s['d1_wins']}/{s['games']}. "
             f"Rescued: {', '.join(s['rescued']) or '-'}. Lost: {', '.join(s['lost']) or '-'}.", "",
             f"Blocked {tot['blocked']} proposals; agent revised {tot['revised']}, kept its action {tot['kept']}; "
             f"executed despite contradiction {tot['despite']}; blocks the tracker calls wrong: {tot['false_block']}; "
             f"hints shown {sum(r['hints_shown'] for r in rows)}.", "",
             f"Blocks the tracker cannot score (free-text conditions only): {tot['blocks_tracker_cannot_score']}. "
             f"Blocked proposals replayed in the env: would have run {tot['blocked_would_have_run']}, "
             f"would have failed {tot['blocked_would_have_failed']}; "
             f"would have shown something new {tot['blocked_would_be_new']}. "
             f"Checks where no condition was written: {tot['checks_without_conditions']}.", "",
             *([f"Model-written place lists: {tot['place_list_steps']} steps, not-visited list identical to the code list "
                f"at {tot['place_list_exact']}; unusable answers {tot['place_list_errors']}; code-unvisited places the model "
                f"left out {tot['place_list_missing']}, places it listed that the code does not {tot['place_list_extra']}.", ""]
               if tot["place_list_steps"] else []),
             f"(per-game keys d1_won / d1_steps hold this arm's result: {lab})", "",
             f"| game | family | baseline | {lab} | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['family'].replace('_then_place_in_recep', '')} | "
                     f"{'win' if r['baseline_won'] else '-'} | {'win' if r['d1_won'] else '-'} | "
                     f"{r['baseline_steps']}/{r['d1_steps']} | {r['checks']} | {r['blocked']} | {r['revised']} | "
                     f"{r['agent_kept_action']} | {r['executed_despite_contradiction']} | {r['false_blocks_vs_tracker']} | "
                     f"{r['diverged_at'] if r['diverged_at'] is not None else '-'} |")
    (out / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
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
    ap.add_argument("--mw-k", type=int, default=3, help="mw arm: at most this many model-written conditions")
    ap.add_argument("--mw-writer", default="risks", choices=["risks", "v2", "v2demo"],
                    help="mw arm: condition writer (aeda/conditions.py); arm file is mw.json for risks, mw_<writer>.json otherwise")
    ap.add_argument("--arm", default="d1", choices=["d1", "t0", "hint", "mw", "h1", "llm", "loop", "llmloop", "explore", "selfexplore", "onecall", "onecall_use"],
                    help="d1 = our method; t0 / hint = control arms (see the docstring)")
    ap.add_argument("--new-per-family", type=int, default=0,
                    help="instead of the src games, sample this many unused valid_seen games per family "
                         "(clean/heat/cool); each runs the baseline (direct) first, then D1")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--exclude", default="",
                    help="comma list of protocol.json files of earlier --new-per-family runs; their games are not sampled again")
    ap.add_argument("--id-start", type=int, default=0,
                    help="first new-game number (default: after the highest id in --exclude, else 1)")
    a = ap.parse_args()
    tag = a.arm if a.arm != "mw" or a.mw_writer == "risks" else f"mw_{a.mw_writer}"
    if a.arm in ("loop", "llmloop") and a.max_revisions != 1:
        tag = f"{a.arm}_r{a.max_revisions}"  # keeps the --max-revisions 1 results (loop.json) apart
    if not os.getenv("OPENROUTER_API_KEY"):
        ap.error("set OPENROUTER_API_KEY in this terminal")
    src = Path(a.src).expanduser()
    protocol = json.loads((src / "protocol.json").read_text())
    if protocol.get("max_steps") != a.max_steps:
        print(f"note: baseline used max_steps={protocol.get('max_steps')}, this run {a.max_steps}", flush=True)
    route = json.loads((src / "routing.json").read_text())["selected"]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.new_per_family:
        examples = json.loads((src / "one_shot_examples.json").read_text())["examples"]
        frozen = out / "protocol.json"
        if frozen.exists():  # resume with the same games
            games = json.loads(frozen.read_text())["games"]
        else:
            prev = [json.loads(Path(x).expanduser().read_text()) for x in a.exclude.split(",") if x]
            excl = {g["game"] for pr in prev for g in pr["games"]}
            start = a.id_start or 1 + max((int(g["id"][3:]) for pr in prev for g in pr["games"]), default=0)
            games = new_games(Path(a.split_dir).expanduser(), protocol, examples, a.new_per_family, a.seed,
                              exclude=excl, id_start=start)
            frozen.write_text(json.dumps({"source_protocol": str(src / "protocol.json"), "seed": a.seed,
                                          "per_family": a.new_per_family, "max_steps": a.max_steps,
                                          "excluded_from": [x for x in a.exclude.split(",") if x],
                                          "games": games}, indent=1))
        print(f"{len(games)} new games -> {frozen}", flush=True)
    elif (out / "protocol.json").exists():  # a finished --new-per-family batch: same games (e.g. control arms)
        games = json.loads((out / "protocol.json").read_text())["games"]
        print(f"{len(games)} games from {out / 'protocol.json'}", flush=True)
    else:
        games = protocol["games"]
    want = {g for g in a.games.split(",") if g}
    games = [g for g in games if not want or g["id"] in want]
    (out / "run_config.json").write_text(json.dumps({**vars(a), "route": route, "baseline_protocol": str(src / "protocol.json")}, indent=1))
    jobs = [{"id": g["id"], "game": g["game"], "family": g["family"], "action_example_sha256": g["action_example_sha256"],
             "src": str(src), "out": str(out), "runner": str(Path(a.runner).expanduser()), "split": str(Path(a.split_dir).expanduser()),
             "route": route, "adapter": a.adapter, "fewshot": a.fewshot, "record_style": a.record_style,
             "max_revisions": a.max_revisions, "max_steps": a.max_steps, "arm": a.arm, "tag": tag, "mw_k": a.mw_k,
             "mw_writer": a.mw_writer}
            for g in games]
    results, failed = [], []
    sys.path.insert(0, jobs[0]["runner"] if jobs else str(DEFAULT_RUNNER))  # so worker errors (providers.*) unpickle here
    with ProcessPoolExecutor(max_workers=max(1, a.workers)) as ex:
        futs = {ex.submit(play, j): j["id"] for j in jobs}
        for f in as_completed(futs):
            gid = futs[f]
            try:
                r = f.result()
                results.append(r)
                print(f"{gid}: {a.arm} {'WIN' if r['won'] else r['end']} in {r['steps']} steps "
                      f"(baseline {'win' if r['baseline_won'] else 'loss'} in {r['baseline_steps']}), "
                      f"{sum(d['blocked'] for d in r['decisions'])} blocked", flush=True)
            except Exception as e:  # report and keep the other games; rerun resumes finished games from disk
                failed.append(gid)
                cause = f" (cause: {str(e.__cause__).strip().splitlines()[-1]})" if e.__cause__ else ""
                print(f"{gid}: FAILED {type(e).__name__}: {e}{cause}", flush=True)
    s = summarize(results, out, tag)
    md = out / ("summary.md" if tag == "d1" else f"summary_{tag}.md")
    print(f"\nbaseline {s['baseline_wins']}/{s['games']}  {LABEL[tag]} {s['d1_wins']}/{s['games']}  -> {md}")
    if failed:
        print(f"failed games (rerun the same command to resume): {', '.join(sorted(failed))}")
        sys.exit(2)


if __name__ == "__main__":
    main()
