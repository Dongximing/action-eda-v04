#!/usr/bin/env python3
"""Dependency graph over an agent's beliefs, with evidence levels, culprit selection and ruled-out beliefs.

Training-free controller around an unchanged agent (arm react_dep in run_online.py). It reads only the task text and
the environment's feedback so far.

Beliefs (each with the step it was formed at and an evidence level):
  at R            you are at R                      from "You arrive at R"
  holding X       you hold X                        from "You pick up X" / "You move X to ..."
  empty           your hands are empty
  in X R          X is in/on R                      from the "you see ..." lists
  open R          R is open                         from "R is closed" / "You open R"
  bind X          X is the object the task names    supported only when X's name is the task's object word
  done V X        X has been V-ed (heat/cool/clean) supported only by "You V the X"; refuted otherwise (the
                                                    agent's own history is complete, so no such reply = not done)
  can V T         a T can V things                  supported after one success with a T; unsupported before
Levels: supported < unsupported < refuted < ruled_out (ruled out = a culprit already chosen).

Dependencies of a command (ALFWorld adapter, from the action guide's preconditions):
  take X from R        at R, empty, in X R
  move X to R          holding X, at R, open R;  into the goal: also bind X and done V X (task verb V)
  open/close R         at R
  V X with R           holding X, at R, bind X, can V type(R)
  use R                at <where R was seen>
Completion (the task should be finished but the game goes on): after the last goal placement (the second one in
a two-object task) -> bind X, done V X; after "use" of the lamp in a look-at task -> holding <task object>.

Decisions:
  before a command runs  any dependency ruled out or refuted -> not run ("look" instead, or put the wrongly bound
                         object down here when that is what blocks it); the agent sees why.
  after a failure        (a command that ran and got "Nothing happens", or a completion that did not finish)
                         culprit = the refuted dependency if any; else the unsupported dependency formed earliest,
                         which is then ruled out. Not chronological: the culprit can be many steps back.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_loops import parse_task  # noqa: E402

ENT = r"[a-z]+ \d+"
PAST = {"heat": "heated", "cool": "cooled", "clean": "cleaned"}
RANK = {"supported": 0, "unsupported": 1, "refuted": 2, "ruled_out": 3}
STATE = ("at", "holding", "empty", "open")   # beliefs about the current situation; never ruled out
ASSUMPTIONS = ("bind", "can")                 # beliefs no reply has to back: checked at every hop of the walk


def norm(a: str) -> str:
    a = " ".join((a or "").lower().split())
    m = re.match(r"put\s+(.*?)\s+(?:in/on|in|on)\s+(.*)$", a)
    return f"move {m.group(1)} to {m.group(2)}" if m else a


def kind(entity: str | None) -> str | None:
    return entity.split()[0] if entity else None


def bid(key) -> str:
    """Node id of a belief, e.g. ("bind", "towel 1") -> "b:bind:towel 1"."""
    return "b:" + ":".join(str(x) for x in key)


class DepGraph:
    def __init__(self, task: str, opening: str, hops: int | None = 1):
        """hops: how far the culprit search walks back through the graph (1 = the beliefs of the failed command
        only, as in the first runs; None = no limit)."""
        self.task = task
        self.hops = hops
        # the graph: nodes (actions, game replies, beliefs, the task text) and typed edges
        #   action -got-> reply                 the reply the command got
        #   action -needs-> belief              a precondition of the command
        #   action -relies_on-> belief          an assumption the command commits to (take X: X is the task's object)
        #   action -creates-> belief            the command made it true (or assumed it, for bind)
        #   action -falsifies-> belief          the command made it false
        #   reply -supports-> belief / reply -refutes-> belief / task -supports-> belief
        self.nodes: dict = {"task": {"id": "task", "type": "task", "text": task}}
        self.edges: list = []
        self._edge_set: set = set()
        self.verb, self.obj, self.goal = parse_task(task)
        self.two = bool(re.search(r"\btwo\b", task.lower()))
        self.light = "lamp" in task.lower()
        self.loc, self.loc_step = None, 0
        self.held, self.held_step, self.held_text = None, 0, ""
        self.last_drop: dict = {}            # object -> (step, feedback) of putting it down
        self.where: dict = {}                # object -> (receptacle, step)
        self.closed: dict = {}               # receptacle -> (is closed, step)
        self.done: dict = {}                 # object -> {verb: step}
        self.bind: dict = {}                 # object -> step it was first taken
        self.can: dict = {}                  # (verb, type) -> step of a success
        self.can_first: dict = {}            # (verb, type) -> step it was first relied on
        self.ruled_out: dict = {}            # belief key -> (step, why)
        self.goal_placed: list = []          # objects moved into a goal receptacle
        self.events: list = []               # what the controller decided, per step (for the logs)
        self.last = None                     # the culprit of the latest after() call
        self.formed_at: dict = {}            # ruled-out belief -> the step it was formed at

    # ----------------------------------------------------------------- the graph
    def _node(self, nid: str, **attrs) -> str:
        n = self.nodes.setdefault(nid, {"id": nid})
        for k, v in attrs.items():
            if k == "first_step":
                n.setdefault(k, v)
            else:
                n[k] = v
        return nid

    def _belief(self, key, step: int) -> str:
        return self._node(bid(key), type="belief", key=list(key), text=self.text(key), first_step=step)

    def _edge(self, src: str, rel: str, dst: str, step: int) -> None:
        if (src, rel, dst) not in self._edge_set:
            self._edge_set.add((src, rel, dst))
            self.edges.append({"src": src, "rel": rel, "dst": dst, "step": step})

    def out_edges(self, src: str, rels: tuple) -> list:
        return [e for e in self.edges if e["src"] == src and e["rel"] in rels]

    def in_edges(self, dst: str, rels: tuple) -> list:
        return [e for e in self.edges if e["dst"] == dst and e["rel"] in rels]

    # ----------------------------------------------------------------- state from feedback
    def update(self, step: int, action: str, obs: str) -> None:
        """Record step `step`: the command the environment ran and its feedback (state and graph)."""
        a, o = norm(action), " ".join((obs or "").lower().split())
        an = self._node(f"a{step}", type="action", step=step, command=action, failed=o.startswith("nothing happens"))
        rn = self._node(f"r{step}", type="reply", step=step, text=(obs or "").strip())
        self._edge(an, "got", rn, step)
        for key in self.deps(action):
            self._edge(an, "needs", self._belief(key, step), step)
        mt = re.fullmatch(rf"take ({ENT}) from ({ENT})", a)
        if mt:
            self._edge(an, "relies_on", self._belief(("bind", mt.group(1)), step), step)
        m = re.match(rf"you arrive at ({ENT})\.", o)
        if m:
            b = self._belief(("at", m.group(1)), step)
            self._edge(an, "creates", b, step)
            self._edge(rn, "supports", b, step)
            self.loc, self.loc_step = m.group(1), step
            if re.search(rf"the {re.escape(self.loc)} is closed", o):
                self.closed[self.loc] = (True, step)
            elif "is open" in o:
                self.closed[self.loc] = (False, step)
        m = re.match(rf"you open the ({ENT})", o)
        if m:
            b = self._belief(("open", m.group(1)), step)
            self._edge(an, "creates", b, step)
            self._edge(rn, "supports", b, step)
            self.closed[m.group(1)] = (False, step)
            for it in re.findall(rf"\b({ENT})\b", o.split("you see", 1)[-1] if "you see" in o else ""):
                self.where[it] = (m.group(1), step)
        m = re.match(rf"you close the ({ENT})", o)
        if m:
            b = self._belief(("open", m.group(1)), step)
            self._edge(an, "falsifies", b, step)
            self._edge(rn, "refutes", b, step)
            self.closed[m.group(1)] = (True, step)
        if "you see" in o and not o.startswith("you open"):
            rec = self.loc
            for it in re.findall(rf"\b({ENT})\b", o.split("you see", 1)[1]):
                if rec:
                    self.where[it] = (rec, step)
        for it, (rec, s) in list(self.where.items()):   # evidence came back: a ruled-out "X is in R" is lifted
            if s == step:
                self.ruled_out.pop(("in", it, rec), None)
                self._edge(rn, "supports", self._belief(("in", it, rec), step), step)
        m = re.match(rf"you pick up the ({ENT}) from the ({ENT})", o)
        if m:
            x = m.group(1)
            b = self._belief(("holding", x), step)
            self._edge(an, "creates", b, step)
            self._edge(rn, "supports", b, step)
            self._edge(an, "falsifies", self._belief(("empty",), step), step)
            self._edge(rn, "refutes", self._belief(("empty",), step), step)
            if self.held is None:
                self.bind.setdefault(x, step)
            bb = self._belief(("bind", x), self.bind.get(x, step))
            self._edge(an, "creates", bb, step)
            if kind(x) == self.obj:
                self._edge("task", "supports", bb, step)
            self.held, self.held_step, self.held_text = x, step, obs.strip()
            self.where.pop(x, None)
            self.bind.setdefault(x, step)
        m = re.match(rf"you (?:move|put) the ({ENT}) (?:to|in|on|in/on) the ({ENT})", o)
        if m:
            b = self._belief(("holding", m.group(1)), step)
            self._edge(an, "falsifies", b, step)
            self._edge(rn, "refutes", b, step)
            e = self._belief(("empty",), step)
            self._edge(an, "creates", e, step)
            self._edge(rn, "supports", e, step)
            i = self._belief(("in", m.group(1), m.group(2)), step)
            self._edge(an, "creates", i, step)
            self._edge(rn, "supports", i, step)
            self.held, self.held_step = None, step
            self.last_drop[m.group(1)] = (step, obs.strip())
            self.where[m.group(1)] = (m.group(2), step)
            if self.goal and kind(m.group(2)) == self.goal:
                self.goal_placed.append(m.group(1))
        m = re.match(rf"you (heat|cool|clean) the ({ENT}) using the ({ENT})", o)
        if m:
            d = self._belief(("done", m.group(1), m.group(2)), step)
            self._edge(an, "creates", d, step)
            self._edge(rn, "supports", d, step)
            self._edge(rn, "supports", self._belief(("can", m.group(1), kind(m.group(3))), step), step)
            self.done.setdefault(m.group(2), {})[m.group(1)] = step
            self.can[(m.group(1), kind(m.group(3)))] = step
            self.ruled_out.pop(("can", m.group(1), kind(m.group(3))), None)

    # ----------------------------------------------------------------- beliefs
    def text(self, key) -> str:
        k = key[0]
        return {"at": lambda: f"you are at {key[1]}", "holding": lambda: f"you are holding {key[1]}",
                "empty": lambda: "your hands are empty", "in": lambda: f"{key[1]} is in/on {key[2]}",
                "open": lambda: f"{key[1]} is open", "bind": lambda: f"{key[1]} is the {self.obj} the task asks for",
                "done": lambda: f"{key[2]} has been {PAST[key[1]]}", "can": lambda: f"a {key[2]} can {key[1]} things"}[k]()

    def level(self, key, step: int) -> tuple[str, int, str]:
        """(evidence level, step the belief was formed at, the evidence in words)."""
        if key in self.ruled_out:
            s, why = self.ruled_out[key]
            return "ruled_out", s, why
        k = key[0]
        if k == "at":   # never "refuted": receptacles can share a spot (cabinet 1 / cabinet 2), which feedback does not show
            if self.loc == key[1]:
                return "supported", self.loc_step, ""
            return "unsupported", step, (f"the last place you arrived at is {self.loc} (step {self.loc_step})" if self.loc
                                         else "you have not gone anywhere yet")
        if k == "holding":
            if self.held == key[1]:
                return "supported", self.held_step, ""
            if self.held:
                return "refuted", self.held_step, f"you are holding {self.held} (step {self.held_step})"
            if key[1] in self.last_drop:
                s, t = self.last_drop[key[1]]
                return "refuted", s, f'step {s}: "{t}"'
            return "refuted", 0, f"you never picked up {key[1]}"
        if k == "empty":
            if not self.held:
                return "supported", self.held_step, ""
            return "refuted", self.held_step, f"you are holding {self.held} (step {self.held_step})"
        if k == "in":
            if key[1] in self.where:
                rec, s = self.where[key[1]]
                if rec == key[2]:
                    return "supported", s, ""
                return "refuted", s, f"{key[1]} was seen in/on {rec} (step {s})"
            return "unsupported", step, f"{key[1]} has not been seen in/on {key[2]}"
        if k == "open":
            c = self.closed.get(key[1])
            if c and c[0]:
                return "refuted", c[1], f"{key[1]} is closed (step {c[1]})"
            return "supported", c[1] if c else 0, ""
        if k == "bind":
            s = self.bind.get(key[1], step)
            if kind(key[1]) == self.obj:
                return "supported", s, ""
            return "unsupported", s, f'the task names "{self.obj}"; you took {key[1]} at step {s}, and no feedback says it is a {self.obj}'
        if k == "done":
            s = self.done.get(key[2], {}).get(key[1])
            if s is not None:
                return "supported", s, ""
            return "refuted", step, f'no feedback said "You {key[1]} the {key[2]}"'
        if k == "can":
            if key[1:] in self.can:
                return "supported", self.can[key[1:]], ""
            s = self.can_first.setdefault(key[1:], step)
            return "unsupported", s, f"no {key[2]} has worked for {key[1]} yet"
        raise ValueError(key)

    def deps(self, command: str) -> list:
        c = norm(command)
        m = re.fullmatch(rf"take ({ENT}) from ({ENT})", c)
        if m:
            return [("at", m.group(2)), ("empty",), ("in", m.group(1), m.group(2))]
        m = re.fullmatch(rf"move ({ENT}) to ({ENT})", c)
        if m:
            x, r = m.group(1), m.group(2)
            out = [("holding", x), ("at", r), ("open", r)]
            if self.goal and kind(r) == self.goal:
                out.append(("bind", x))
                if self.verb:
                    out.append(("done", self.verb, x))
            return out
        m = re.fullmatch(rf"(?:open|close) ({ENT})", c)
        if m:
            return [("at", m.group(1))]
        m = re.fullmatch(rf"(heat|cool|clean) ({ENT}) with ({ENT})", c)
        if m:
            return [("holding", m.group(2)), ("at", m.group(3)), ("bind", m.group(2)), ("can", m.group(1), kind(m.group(3)))]
        m = re.fullmatch(rf"use ({ENT})", c)
        if m and m.group(1) in self.where:
            return [("at", self.where[m.group(1)][0])]
        return []

    def completion_deps(self, step: int, action: str, obs: str) -> list:
        """Dependencies of 'the task is now finished' when this step should have finished it (game goes on)."""
        a, o = norm(action), (obs or "").lower()
        m = re.fullmatch(rf"move ({ENT}) to ({ENT})", a)
        if m and o.startswith("you move") and self.goal and kind(m.group(2)) == self.goal:
            if self.two and len(self.goal_placed) < 2:
                return []
            out = [("bind", x) for x in self.goal_placed[-2 if self.two else -1:]]
            if self.verb:
                out.append(("done", self.verb, m.group(1)))
            return out
        if self.light and re.fullmatch(rf"use ({ENT})", a) and not o.startswith("nothing happens"):
            if self.held:
                return [("bind", self.held)]
            target = next((x for x in self.bind if kind(x) == self.obj), f"{self.obj} 1")
            return [("holding", target)]
        return []

    def snapshot(self, step: int) -> dict:
        """The ledger after `step`: every belief the controller holds, with its evidence level and the step behind it."""
        def lv(key):
            level, s, why = self.level(key, step)
            return {"belief": self.text(key), "level": level, "step": s, **({"why": why} if why else {})}
        out = {"location": self.loc or "(start)", "location_step": self.loc_step,
               "holding": self.held or "nothing", "holding_step": self.held_step,
               "taken_for_task": [lv(("bind", x)) for x in self.bind],
               "transforms_done": [f"{x}: {v} (step {s})" for x, d in self.done.items() for v, s in d.items()],
               "tools_known": [f"a {t} can {v} things (step {s})" for (v, t), s in self.can.items()],
               "closed": [r for r, (c, _) in self.closed.items() if c],
               "ruled_out": [{"belief": self.text(k), "at_step": s, "why": w} for k, (s, w) in self.ruled_out.items()]}
        return out

    def maker(self, key, level: str) -> str | None:
        """The action node behind a belief's current status: the latest one that falsified it (refuted) or
        created it (unsupported). None when no command made it so (never arrived there, never tried, ...)."""
        rel = ("falsifies",) if level == "refuted" else ("creates",)
        es = self.in_edges(bid(key), rel)
        return max(es, key=lambda e: e["step"])["src"] if es else None

    def trace(self, start_keys: list, step: int) -> list:
        """Walk back through the graph from the beliefs a failed command needs: a belief without support leads to
        the action that made it so, whose own needs/relies_on beliefs are checked in turn, up to self.hops.
        Returns (key, hop, level, step formed, evidence) for every unsupported belief reached, nearest first."""
        out, seen = [], set()
        frontier = [(tuple(k), 1) for k in start_keys]
        while frontier:
            key, hop = frontier.pop(0)
            if key in seen:
                continue
            if hop > 1 and key[0] not in ASSUMPTIONS:   # an earlier command that ran: its situation facts held then
                continue
            seen.add(key)
            lv, s, why = self.level(key, step)
            if lv == "supported":
                continue
            out.append((key, hop, lv, s, why))
            if self.hops is not None and hop >= self.hops:
                continue
            m = self.maker(key, "refuted" if lv in ("refuted", "ruled_out") and key[0] in STATE else lv)
            if m:
                frontier += [(tuple(self.nodes[e["dst"]]["key"]), hop + 1) for e in self.out_edges(m, ("needs", "relies_on"))]
        return out

    def graph_at(self, step: int) -> dict:
        """The whole graph after `step`, with every belief's current evidence level (no side effects)."""
        saved = dict(self.can_first)
        nodes = []
        for n in self.nodes.values():
            n = dict(n)
            if n.get("type") == "belief":
                lv, s, why = self.level(tuple(n["key"]), step)
                n.update(level=lv, level_step=s, **({"why": why} if why else {}))
            nodes.append(n)
        self.can_first = saved
        return {"step": step, "nodes": nodes, "edges": list(self.edges)}

    # ----------------------------------------------------------------- decisions
    def before(self, step: int, command: str):
        """None to run the command; else (command to run instead, what the agent is told)."""
        keys = self.deps(command)
        mt = re.fullmatch(rf"take ({ENT}) from ({ENT})", norm(command))
        if mt and self.hops != 1:      # graph mode: taking an object ruled out as the task's object is not run
            keys = keys + [("bind", mt.group(1))]
        for key in keys:
            lv, s, why = self.level(key, step)
            if lv == "ruled_out":
                if key[0] == "bind" and self.held == key[1] and self.loc and not self.closed.get(self.loc, (False,))[0]:
                    instead = f"move {key[1]} to {self.loc}"
                    if instead == norm(command):   # it is putting the object down here anyway
                        return None
                    note = f'Not run: it relies on "{self.text(key)}", which was ruled out at step {s} ({why}).'
                else:
                    instead = "look"
                    note = f'Not run: it relies on "{self.text(key)}", which was ruled out at step {s} ({why}).'
                self.events.append({"step": step, "type": "blocked", "command": command, "belief": self.text(key), "level": lv, "instead": instead})
                return instead, note
            if lv == "refuted":
                note = f'Not run: it needs "{self.text(key)}", but {why}.'
                instead = "look"
                if self.hops != 1:   # graph mode: walk back from the false fact to the assumption behind it
                    roots = sorted([c for c in self.trace([key], step) if c[1] > 1 and c[2] == "unsupported"
                                    and c[0][0] not in STATE], key=lambda c: (c[3], -c[1]))
                    if roots:
                        rk, hop, _, rs, rwhy = roots[0]
                        self.ruled_out[rk] = (step, rwhy)
                        self.formed_at[rk] = rs
                        note += (f' That goes back to step {rs}, which relied on "{self.text(rk)}", which no feedback '
                                 f"supports: {rwhy}. That is now ruled out.")
                        self.events.append({"step": step, "type": "culprit", "belief": self.text(rk), "level": "unsupported",
                                            "formed": rs, "hops": hop, "ruled_out": True})
                        if rk[0] == "bind" and self.held == rk[1] and self.loc and not self.closed.get(self.loc, (False,))[0]:
                            instead = f"move {rk[1]} to {self.loc}"   # put the wrongly taken object down here
                            note += f" Put {rk[1]} down here instead."
                self.events.append({"step": step, "type": "blocked", "command": command, "belief": self.text(key), "level": lv, "instead": instead})
                return instead, note
        return None

    def after(self, step: int, action: str, obs: str, ran_as_agent: bool) -> str | None:
        """Call after update(step, ...). A note for the agent when this step failed or did not finish the task."""
        self.last = None   # the culprit chosen here: {"what", "formed", "belief"} (read by the pointer arms)
        failed = (obs or "").strip().lower().startswith("nothing happens")
        if failed and ran_as_agent:
            deps, what = self.deps(action), "This failed."
        else:
            deps, what = self.completion_deps(step, action, obs), "The task is not finished."
        if not deps:
            return None
        self._node(f"c{step}", type="completion", step=step) if what.startswith("The task") else None
        if what.startswith("The task"):
            for key in deps:
                self._edge(f"c{step}", "needs", self._belief(key, step), step)
        if self.hops != 1:
            return self._after_graph(step, deps, what)
        levels = [(key, *self.level(key, step)) for key in deps]
        refuted = [x for x in levels if x[1] in ("refuted", "ruled_out")]
        if refuted:
            key, lv, s, why = refuted[0]
            formed = self.formed_at.get(key, s) if lv == "ruled_out" else s   # a ruled-out belief: where it was formed
            self.events.append({"step": step, "type": "culprit", "belief": self.text(key), "level": lv, "formed": formed})
            self.last = {"what": what, "formed": formed, "belief": self.text(key)}
            return f'{what} It needs "{self.text(key)}", but {why}.'
        state = [x for x in levels if x[1] == "unsupported" and x[0][0] in STATE]
        if state:   # unverified position or hands: told, not ruled out (it changes as the agent acts)
            key, lv, s, why = state[0]
            self.events.append({"step": step, "type": "culprit", "belief": self.text(key), "level": lv, "formed": s})
            self.last = {"what": what, "formed": s, "belief": self.text(key)}
            return f'{what} It needs "{self.text(key)}", which no feedback supports: {why}.'
        unsup = sorted([x for x in levels if x[1] == "unsupported"], key=lambda x: x[2])
        if unsup:   # position and hands check out: blame the assumption formed earliest and rule it out
            key, lv, s, why = unsup[0]
            self.ruled_out[key] = (step, why)
            self.formed_at[key] = s
            self.events.append({"step": step, "type": "culprit", "belief": self.text(key), "level": lv, "formed": s, "ruled_out": True})
            self.last = {"what": what, "formed": s, "belief": self.text(key)}
            return f'{what} It relies on "{self.text(key)}" (assumed at step {s}), which no feedback supports: {why}. That is now ruled out.'
        return None

    def _after_graph(self, step: int, deps: list, what: str) -> str | None:
        """Multi-hop culprit search: the immediate cause among the failed command's own needs (as with hops=1),
        then the walk goes on through the actions behind them; the earliest unsupported assumption reached is
        ruled out, even when it is several steps back."""
        cands = self.trace(deps, step)
        hop1 = [c for c in cands if c[1] == 1]
        immediate = next((c for c in hop1 if c[2] in ("refuted", "ruled_out")), None) or \
            next((c for c in hop1 if c[2] == "unsupported" and c[0][0] in STATE), None)
        roots = sorted([c for c in cands if c[2] == "unsupported" and c[0][0] not in STATE and (immediate is None or c[1] > 1)],
                       key=lambda c: (c[3], -c[1]))
        parts, culprit = [], None
        if immediate:
            key, hop, lv, s, why = immediate
            parts.append(f'It needs "{self.text(key)}", but {why}.' if lv in ("refuted", "ruled_out")
                         else f'It needs "{self.text(key)}", which no feedback supports: {why}.')
            culprit = (key, s)
        if roots:
            key, hop, lv, s, why = roots[0]
            self.ruled_out[key] = (step, why)
            self.formed_at[key] = s
            parts.append((f'That goes back to step {s}, which relied on "{self.text(key)}"' if immediate else
                          f'It relies on "{self.text(key)}" (assumed at step {s})') +
                         f", which no feedback supports: {why}. That is now ruled out.")
            culprit = (key, s)
            self.events.append({"step": step, "type": "culprit", "belief": self.text(key), "level": lv, "formed": s,
                                "hops": hop, "ruled_out": True})
        if immediate and not roots:
            self.events.append({"step": step, "type": "culprit", "belief": self.text(immediate[0]), "level": immediate[2],
                                "formed": immediate[3], "hops": 1})
        if not parts:
            return None
        self.last = {"what": what, "formed": culprit[1], "belief": self.text(culprit[0])}
        return f"{what} " + " ".join(parts)
