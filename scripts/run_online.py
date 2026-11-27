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
      --out runs/online/d1

More games (baseline + D1 on unused valid_seen games of the same three families):

  ~/state-audit-pilot/.venv/bin/python scripts/run_online.py \\
      --out runs/online/more \\
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
  jevexplore  the same note as selfexplore, but the lists are kept by a decision model (OneJev / Jev, System
        One API at --jev-url) one record at a time: for each new record (command + feedback) it answers one
        choice question, which of the places it arrived at (or none); the answers are accumulated. The place
        names are the agent model's own SELF_PLACES answer on r0 alone (one call per game, the same request
        as selfexplore's first step). The code lists are logged beside it for scoring only.
  jevexplore_name  jevexplore plus a name check before "take": a command taking an object whose name (without its
        number) is not a word of the task text is blocked, and the agent gets the baseline's revise call with
        the reason (as in the d1 arm, one revision). A fixed rule on names, no model; reported apart.
  jevexplore_hard  jevexplore_name with a hard block: when the agent keeps a blocked take after its revision, the
        take is not run. The environment gets "look" instead (it changes nothing in the world and uses the step),
        and the agent's copy of that record shows its own command with the feedback 'Not run: the task is "...",
        which does not name "<name>".' The environment history keeps the "look".
  think_jev  a thinking agent with our module: each step one call that returns {"thought", "action"} (the
        baseline's action prompt asking for a short thought first; earlier thoughts stay in its history records),
        with ReAct's thought version of the same one-shot demonstration (data/fewshot/react_think_examples.json,
        same games, actions and observations as the baseline's); plus the jevexplore_hard module (OneJev ledger
        note, name check with hard block). Compared with stateact.
  statejev  the baseline agent with the full state kept by the decision model (scripts/state_ledger.py): one
        request per new record with five questions, folded into where the agent is, what it carries and which
        places it has looked inside; the note after the latest observation gives those, the places not looked
        inside yet and the places reached but not looked inside. Plus the name check with hard block.
  think_state  the thinking agent of think_jev with statejev's full state note and the name check (hard block).
  think_copy  think_state, but each step the agent first copies the state note into its answer:
        {"state", "thought", "action"}; earlier copies and thoughts stay in its history records (as StateAct keeps
        its written states). Demonstrations: data/fewshot/react_think_copy_examples.json, the thought demonstrations
        with the notes the decision model writes for them (scripts/make_copy_examples.py; nothing written by hand).
  react_std  the standard ReAct baseline of VBL (arXiv 2610.41564, App. F.3), which follows ReflAct (arXiv 2505.15182,
        App. K.1) and the MPO implementation (github.com/WeiminXiong/MPO): one first user message = the ReflAct ReAct
        instruction + "---" + one example of the task type (MPO's alfworld_icl.json, data/fewshot/mpo) + "---" + the
        task; then alternating turns, the model's "Thought: ...\n Action: ..." or "Action: ...", and "Observation: ...".
        Stop words, temperature 0, 512 output tokens (MPO's default; --react-max-tokens N runs it as react_std_tN,
        e.g. 1536, the top of VBL's 512-1536 executor range: at 512 the 9B model's long thoughts are cut before
        "Action:"), 50 steps; an output without "Action:" uses a step and gets MPO's
        "Error Input" observation. "put X in/on Y" is run as "move X to Y" (this ALFWorld release).
  stateact  the published StateAct agent (Rozanov & Rei, arXiv 2410.02810) on the same games, model, provider
        route, temperature 0 and 50-step budget: its own prompt (two ReAct examples per task type annotated with
        goal / locations visited / current location / current inventory / thought / action, from
        third_party/stateact, scripts/fetch_stateact_prompts.sh), one call per step whose text output carries the
        state, thought and action, the full transcript (earlier outputs included) as context, stop "\n\n", the
        action after the last "action: ", put -> move correction. Not the baseline's prompt or demonstration.
        As their llamp OpenAIChatText sends it: one user message, their prompt + the opening observation + "\n",
        then for each step ">" + the cleaned output + the next observation (with "\n"). Differences from their
        code: the 50-step budget instead of their 100-call cap, no stop after 5 identical outputs, and the
        actor's request settings (OpenRouter route, reasoning off, max_tokens 512).
  stateact_chat  stateact with the transcript as chat turns instead of one user message: system = their prompt,
        then user = observation, assistant = ">" + cleaned output, alternating. Everything else as stateact. With
        qwen3.5-9b the one-message form leaves the model continuing the prompt's last example (wrong task from step 0).
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

DEFAULT_RUNNER = ROOT / "baseline/runner"      # copy of the baseline agent code (alfworld-action-eda-oneshot-altprovider)
DEFAULT_SRC = ROOT / "baseline/oneshot12"      # copy of the 12-game baseline run (alfworld-9b-oneshot-alternate)
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


def name_check(view: dict, action: str) -> Check:
    """Arm jevexplore_name: "take <name> <n> from ..." is blocked when <name> is not a word of the task text.
    A fixed rule on names only (no list of objects, no model); every other command is not checked."""
    m = re.match(r"take ([a-z]+) \d+\b", _norm(action))
    if not m:
        return Check("NONE")
    name, task = m.group(1), view["task"].strip()
    if name in re.findall(r"[a-z]+", task.lower()):
        return Check("SUPPORTED", claims=[{"claim": f"{name} is named in the task", "verdict": "SUPPORTED",
                                          "evidence_records": [None]}])
    return Check("CONTRADICTED", claims=[{
        "claim": f'The object you are taking ("{name}") is the object the task names. The task is: "{task}", '
                 f'which does not name "{name}".', "verdict": "CONTRADICTED", "evidence_records": [None]}])


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


JEV_ARRIVED_Q = ("The record is a command and the environment's feedback. Which of these places did the agent arrive at "
                 "with this command? Choose none if it did not arrive at any of them.")


class JevPlaces:
    """System One client for the jevexplore arm (OneJev served locally, or TypeSafe Jev). `model` names the
    decision model in the answer cache; `calls` holds the transport log of each request (CallBook reads it)."""

    def __init__(self, url: str, model: str, timeout: float = 600):
        self.url, self.model, self.timeout, self.calls = url, model, timeout, []
        key = (os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY") or "").strip()
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if key and not url.startswith(("http://127.0.0.1", "http://localhost")):
            self.headers["Authorization"] = f"Bearer {key}"

    def ask(self, state: dict, questions: dict) -> dict:
        import urllib.error
        import urllib.request

        payload = {"state": state, "questions": questions}
        if not self.url.startswith(("http://127.0.0.1", "http://localhost")):
            payload["model"] = self.model
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        t = time.time()
        for i in range(6):
            try:
                req = urllib.request.Request(self.url, data=data, headers=self.headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    out = json.load(r)
                self.calls.append({"ok": True, "attempts": i + 1, "seconds": round(time.time() - t, 3),
                                   "input_tokens": (out.get("usage") or {}).get("input_tokens")})
                return out
            except urllib.error.HTTPError as e:
                if e.code not in (408, 429, 500, 502, 503, 504) or i == 5:
                    raise RuntimeError(f"Jev HTTP {e.code} from {self.url}") from None
            except (OSError, json.JSONDecodeError) as e:
                if i == 5:
                    raise RuntimeError(f"cannot reach Jev at {self.url} ({type(e).__name__})") from None
            time.sleep(min(30, 2 ** i))
        raise RuntimeError("unreachable")


def jev_arrived(answer: object, places: list[str]) -> str | None:
    """The chosen place (None for "none"); ValueError when the answer has no usable choice."""
    a = answer.get("answers", {}).get("arrived") if isinstance(answer, dict) else None
    p = a.get("probabilities") if isinstance(a, dict) else None
    labels = places + ["none"]
    if isinstance(p, dict) and p and set(p) <= set(labels):
        c = max(p, key=lambda k: float(p[k]))
    elif isinstance(a, dict) and isinstance(a.get("choice"), str) and a["choice"].strip() in labels:
        c = a["choice"].strip()
    else:
        raise ValueError(f"no usable choice in {str(answer)[:200]}")
    return None if c == "none" else c


def state_explored(view: dict, names: list[str] | None, ask_state, events: dict, log: list, skip=()) -> dict:
    """Arm statejev: the agent's copy of the view with the state note (state_ledger.note). ask_state(record, names)
    -> the decision model's raw answer to the five questions for one record; events (record index -> event) is
    kept across the episode, so each record is asked once. Records in `skip` (blocked commands that were not run,
    jevexplore_hard's veto) are not asked: nothing happened in them. The answer key's state is logged beside it."""
    import state_ledger as L
    hist = view["history"]
    listed, visited = places(hist)
    key = L.fold([{**e, "searched": e["searched"] if e["searched"] in listed else None}
                  for e in (L.code_event(h) for h in hist[1:])])
    entry = {"step": len(hist) - 1, "code_visited": visited, "code_not_visited": [p for p in listed if p not in key["searched"]],
             "code_location": key["location"], "code_carrying": key["carrying"]}
    if not names:
        entry["error"] = "no place names from the agent model"
        log.append(entry)
        return view
    for k in range(1, len(hist)):
        if k not in events and k in skip:
            events[k] = {"arrived": None, "searched": None, "carry": None, "unusable": [], "not_run": True}
        elif k not in events:
            rec = {"action": hist[k]["action"], "observation": hist[k]["observation"]}
            try:
                events[k] = L.read(ask_state(rec, names), rec, names)
            except ValueError as e:
                events[k] = {"arrived": None, "searched": None, "carry": None, "unusable": [str(e)[:80]]}
    st = L.fold([events[k] for k in range(1, len(hist))])
    entry.update(model_visited=st["searched"], model_not_visited=[p for p in names if p not in st["searched"]],
                 model_location=st["location"], model_carrying=st["carrying"],
                 unusable=sum(bool(events[k]["unusable"]) for k in range(1, len(hist))))
    log.append(entry)
    return with_note(view, L.note(st, names))


def jev_explored(view: dict, names: list[str] | None, ask_record, arrived: dict, log: list) -> dict:
    """Arm jevexplore: names = the place names (the agent model's SELF_PLACES answer on r0, None when unusable);
    ask_record(record, names) -> the decision model's raw answer for one record; arrived (record index -> place or
    None) is kept across the steps of the episode, so each record is asked once."""
    hist = view["history"]
    listed, visited = places(hist)
    entry = {"step": len(hist) - 1, "code_visited": visited, "code_not_visited": [p for p in listed if p not in visited]}
    if not names:
        entry["error"] = "no place names from the agent model"
        log.append(entry)
        return view
    errors = 0
    for k in range(1, len(hist)):
        if k not in arrived:
            rec = {"action": hist[k]["action"], "observation": hist[k]["observation"]}
            try:
                arrived[k] = jev_arrived(ask_record(rec, names), names)
            except ValueError:
                arrived[k] = None   # unusable answer: counted as none for this record
                errors += 1
    vis = list(dict.fromkeys(p for k in sorted(arrived) if k < len(hist) and (p := arrived[k])))
    left = [p for p in names if p not in vis]
    entry.update(model_visited=vis, model_not_visited=left, jev_unusable=errors)
    log.append(entry)
    return with_note(view, place_note(left, vis))


# Arm stateact: the published StateAct prompt and loop (see the docstring). Their files are read as data only.
STATEACT_KEYS = ["goal", "locations_visited", "current_location", "current_inventory", "thought", "action"]
STATEACT_DIR = ROOT / "third_party/stateact/prompts"
STATEACT_TYPES = {"pick_and_place": "put", "pick_clean_then_place": "clean", "pick_heat_then_place": "heat",
                  "pick_cool_then_place": "cool", "look_at_obj": "examine", "pick_two_obj": "puttwo"}


def stateact_examples(env_type: str, prompt_ids=(1, 0), keys=STATEACT_KEYS, folder: Path = STATEACT_DIR) -> str:
    """Their return_stringstate_prompt(env_type, prompt_ids, keys_to_use): each example alternates observations and
    JSON states; a state is written as "key with spaces: value" lines in `keys` order (empty -> None, list joined
    by ", "), prefixed with ">"; every block ends with a blank line; examples are joined by a blank line."""
    import ast

    path = folder / f"alfworld_prompts_utils_v4_{env_type}_base.py"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing: run scripts/fetch_stateact_prompts.sh")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {f"{env_type}_v4_base_{i}" for i in prompt_ids}
    data = {t.id: ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
            for t in node.targets if isinstance(t, ast.Name) and t.id in names}
    out = ""
    for n, pid in enumerate(prompt_ids):
        if n:
            out += "\n\n"
        for idx, comp in enumerate(data[f"{env_type}_v4_base_{pid}"]):
            if idx % 2 == 0:
                out += comp + "\n\n"
                continue
            st, lines = json.loads(comp), []
            for k in keys:
                v = st[k]
                v = "None" if not v else ", ".join(v) if isinstance(v, list) else v
                lines.append(f"{k.replace('_', ' ')}: {v}")
            out += ">" + "\n".join(lines) + "\n\n"
    return out


def stateact_system(examples: str, n: int = 2) -> str:
    """Their generate_prompt_from_example(..., return_raw_prompt=True) with empty instructions, marks and hints."""
    base, instructions, mark, hints, task = "Interact with a household to solve a task.", "", "", "", "Here is the task."
    return f"""{base}
{instructions}

Here {'are' if n > 1 else 'is'} {n} example{'s' if n > 1 else ''}:
{mark}
{examples}
{mark}
{hints}
{task}

"""


def stateact_first_observation(obs: str) -> str:
    return "\n".join(obs.split("\n\n")[1:])     # their reset handling: drop the welcome banner


def stateact_observation(obs: str) -> str:
    if obs.startswith("You arrive at loc "):    # their process_ob
        obs = obs[obs.find(". ") + 2:]
    return obs if obs.endswith("\n") else obs + "\n"


def stateact_clean(output: str) -> str:
    """Their general_action_cleaning then our_text_action_cleaning: the output as it goes back into the transcript
    (after a ">" they add) and as the action is read from."""
    out = output
    if out.startswith("> "):
        out = out.replace("> ", "")
    if out.startswith(">"):
        out = out.replace(">", "")
    return out.strip() + "\n\n"


def stateact_action(output: str) -> str:
    """The text after the last "action: " of the cleaned output, the put -> move correction, made into the one-line
    command our environment takes (anything it cannot parse gets "Nothing happens.")."""
    out = stateact_clean(output)
    act = out.split("action: ")[-1] if "action: " in out else out
    act = " ".join(act.split())
    if act.startswith("put"):
        if re.match(r"put(?:\s\w+)(?:\s\w+)?(?:\s\d+)\son(?:\s\w+)(?:\s\w+)?(?:\s\d+)", act):
            act = act.replace(" on ", " in/on ")
        elif re.match(r"put(?:\s\w+)(?:\s\w+)?(?:\s\d+)\sin(?:\s\w+)(?:\s\w+)?(?:\s\d+)", act):
            act = act.replace(" in ", " in/on ")
    act = act.replace("put", "move").replace("in/on", "to")
    return act or "none"


def stateact_visited(output: str) -> list[str] | None:
    m = re.search(r"^locations visited: (.*)$", output, flags=re.M)
    if not m:
        return None
    v = m.group(1).strip()
    return [] if v.lower() == "none" else list(dict.fromkeys(" ".join(x.lower().split()) for x in v.split(",") if x.strip()))


def stateact_call(actor, messages: list[dict], max_tokens: int = 512, stop: list[str] | None = None) -> str:
    """One chat request with the actor's model, route and settings, as text (no JSON mode); stop at a blank line
    unless other stop words are given."""
    from providers import ProviderError

    payload = {"model": actor.model, "messages": messages, "temperature": 0, "max_tokens": max_tokens,
               "stop": stop if stop is not None else ["\n\n"]}
    if actor._chat_template_kwargs is not None:
        payload["chat_template_kwargs"] = actor._chat_template_kwargs
    if actor._openrouter:
        payload["reasoning"] = {"enabled": False}
        payload["provider"] = {"require_parameters": True}
        if actor.openrouter_route:
            payload["provider"].update(only=[actor.openrouter_route], allow_fallbacks=False)
    result = actor.post(payload)
    served = str(result.get("model", "")).lower()
    if actor._openrouter and served != actor.model.lower() and not served.startswith(actor.model.lower() + "-20"):
        raise ProviderError("OpenRouter did not confirm the requested model in the response.")
    try:
        choice = result["choices"][0]
        content, finish = choice["message"].get("content"), choice.get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        raise ProviderError("Chat response lacks an assistant message.") from None
    if finish not in (None, "stop", "length"):
        raise ProviderError(f"Chat response stopped without a usable answer (finish_reason={finish!r}).")
    return content if isinstance(content, str) else ""


# Arm react_std: the standard ReAct baseline (VBL App. F.3 -> ReflAct App. K.1 -> MPO's implementation).
REACT_STD_INSTRUCTION = (
    "Interact with a household to solve a task. Imagine you are an intelligent agent in a household environment and your "
    "target is to perform actions to complete the task goal. At the beginning of your interactions, you will be given the "
    "detailed description of the current environment and your goal to accomplish. \n"
    "For each of your turn, you will be given the observation of the last turn. You should first think about the current "
    "condition and plan for your future actions, and then output your action in this turn. Your output must strictly "
    "follow this format:\"Thought: your thoughts.\\n Action: your next action\". \n"
    "The available actions are:\n1. go to recep\n2. take obj from recep\n3. put obj in/on recep\n4. open recep\n"
    "5. close recep\n6. use obj\n7. clean obj with recep\n8. heat obj with recep\n9. cool obj with recep\n"
    "where obj and recep correspond to objects and receptacles.\n"
    "After your each turn, the environment will give you immediate feedback based on which you plan your next few steps. "
    "if the envrionment output \"Nothing happened\", that means the previous action is invalid and you should try more options.\n"
    "Reminder: \nThe action must be chosen from the given available actions. Any actions except provided available actions "
    "will be regarded as illegal.")
REACT_STD_ICL = ROOT / "data/fewshot/mpo/alfworld_icl.json"
# Control arms for react_dep (docs: same trigger steps and the same message form, only the blamed step differs):
#   react_ptr_none    "This failed."  (content-free)
#   react_ptr_recent  "... The likely cause is your command at step t-1: "<command>"."   (the step just before)
#   react_ptr_random  same form, a step drawn uniformly from 1..t (seeded by game and step)
#   react_ptr_dep     same form, the step where the dependency graph's culprit belief was formed
# No command is blocked in these arms; the dependency graph only decides when to speak (and, for _dep, where to point).
PTR_ARMS = ("react_ptr_none", "react_ptr_recent", "react_ptr_random", "react_ptr_dep")
# The dependency-graph controller itself: react_dep walks one hop back from a failed command (the first runs);
# react_dep_graph walks back through the graph without a limit (scripts/dep_graph.py, DepGraph(hops=None)).
DEP_ARMS = ("react_dep", "react_dep_graph")
REACT_STD_STOP = ["\nObservation:", "\nTask:", "\n---"]          # MPO agents/base.py
REACT_STD_ERROR = "Observation: Error Input. Your input must contains 'Action: '"   # MPO envs/alfworld_env.py


def react_std_prompt(example_turns: list[dict], task_text: str) -> str:
    """MPO prompt/templates.py prompt_with_icl with icl_num 1 and icl_format "first"."""
    examples = ""
    for j, t in enumerate(example_turns):
        examples += t["content"] + ("\n" if j == 0 or j % 2 == 1 else "\n\n")
    return (f"{REACT_STD_INSTRUCTION}\n---\nHere is an example.\n\n{examples}\n---\n\n"
            f"Now, it's your turn and here is the task.\n{task_text}")


def react_std_action(output: str) -> str | None:
    """MPO's parse: the text after the first "Action:" (None when there is none). A placement is run as
    "move X to Y", the command this ALFWorld release takes for "put X in/on Y"."""
    m = re.findall(r"Action:\s?(.*)", output.strip(), re.DOTALL)
    if not m:
        return None
    action = " ".join(m[0].split())
    put = re.match(r"put\s+(.*?)\s+(?:in/on|in|on)\s+(.*)$", action)
    if put:
        action = f"move {put.group(1)} to {put.group(2)}"
    return action or None


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



# Arm think_jev: the baseline's action prompt asking for a short thought before the command.
THINK_ACTION = BASE_ACTION.replace("propose the next single ALFWorld command. ",
                                   "first write a short thought about the situation and what to do next (it may be empty "
                                   "when the next command is obvious), then propose the next single ALFWorld command. ") + (
    'Return only a JSON object {"thought":"...","action":"..."} without explanation.')
THINK_EXAMPLES = ROOT / "data/fewshot/react_think_examples.json"


def think_action(actor, cp: dict, thoughts: dict, example: dict) -> dict:
    """One agent call: the baseline's public state with each earlier record carrying the thought the agent wrote
    for it ({"id", "thought", "action", "observation"}), THINK_ACTION and the thought demonstration."""
    from models import public_checkpoint as model_cp
    from providers import ProviderError
    state = model_cp(cp)
    state.pop("action", None)
    state["history"] = [({"id": r["id"], "thought": thoughts[i], "action": r["action"], "observation": r["observation"]}
                         if i in thoughts else r) for i, r in enumerate(state["history"])]
    result = actor._respond(state, THINK_ACTION + DEMO_TEXT.format(text=example["text"]), max_tokens=512)
    if not isinstance(result, dict) or not isinstance(result.get("action"), str):
        raise ProviderError("think output must be a JSON object with an action.")
    return result



# Arm think_copy: the agent copies the state note, then thinks, then acts (one call).
THINK_COPY_ACTION = BASE_ACTION.replace(
    "propose the next single ALFWorld command. ",
    "first copy the state note that follows the latest observation (where you are, what you carry, the places not "
    "looked inside or on yet, and the places reached but not looked inside or on), then write a short thought about "
    "what to do next, then propose the next single ALFWorld command. ") + (
    'Return only a JSON object {"state":"...","thought":"...","action":"..."} without explanation.')
COPY_EXAMPLES = ROOT / "data/fewshot/react_think_copy_examples.json"


def think_copy_action(actor, cp: dict, written: dict, example: dict) -> dict:
    """One agent call: the baseline's public state with each earlier record carrying what the agent wrote at that
    step ({"id", "state", "thought", "action", "observation"}), THINK_COPY_ACTION and the copy demonstration."""
    from models import public_checkpoint as model_cp
    from providers import ProviderError
    state = model_cp(cp)
    state.pop("action", None)
    state["history"] = [({"id": r["id"], **written[i], "action": r["action"], "observation": r["observation"]}
                         if i in written else r) for i, r in enumerate(state["history"])]
    result = actor._respond(state, THINK_COPY_ACTION + DEMO_TEXT.format(text=example["text"]), max_tokens=1024)
    if not isinstance(result, dict) or not isinstance(result.get("action"), str):
        raise ProviderError("think_copy output must be a JSON object with an action.")
    return result


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

def _episode(job, arm, env, book, actor, example, check=None, show=None, propose=None, veto=None):
    """One episode. arm "direct": execute every proposal (the baseline). "d1"/"t0": check first.
    show(view) -> the agent's copy of the view (hinted / explored); the env history is unchanged.
    veto(command, record) -> None to run the command, or (command to run instead, agent-side record) when a
    blocked command the agent kept must not run (jevexplore_hard); the agent-side record replaces that step's
    record in show()'s input through the overrides veto keeps."""
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
        vetoed = veto(chosen, rec) if veto else None
        if vetoed:
            if rec is not None:
                rec["vetoed"], rec["env_action"] = True, vetoed[0]
            chosen = vetoed[0]
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



_IO_RAW: list = []   # raw provider outputs of fresh chat requests, in order (filled by the wrapped transport)


def _install_io_transport():
    """Wrap the runner's HTTP transport once per process so a fresh chat request's raw output is kept."""
    import providers
    if getattr(providers._Transport.post, "_io_recording", False):
        return
    orig = providers._Transport.post

    def post(self, payload):
        out = orig(self, payload)
        try:
            _IO_RAW.append(out["choices"][0]["message"].get("content"))
        except (KeyError, IndexError, TypeError, AttributeError):
            _IO_RAW.append(None)
        return out
    post._io_recording = True
    post._io_orig = orig
    providers._Transport.post = post


def _render_request(perform, answer) -> dict:
    """The exact request a call makes, rebuilt without the network: perform() runs with the transports replaced by
    stubs that record the payload and give back the answer already obtained (so cached answers are covered too)."""
    import providers
    captured: dict = {}
    saved_post, saved_jev = providers._Transport.post, JevPlaces.ask

    def fake_post(self, payload):
        captured.update(kind="chat", endpoint=getattr(self, "endpoint", None), payload=payload)
        if isinstance(answer, str) and "response_format" in payload:
            content = json.dumps({"action": answer})
        elif isinstance(answer, str):
            content = answer
        else:
            content = json.dumps(answer, ensure_ascii=False)
        return {"model": payload.get("model"), "choices": [{"message": {"content": content}, "finish_reason": "stop"}]}

    def fake_jev(self, state, questions):
        captured.update(kind="system_one", endpoint=self.url, payload={"state": state, "questions": questions})
        return answer
    providers._Transport.post, JevPlaces.ask = fake_post, fake_jev
    try:
        perform()
    except Exception as e:  # noqa: BLE001  (e.g. a call kind this rebuild does not cover)
        captured.setdefault("rebuild_error", f"{type(e).__name__}: {e}")
    finally:
        providers._Transport.post, JevPlaces.ask = saved_post, saved_jev
    return captured


def _attach_io_log(book, log: list, env_box: list) -> None:
    """Every model request of the episode, in order: the environment step it was made at, who was asked and for
    what, whether the answer came from the cache, the exact request, the raw output of a fresh request, and the
    answer the run used."""
    _install_io_transport()
    orig_ask = book.ask

    def ask(scope, role, operation, inputs, client, perform):
        n_answers = book.db.execute("SELECT COUNT(*) FROM answers").fetchone()[0]
        if isinstance(book, FreshBook):
            book.last_fresh = False
        mark = len(_IO_RAW)
        answer = orig_ask(scope, role, operation, inputs, client, perform)
        fresh = book.last_fresh if isinstance(book, FreshBook) else \
            book.db.execute("SELECT COUNT(*) FROM answers").fetchone()[0] != n_answers
        raw = _IO_RAW[mark:] if fresh else None
        log.append({"n": len(log) + 1, "env_step": env_box[0].steps if env_box[0] is not None else None,
                    "phase": env_box[1] if len(env_box) > 1 else None, "role": role, "operation": operation,
                    "from_cache": not fresh, "request": _render_request(perform, answer),
                    "raw_output": (raw[-1] if raw else None) if role != "jev" else (answer if fresh else None),
                    "answer": answer})
        return answer
    book.ask = ask


class FreshBook:
    """CallBook without reuse: every request goes to the model, even when an identical one was answered before.
    Answers are still written to calls.sqlite (as the record of the run), never read back. last_fresh tells the
    I/O log that the answer is new."""

    def __init__(self, path):
        from paired_store import CallBook
        self._book = CallBook(path)
        self.db = self._book.db
        self.last_fresh = False

    def __getattr__(self, name):
        return getattr(self._book, name)

    def ask(self, scope, role, operation, inputs, client, perform):
        from paired_store import canonical, digest
        key = digest([role, client.model, operation, inputs])
        row = (scope, role, operation, key)
        mark = len(client.calls)
        try:
            answer = perform()
        except Exception as error:
            with self.db:
                self.db.execute("INSERT INTO requests VALUES(NULL,?,?,?,?,0,0,?,?)",
                                (*row, canonical(client.calls[mark:]), type(error).__name__))
            raise
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO answers VALUES(?,?)", (key, canonical(answer)))
            self.db.execute("INSERT INTO requests VALUES(NULL,?,?,?,?,0,1,?,NULL)",
                            (*row, canonical(client.calls[mark:])))
        self.last_fresh = True
        return answer


def _write_io_log(folder: Path, tag: str, log: list) -> None:
    import gzip
    if not log:
        return
    with gzip.open(folder / f"{tag}_io.jsonl.gz", "wt", encoding="utf-8") as fh:
        for x in log:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")


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
    # the baseline actor's one-shot demonstration (clean/heat/cool only; None for other task types, which only the
    # arms with their own prompts run: react_std, stateact)
    example = load(Path(job["src"]) / "one_shot_examples.json")["examples"].get(job["family"])
    if job.get("action_example_sha256") is not None and digest(example) != job["action_example_sha256"]:
        raise ValueError(f"{job['id']}: demonstration differs from the frozen protocol")
    actor.action_example = example
    # no answer reuse: every request is sent to the model. Only the offline log tools (replay_io.py, backfill_io.py),
    # which rebuild logs of finished runs from their stored answers and never call a provider, set replay_cache.
    book = CallBook(folder / "calls.sqlite") if job.get("replay_cache") else FreshBook(folder / "calls.sqlite")
    io_log, io_env = [], [None, "baseline"]   # every model request (written to <tag>_io.jsonl.gz)
    _attach_io_log(book, io_log, io_env)
    game = Path(job["split"]) / job["game"]
    try:
        # baseline: the finished run's natural.json, or run the direct arm here with the same actor and cache
        if job.get("no_baseline"):   # --no-baseline: only this arm is played (e.g. react_std on valid_unseen)
            natural = None
        elif has_src_baseline:
            natural = load(src_game / "natural.json")
        elif (folder / "direct.json").exists():
            natural = load(folder / "direct.json")
        else:
            env = Episode(game)
            io_env[0], io_env[1] = env, "baseline (direct)"
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
        elif arm in ("hint", "explore", "selfexplore", "jevexplore", "onecall", "onecall_use", "stateact", "stateact_chat", "react_std", *DEP_ARMS, *PTR_ARMS):
            check = None
        elif arm in ("jevexplore_name", "jevexplore_hard", "think_jev", "statejev", "think_state", "think_copy"):
            check = lambda v, a: name_check(v, a)  # noqa: E731
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
            raise ValueError(f"unknown arm {arm!r} (d1, t0, hint, mw, h1, llm, loop, llmloop, explore, selfexplore, jevexplore, jevexplore_name, jevexplore_hard, think_jev, statejev, think_state, think_copy, onecall, onecall_use, stateact, stateact_chat, react_std, react_dep, react_ptr_*)")
        show, place_log = {"hint": hinted, "explore": explored}.get(arm), []
        think_log: list = []   # think_jev: steps whose thought call was unusable
        vetoed: set = set()    # env record indices whose command was blocked and not run (hard block)
        copies: list = []      # think_copy: per step, whether the agent's copy equals the note
        thoughts: dict = {}    # think_jev: env record index -> the thought the agent wrote for that step
        if arm == "selfexplore":
            from providers import ProviderError as _PE2

            def ask_places(state):
                try:
                    return book.ask(arm, "qwen", "judge-places", [state], actor,
                                    lambda: actor._respond(state, SELF_PLACES, max_tokens=900))
                except _PE2 as e:
                    raise ValueError(f"provider: {e}") from None
            show = lambda v: self_explored(v, ask_places, place_log)  # noqa: E731
        if arm in ("jevexplore", "jevexplore_name", "jevexplore_hard", "think_jev", "statejev", "think_state", "think_copy"):
            from providers import ProviderError as _PE4
            jev = JevPlaces(job["jev_url"], job["jev_model"])
            arrived: dict = {}
            names_box: list = []

            def place_names(v):  # the agent model's own SELF_PLACES answer on r0 alone (same request as selfexplore's first step)
                if not names_box:
                    state = {"history": [{k: v["history"][0][k] for k in ("id", "action", "observation")}]}
                    try:
                        left, vis = parse_places(book.ask(arm, "qwen", "judge-places", [state], actor,
                                                          lambda: actor._respond(state, SELF_PLACES, max_tokens=900)))
                        names_box.append(list(dict.fromkeys(vis + left)) or None)
                    except (_PE4, ValueError):
                        names_box.append(None)
                return names_box[0]

            def ask_record(rec, names):
                crit = {p: p for p in names}
                crit["none"] = "none of these places"
                qs = {"arrived": {"type": "choice", "instructions": JEV_ARRIVED_Q, "criteria": crit}}
                return book.ask(arm, "jev", "judge-jev-arrived", [{"record": rec}, qs], jev,
                                lambda: jev.ask({"record": rec}, qs))
            show = lambda v: jev_explored(v, place_names(v), ask_record, arrived, place_log)  # noqa: E731
            if arm in ("statejev", "think_state", "think_copy"):
                import state_ledger as _L
                events: dict = {}

                def ask_state(rec, names):
                    qs = _L.questions(rec, names)
                    return book.ask(arm, "jev", "judge-jev-state", [{"record": rec}, qs], jev,
                                    lambda: jev.ask({"record": rec}, qs))
                show = lambda v: state_explored(v, place_names(v), ask_state, events, place_log, vetoed)  # noqa: E731
        veto = None
        if arm in ("jevexplore_hard", "think_jev", "statejev", "think_state", "think_copy"):
            overrides: dict = {}   # env record index -> the agent's own command and the not-run feedback
            ledger_show = show

            def with_overrides(v):
                hist = [dict(h, **overrides[i]) if i in overrides else h for i, h in enumerate(v["history"])]
                return {**v, "history": hist, "observation": hist[-1]["observation"]}

            def veto(command, rec):
                if not (rec and rec.get("executed_despite_contradiction")):
                    return None
                last = rec["revisions"][-1] if rec.get("revisions") and "check" in rec["revisions"][-1] else rec
                claim = next(c["claim"] for c in last["check"]["claims"] if c["verdict"] == "CONTRADICTED")
                why = claim.split("The task is: ", 1)[-1]   # '"<task>", which does not name "<name>".'
                overrides[len(state_box[0]["history"])] = {"action": command, "observation": f"Not run: the task is {why}"}
                vetoed.add(len(state_box[0]["history"]))
                return "look", None
            state_box: list = [None]

            def show(v):  # noqa: F811
                state_box[0] = v
                return ledger_show(with_overrides(v))
        propose = None
        if arm in ("think_jev", "think_state"):
            from models import command as _command
            from providers import ProviderError as _PE5
            think_example = json.loads(THINK_EXAMPLES.read_text())["examples"][job["family"]]

            def propose(v, cp):
                idx = len(v["history"])
                try:
                    ans = book.ask(arm, "qwen", "actor-think", [cp, digest(think_example), sorted(thoughts.items())],
                                   actor, lambda: think_action(actor, cp, thoughts, think_example))
                    thoughts[idx] = ans.get("thought") if isinstance(ans.get("thought"), str) else ""
                    return _command(ans["action"])
                except _PE5 as e:   # unusable answer: this step uses the baseline's own action call (logged)
                    thoughts[idx] = ""
                    think_log.append({"step": idx - 1, "error": f"{type(e).__name__}: {e}", "fallback": "baseline action call"})
                    return book.ask(arm, "qwen", "actor", [cp, digest(example)], actor, lambda: actor.action(cp))
        if arm == "think_copy":
            from models import command as _command
            from providers import ProviderError as _PE6
            copy_example = json.loads(COPY_EXAMPLES.read_text())["examples"][job["family"]]
            written: dict = {}     # env record index -> {"state": the agent's copy, "thought": ...}

            def propose(v, cp):
                idx = len(v["history"])
                obs = v["history"][-1]["observation"]
                note = obs[obs.rindex(" [") + 2:-1] if " [" in obs and obs.endswith("]") else None
                try:
                    ans = book.ask(arm, "qwen", "actor-think-copy", [cp, digest(copy_example), sorted(written.items())],
                                   actor, lambda: think_copy_action(actor, cp, written, copy_example))
                    st = ans.get("state") if isinstance(ans.get("state"), str) else ""
                    th = ans.get("thought") if isinstance(ans.get("thought"), str) else ""
                    written[idx] = {"state": st, "thought": th}
                    thoughts[idx] = th
                    copies.append({"step": idx - 1, "copy_equals_note": note is not None and " ".join(st.split()) == " ".join(note.split()),
                                   "copy_chars": len(st), "note_chars": len(note or "")})
                    return _command(ans["action"])
                except _PE6 as e:   # unusable answer: this step uses the baseline's own action call (logged)
                    written[idx] = {"state": "", "thought": ""}
                    thoughts[idx] = ""
                    think_log.append({"step": idx - 1, "error": f"{type(e).__name__}: {e}", "fallback": "baseline action call"})
                    return book.ask(arm, "qwen", "actor", [cp, digest(example)], actor, lambda: actor.action(cp))
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
        if arm in ("react_std", *DEP_ARMS, *PTR_ARMS):
            icl = json.loads(REACT_STD_ICL.read_text())
            icl_key = next(k for k in icl if job["family"].startswith(k))
            outputs: list[str] = []
            errors: set = set()      # env record indices whose output had no "Action:" (a step is used, "look" is run)
            dep = {"graph": None, "done": 0, "notes": {}, "blocked": {}, "hist_len": 1, "pointed": {},
                   "graph_log": []}   # controller state; graph_log: the whole graph after every step

            def pointer_note(i, culprit, hist):   # the control arms: same trigger, same form, only the step differs
                what = culprit["what"]
                if arm == "react_ptr_none":
                    return what
                if arm == "react_ptr_recent":
                    k = max(1, i - 1)
                elif arm == "react_ptr_random":
                    import random as _r
                    k = _r.Random(f"{job['id']}-{i}").randint(1, i)
                else:
                    k = culprit["formed"] if 1 <= culprit["formed"] <= i else i
                dep["pointed"][i] = k
                return f'{what} The likely cause is your command at step {k}: "{hist[k]["action"]}".'

            def dep_catch_up(v):   # feed the controller every record it has not seen: the command run and its feedback
                if dep["graph"] is None:
                    from dep_graph import DepGraph
                    dep["graph"] = DepGraph(v["task"], v["history"][0]["observation"],
                                            hops=None if arm == "react_dep_graph" else 1)
                hist, g = v["history"], dep["graph"]
                for i in range(dep["done"] + 1, len(hist)):
                    g.update(i, hist[i]["action"], hist[i]["observation"])
                    note = g.after(i, hist[i]["action"], hist[i]["observation"],
                                   ran_as_agent=i not in errors and i not in dep["blocked"])
                    if note:
                        dep["notes"][i] = note if arm in DEP_ARMS else pointer_note(i, g.last, hist)
                    dep["graph_log"].append({**g.graph_at(i), "note": dep["notes"].get(i), "blocked": dep["blocked"].get(i)})
                dep["done"] = len(hist) - 1
                dep["hist_len"] = len(hist)

            def shown(i, obs):   # the agent's copy of record i (react_dep: blocked commands and the controller's notes)
                if arm == "react_std":
                    return obs
                if i in dep["blocked"]:
                    told, instead = dep["blocked"][i]
                    obs = told if instead == "look" else f"{told} Ran instead: {instead}. {obs}"
                if i in dep["notes"]:
                    obs = f"{obs}\nCheck: {dep['notes'][i]}"
                return obs

            def propose(v, cp):   # MPO's turns: the prompt, then the model's outputs and "Observation: ..." replies
                hist = v["history"]
                if arm != "react_std":
                    dep_catch_up(v)
                task_text = stateact_first_observation(hist[0]["observation"] + "\n\nYour task is to: " + v["task"])
                msgs = [{"role": "user", "content": react_std_prompt(icl[icl_key][0], task_text)}]
                for i, out in enumerate(outputs):
                    obs = hist[i + 1]["observation"]
                    if obs.startswith("You arrive at loc "):
                        obs = obs[obs.find(". ") + 2:]
                    msgs += [{"role": "assistant", "content": out},
                             {"role": "user", "content": REACT_STD_ERROR if (i + 1) in errors else f"Observation: {shown(i + 1, obs)}"}]
                mt = job.get("react_max_tokens", 512)
                op = "actor-react-std" if mt == 512 else f"actor-react-std-t{mt}"   # own cache entries per output limit
                out = book.ask(arm, "qwen", op, [msgs], actor,
                               lambda: stateact_call(actor, msgs, max_tokens=mt, stop=REACT_STD_STOP))
                outputs.append(out)
                act = react_std_action(out)
                place_log.append({"step": len(hist) - 1, "output": out, "action": act})
                if act is None:
                    errors.add(len(hist))
                    return "look"
                return act
            if arm in DEP_ARMS:
                def veto(command, rec):   # noqa: F811  before a command runs: a ruled-out or refuted dependency stops it
                    i = dep["hist_len"]                   # the record this command will become
                    if i in errors:
                        return None
                    decided = dep["graph"].before(i, command)
                    if not decided:
                        return None
                    instead, told = decided
                    dep["blocked"][i] = (told, instead)
                    place_log[-1].update(blocked=told, ran_instead=instead)
                    return instead, None
        if arm in ("stateact", "stateact_chat"):
            env_type = next(v for k, v in STATEACT_TYPES.items() if job["family"].startswith(k))
            system = stateact_system(stateact_examples(env_type))
            outputs: list[str] = []

            def propose(v, cp):
                hist = v["history"]
                # our env keeps the task apart; ALFWorld's reset text ends with "\n\nYour task is to: <task>"
                turns = [stateact_first_observation(hist[0]["observation"] + "\n\nYour task is to: " + v["task"]) + "\n"]
                for i, out in enumerate(outputs):
                    turns += [">" + stateact_clean(out), stateact_observation(hist[i + 1]["observation"])]
                if arm == "stateact":   # their llamp OpenAIChatText / VLLMChat: the whole transcript as one user message
                    msgs = [{"role": "user", "content": system + "".join(turns)}]
                else:                   # chat turns: their prompt as the system message, then observation / output turns
                    msgs = [{"role": "system", "content": system}] + [
                        {"role": "user" if i % 2 == 0 else "assistant", "content": t} for i, t in enumerate(turns)]
                op = "actor-stateact" if arm == "stateact" else "actor-stateact-chat"
                out = book.ask(arm, "qwen", op, [msgs], actor, lambda: stateact_call(actor, msgs))
                outputs.append(out)
                listed, visited = places(hist)
                mv = stateact_visited(out)
                entry = {"step": len(hist) - 1, "code_visited": visited,
                         "code_not_visited": [p for p in listed if p not in visited], "output": out}
                if mv is None:
                    entry["error"] = "no locations visited line"
                else:
                    entry.update(model_visited=mv, model_not_visited=[p for p in listed if p not in mv])
                place_log.append(entry)
                return stateact_action(out)
        env = Episode(game)
        io_env[0], io_env[1] = env, job.get("tag") or arm
        t0, first_request = time.time(), book.last_request_id()
        try:
            view, decisions = _episode(job, arm, env, book, actor, example, check=check,
                                      show=show, propose=propose, veto=veto)
            won, steps, done = env.won, env.steps, env.done
        finally:
            env.close()
        if natural is not None and (view["task"] != natural["task"] or view["history"][0] != natural["history"][0]):
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
        diverged = None if natural is None else next(
            (i for i, (a, b) in enumerate(zip(hist, natural["history"])) if a != b),
            None if len(hist) == len(natural["history"]) else min(len(hist), len(natural["history"])))
        new_actor = book.db.execute("SELECT COUNT(*) FROM requests WHERE id>? AND reused=0 AND ok=1 "
                                    "AND operation NOT LIKE 'judge-%'", (first_request,)).fetchone()[0]
        llm_judge = dict(zip(("calls", "cache_hits"), book.db.execute(
            "SELECT SUM(reused=0), SUM(reused=1) FROM requests WHERE id>? AND operation LIKE 'judge-%'",
            (first_request,)).fetchone()))
        result = {"id": job["id"], "family": job["family"], "game": job["game"], "task": view["task"], "arm": job.get("tag") or job["arm"],
                  "won": won, "steps": steps, "end": "success" if won else "environment_end" if done else "step_limit",
                  "baseline_won": natural["won"] if natural else None, "baseline_steps": natural["steps"] if natural else None,
                  "baseline_source": "none (--no-baseline)" if natural is None else "src natural.json" if has_src_baseline else "direct.json (this run)",
                  "diverged_from_baseline_at": diverged, "history": hist, "decisions": decisions, "place_lists": place_log,
                  **({"thoughts": {str(k): v for k, v in sorted(thoughts.items())}, "think_errors": think_log} if arm in ("think_jev", "think_state", "think_copy") else {}),
                  **({"copies": copies} if arm == "think_copy" else {}),
                  **({"dep_graph": {"notes": {str(k): v for k, v in sorted(dep["notes"].items())},
                                    "blocked": {str(k): {"told": t, "ran_instead": r} for k, (t, r) in sorted(dep["blocked"].items())},
                                    "events": dep["graph"].events if dep["graph"] else [],
                                    "pointed_step": {str(k): v for k, v in sorted(dep["pointed"].items())},
                                    "hops": dep["graph"].hops if dep["graph"] else None}} if arm in (*DEP_ARMS, *PTR_ARMS) else {}),
                  "hints_shown": sum(not A.succeeded(h["observation"]) for h in hist[1:]) if arm == "hint" else 0,
                  "usage": {"judge": backend.usage.as_dict() if backend else
                            {"calls": llm_judge["calls"] or 0, "cache_hits": llm_judge["cache_hits"] or 0},
                            "new_actor_requests": new_actor,
                            "jev": dict(zip(("calls", "cache_hits"), (x or 0 for x in book.db.execute(
                                "SELECT SUM(reused=0), SUM(reused=1) FROM requests WHERE id>? AND role='jev'",
                                (first_request,)).fetchone()))),
                            "seconds": round(time.time() - t0, 1)},
                  "config": {k: job[k] for k in ("adapter", "fewshot", "record_style", "max_revisions",
                                                 "max_steps", "route")} if arm in ("d1", "h1") else
                            {k: job[k] for k in ("adapter", "fewshot", "record_style", "max_revisions",
                                                 "max_steps", "route", "mw_k", "mw_writer")} if arm == "mw" else
                            {k: job[k] for k in ("max_revisions", "max_steps", "route")} | (
                                {"hint": HINT} if arm == "hint" else {"note": "unvisited places (explored)"} if arm == "explore" else
                                {"note": "unvisited places written by the agent model (SELF_PLACES)"} if arm == "selfexplore" else
                                {"agent": "StateAct (arXiv 2410.02810), prompt_ids [1, 0], keys " + ",".join(STATEACT_KEYS),
                                 "prompt_source": "github.com/ai-nikolai/StateAct@8fb47be alfworld_runs/prompts/*_v4_*_base.py",
                                 "transcript": "one user message" if arm == "stateact" else "chat turns (system prompt, user observations, assistant outputs)"} if arm in ("stateact", "stateact_chat") else
                                {"agent": "standard ReAct (VBL App. F.3 / ReflAct App. K.1 / MPO)", "examples": "data/fewshot/mpo/alfworld_icl.json @5529eca"} if arm == "react_std" else
                                {"agent": "standard ReAct (as react_std) + dependency-graph controller (scripts/dep_graph.py)",
                                 "examples": "data/fewshot/mpo/alfworld_icl.json @5529eca",
                                 "culprit_search": "one hop" if arm == "react_dep" else "multi-hop walk over the graph"} if arm in DEP_ARMS else
                                {"agent": f"standard ReAct (as react_std) + {arm}: message at the dependency graph's trigger steps, see PTR_ARMS",
                                 "examples": "data/fewshot/mpo/alfworld_icl.json @5529eca"} if arm in PTR_ARMS else
                                {"note": "visited places kept by a decision model one record at a time (JEV_ARRIVED_Q); names from SELF_PLACES on r0",
                                 "jev_url": job["jev_url"], "jev_model": job["jev_model"]} if arm == "jevexplore" else
                                {"note": "jevexplore ledger", "checker": "name_check (taken object's name must be a word of the task)",
                                 "jev_url": job["jev_url"], "jev_model": job["jev_model"]} if arm == "jevexplore_name" else
                                {"note": "jevexplore ledger", "checker": "name_check, hard block (kept blocked takes are not run; env gets look)",
                                 "jev_url": job["jev_url"], "jev_model": job["jev_model"]} if arm == "jevexplore_hard" else
                                {"agent": "thinking agent (THINK_ACTION, data/fewshot/react_think_examples.json)",
                                 "note": "jevexplore ledger", "checker": "name_check, hard block",
                                 "jev_url": job["jev_url"], "jev_model": job["jev_model"]} if arm == "think_jev" else
                                {"note": "full state kept by the decision model (state_ledger.py)", "checker": "name_check, hard block",
                                 "jev_url": job["jev_url"], "jev_model": job["jev_model"]} if arm == "statejev" else
                                {"agent": "thinking agent (THINK_ACTION, data/fewshot/react_think_examples.json)",
                                 "note": "full state kept by the decision model (state_ledger.py)", "checker": "name_check, hard block",
                                 "jev_url": job["jev_url"], "jev_model": job["jev_model"]} if arm == "think_state" else
                                {"agent": "copies the state note, thinks, acts (THINK_COPY_ACTION, data/fewshot/react_think_copy_examples.json)",
                                 "note": "full state kept by the decision model (state_ledger.py)", "checker": "name_check, hard block",
                                 "jev_url": job["jev_url"], "jev_model": job["jev_model"]} if arm == "think_copy" else
                                {"note": "place lists asked inside the agent's own call (ONECALL_ACTION), nothing shown"} if arm == "onecall" else
                                {"note": "place lists asked inside the agent's own call, action based on them (ONECALL_USE_ACTION), nothing shown"} if arm == "onecall_use" else {"judge": "agent model, LLM_JUDGE"} if arm == "llm"
                                else {"checker": "repetition (loop_check)"} if arm == "loop"
                                else {"checker": "repetition (loop_check), then agent model LLM_JUDGE"} if arm == "llmloop"
                                else {"checker": "aeda.alfworld tracker"})}
        save(out_path, result)
        _write_io_log(folder, job.get("tag") or job["arm"], [x for x in io_log if x["phase"] != "baseline (direct)"])
        if arm in (*DEP_ARMS, *PTR_ARMS) and dep["graph"] is not None:   # the graph after every step
            import gzip as _gz
            if dep["done"] < len(view["history"]) - 1:   # the record that ended the game was never shown to the agent
                dep_catch_up(view)
            gl = dep["graph_log"]
            with _gz.open(folder / f"{job.get('tag') or job['arm']}_graph.jsonl.gz", "wt", encoding="utf-8") as fh:
                for x in gl:
                    fh.write(json.dumps(x, ensure_ascii=False) + "\n")
        if any(x["phase"] == "baseline (direct)" for x in io_log):
            _write_io_log(folder, "direct", [x for x in io_log if x["phase"] == "baseline (direct)"])
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
         "explore": "EXPLORE (unvisited places shown)", "selfexplore": "SELF-EXPLORE (model lists the places)", "jevexplore": "JEV-EXPLORE (decision model keeps the places)", "jevexplore_name": "JEV-EXPLORE + NAME CHECK", "jevexplore_hard": "JEV-EXPLORE + NAME CHECK (hard block)", "think_jev": "THINKING AGENT + OUR MODULE", "statejev": "FULL STATE (decision model) + NAME CHECK", "think_state": "THINKING AGENT + FULL STATE + NAME CHECK", "think_copy": "COPY STATE + THINK + NAME CHECK", "stateact": "STATEACT (published prompt, same games and model)", "react_std": "REACT (standard: VBL/ReflAct/MPO)", "react_std_t1536": "REACT (standard, 1536-token outputs)", "react_dep": "REACT + DEPENDENCY GRAPH", "react_dep_t1536": "REACT + DEPENDENCY GRAPH (1536-token outputs)", "react_dep_graph_t1536": "REACT + DEPENDENCY GRAPH, multi-hop walk",
         "react_ptr_none_t1536": "REACT + 'This failed.' (placebo)", "react_ptr_recent_t1536": "REACT + points at the step before the failure",
         "react_ptr_random_t1536": "REACT + points at a random earlier step", "react_ptr_dep_t1536": "REACT + points at the dependency-graph culprit step", "stateact_chat": "STATEACT-CHAT (same prompt, chat turns)", "onecall": "ONE-CALL (agent lists places, then acts, same call)", "onecall_use": "ONE-CALL-USE (lists, then an action based on them, same call)", "loop_r3": "LOOP, up to 3 revisions", "llmloop_r3": "LLM judge + LOOP, up to 3 revisions", "mw_v2demo": "MW-v2demo (precondition writer + agent's demo + D1)"}


def place_list_score(log: list[dict]) -> dict:
    """selfexplore: the model's not-visited list against the code list, per step."""
    log = [e for e in log if "code_not_visited" in e]   # arms that log other things (react_std, stateact outputs) have no lists
    ok = [e for e in log if "error" not in e and "model_not_visited" in e]
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
    has_base = all(r["baseline_won"] is not None for r in rows)
    s = {"arm": arm, "games": len(rows), "baseline_wins": sum(r["baseline_won"] for r in rows) if has_base else None,
         "d1_wins": sum(r["d1_won"] for r in rows),
         "rescued": [r["id"] for r in rows if r["d1_won"] and not r["baseline_won"]] if has_base else [],
         "lost": [r["id"] for r in rows if r["baseline_won"] and not r["d1_won"]] if has_base else [],
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
    ap.add_argument("--src", default=str(DEFAULT_SRC), help="finished paired run with protocol.json, routing.json, gameXX/")
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
    ap.add_argument("--arm", default="d1", choices=["d1", "t0", "hint", "mw", "h1", "llm", "loop", "llmloop", "explore", "selfexplore", "jevexplore", "jevexplore_name", "jevexplore_hard", "think_jev", "statejev", "think_state", "think_copy", "onecall", "onecall_use", "stateact", "stateact_chat", "react_std", *DEP_ARMS, *PTR_ARMS],
                    help="d1 = our method; t0 / hint = control arms (see the docstring)")
    ap.add_argument("--jev-url", default=os.getenv("JEV_URL", "http://127.0.0.1:8000/v1/systemone"),
                    help="jevexplore: System One endpoint (scripts/onejev_mac_server.py, flide serve, or TypeSafe)")
    ap.add_argument("--jev-model", default=os.getenv("JEV_MODEL", "OneJev1.6-4B"),
                    help="jevexplore: decision model name (answer cache key; sent as model to a remote endpoint)")
    ap.add_argument("--react-max-tokens", type=int, default=512,
                    help="react_std: output-token limit per step (512 = MPO's default; other values run as react_std_t<N>)")
    ap.add_argument("--no-baseline", action="store_true",
                    help="play only --arm, without the baseline (direct) run; used for valid_unseen (runs/online/unseen)")
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
    if a.arm in ("react_std", *DEP_ARMS, *PTR_ARMS) and a.react_max_tokens != 512:
        tag = f"{a.arm}_t{a.react_max_tokens}"   # keeps the 512-token runs (react_std.json) apart
    if a.arm in ("loop", "llmloop") and a.max_revisions != 1:
        tag = f"{a.arm}_r{a.max_revisions}"  # keeps the --max-revisions 1 results (loop.json) apart
    if not os.getenv("OPENROUTER_API_KEY"):
        ap.error("set OPENROUTER_API_KEY in this terminal")
    if a.arm in ("jevexplore", "jevexplore_name", "jevexplore_hard", "think_jev", "statejev", "think_state", "think_copy"):  # fail now, not inside every game, when the decision model is not up
        try:
            JevPlaces(a.jev_url, a.jev_model, timeout=120).ask(
                {"record": {"action": "look", "observation": "Nothing happens."}},
                {"arrived": {"type": "choice", "instructions": JEV_ARRIVED_Q, "criteria": {"a 1": "a 1", "none": "none"}}})
        except RuntimeError as e:
            ap.error(f"{e}; start scripts/onejev_mac_server.py (or flide serve) first, or pass --jev-url")
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
    run_config = json.dumps({**vars(a), "tag": tag, "route": route, "baseline_protocol": str(src / "protocol.json")}, indent=1)
    (out / "run_config.json").write_text(run_config)          # the latest run in this folder
    (out / f"run_config_{tag}.json").write_text(run_config)   # kept per arm, so a later arm does not erase it
    jobs = [{"id": g["id"], "game": g["game"], "family": g["family"], "action_example_sha256": g["action_example_sha256"],
             "src": str(src), "out": str(out), "runner": str(Path(a.runner).expanduser()), "split": str(Path(a.split_dir).expanduser()),
             "route": route, "adapter": a.adapter, "fewshot": a.fewshot, "record_style": a.record_style,
             "max_revisions": a.max_revisions, "max_steps": a.max_steps, "arm": a.arm, "tag": tag, "mw_k": a.mw_k,
             "mw_writer": a.mw_writer, "jev_url": a.jev_url, "jev_model": a.jev_model, "no_baseline": a.no_baseline,
             "react_max_tokens": a.react_max_tokens}
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
                base = (f"(baseline {'win' if r['baseline_won'] else 'loss'} in {r['baseline_steps']}), "
                        if r["baseline_won"] is not None else "(no baseline), ")
                print(f"{gid}: {a.arm} {'WIN' if r['won'] else r['end']} in {r['steps']} steps {base}"
                      f"{sum(d['blocked'] for d in r['decisions'])} blocked", flush=True)
            except Exception as e:  # report and keep the other games; rerun resumes finished games from disk
                failed.append(gid)
                cause = f" (cause: {str(e.__cause__).strip().splitlines()[-1]})" if e.__cause__ else ""
                print(f"{gid}: FAILED {type(e).__name__}: {e}{cause}", flush=True)
    s = summarize(results, out, tag)
    md = out / ("summary.md" if tag == "d1" else f"summary_{tag}.md")
    print(f"\nbaseline {s['baseline_wins']}/{s['games']}  {LABEL.get(tag, tag)} {s['d1_wins']}/{s['games']}  -> {md}")
    if failed:
        print(f"failed games (rerun the same command to resume): {', '.join(sorted(failed))}")
        sys.exit(2)


if __name__ == "__main__":
    main()
