#!/usr/bin/env python3
"""Offline checks of two more jobs for the decision model (OneJev / Jev), on logged trajectories. No game is played.

  --check object   Before "take X from Y": is X the object the task asks for? One yes/no ("noul") question per
                   distinct (task, taken object type) pair found in runs/online/*/*/*.json and the 12 baseline
                   trajectories. Answer key from the names: the taken object's type equals the task's object.
                   Two wordings are asked (--wording plain | exact | both).
  --check seen     Which place's contents does this record show (what is in or on it)? One choice question per
                   record (options: the places of r0 plus none), accumulated into "searched" places, on the
                   selfexplore trajectories (the same records as jev_places_offline.py --mode incremental).
                   Answer key from the feedback text: "On the P, you see ...", "The P is open. In it, you see ...".
                   A place the agent reached while it was closed is not searched. Scored per record and per logged
                   step (the not-searched list exact).

Both ask a System One endpoint (scripts/onejev_mac_server.py, flide serve, or TypeSafe Jev):
  python3 scripts/jev_checks_offline.py --check object
  python3 scripts/jev_checks_offline.py --check seen
Answers are cached in runs/jev_checks/<check>/cache.jsonl; report.md and rows.jsonl beside it.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jev_places_offline import DIRS, ROOT, Client, choice_of, code_places, load_games, yes_prob  # noqa: E402

TASK = [re.compile(r"put an? (clean|hot|cool) (\w+) in (\w+)"),
        re.compile(r"(clean|heat|cool) some (\w+) and put it in (\w+)")]
OBJECT_Q = {
    "plain": "The object this command takes is the object the task asks for.",
    "exact": "The object this command takes is exactly the object named in the task (the same object name, ignoring its number).",
}
SEEN_Q = ("The record is a command and the environment's feedback. Which of these places does the feedback show the "
          "contents of (what is in it or on it)? Choose none if it shows no place's contents.")
_SEEN = [re.compile(r"^you arrive at ([a-z]+ \d+)\. on the \1, you see"),
         re.compile(r"^you arrive at ([a-z]+ \d+)\. the \1 is open\. in it, you see"),
         re.compile(r"^you open the ([a-z]+ \d+)\. the \1 is open\. in it, you see"),
         re.compile(r"^on the ([a-z]+ \d+), you see")]


def task_object(task: str) -> str:
    t = task.lower()
    for p in TASK:
        m = p.search(t)
        if m:
            return m.group(2)
    raise ValueError(f"unknown task {task!r}")


def seen_place(observation: str) -> str | None:
    o = observation.strip().lower()
    for p in _SEEN:
        m = p.match(o)
        if m:
            return m.group(1)
    return None


# ------------------------------------------------------------------ object check

def take_samples() -> list[dict]:
    """Distinct (task, taken object type) pairs, each with the first command that took it."""
    files = glob.glob(str(ROOT / "runs/online/*/*/*.json")) + glob.glob(str(ROOT / "baseline/oneshot12/game*/natural.json"))
    seen, out = set(), []
    for f in sorted(files):
        try:
            r = json.loads(Path(f).read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(r, dict) or "history" not in r or "task" not in r:
            continue
        want = task_object(r["task"])
        for h in r["history"][1:]:
            m = re.match(r"you pick up the ([a-z]+) (\d+) from", h["observation"].strip().lower())
            if not m:
                continue
            key = (r["task"].strip().lower(), m.group(1))
            if key in seen:
                continue
            seen.add(key)
            out.append({"task": r["task"].strip(), "command": h["action"].strip(), "taken": m.group(1),
                        "wanted": want, "match": m.group(1) == want})
    return out


def run_object(client: Client, wordings: list[str], workers: int) -> tuple[list[dict], list[str]]:
    samples = take_samples()

    def one(s):
        row = dict(s)
        for w in wordings:
            try:
                resp = client.ask({"task": s["task"], "command": s["command"]},
                                  {"same": {"type": "noul", "instructions": OBJECT_Q[w]}})
                row[f"p_{w}"] = yes_prob(resp["answers"]["same"])
            except (KeyError, TypeError, ValueError) as e:
                row[f"error_{w}"] = f"{type(e).__name__}: {e}"
        return row
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        rows = list(ex.map(one, samples))
    lines = [f"# Object check offline: {len(rows)} distinct (task, taken object) pairs", "",
             "Answer key: the taken object's type equals the task's object (names). P(yes) >= 0.5 counts as yes.", ""]
    for w in wordings:
        ok = [r for r in rows if f"p_{w}" in r]
        pos = [r for r in ok if r["match"]]
        neg = [r for r in ok if not r["match"]]
        tp = sum(r[f"p_{w}"] >= 0.5 for r in pos)
        tn = sum(r[f"p_{w}"] < 0.5 for r in neg)
        lines += [f"## Wording `{w}`: \"{OBJECT_Q[w]}\"", "",
                  f"- right object, answered yes: {tp}/{len(pos)}",
                  f"- wrong object, answered no (would be blocked): {tn}/{len(neg)}",
                  f"- unusable answers: {len(rows) - len(ok)}", "",
                  "| task object | taken | pairs | answered no | mean P(yes) |", "|---|---|---|---|---|"]
        groups = collections.defaultdict(list)
        for r in neg:
            groups[(r["wanted"], r["taken"])].append(r[f"p_{w}"])
        for (want, took), ps in sorted(groups.items(), key=lambda x: (-len(x[1]), x[0])):
            lines.append(f"| {want} | {took} | {len(ps)} | {sum(p < 0.5 for p in ps)} | {sum(ps) / len(ps):.2f} |")
        lines.append("")
    return rows, lines


# ------------------------------------------------------------------ seen-inside ledger

def run_seen(client: Client, workers: int, limit: int) -> tuple[list[dict], list[str]]:
    games = load_games(DIRS, limit)
    rec_right = rec_total = 0
    confusion = collections.Counter()

    def one(g):
        hist = g["history"]
        listed, _ = code_places(hist[:1])
        crit = {p: p for p in listed}
        crit["none"] = "none of these places"
        chosen, gold, errors = {}, {}, 0
        last = max([e["step"] for e in g["place_lists"]], default=0)
        for k in range(1, last + 1):
            rec = {kk: hist[k][kk] for kk in ("action", "observation")}
            gp = seen_place(hist[k]["observation"])
            gold[k] = gp if gp in listed else None
            try:
                resp = client.ask({"record": rec}, {"seen": {"type": "choice", "instructions": SEEN_Q, "criteria": crit}})
                c = choice_of(resp["answers"]["seen"], listed + ["none"])
            except (KeyError, TypeError, ValueError):
                c, errors = "none", errors + 1
            chosen[k] = None if c == "none" else c
        out = []
        for e in g["place_lists"]:
            ks = range(1, e["step"] + 1)
            got = list(dict.fromkeys(chosen[k] for k in ks if chosen.get(k)))
            want = list(dict.fromkeys(gold[k] for k in ks if gold.get(k)))
            out.append({"folder": g["folder"], "id": g["id"], "step": e["step"],
                        "searched": want, "not_searched": [p for p in listed if p not in want],
                        "model_searched": got, "model_not_searched": [p for p in listed if p not in got],
                        "arrived_not_searched": [p for p in e["code_visited"] if p not in want]})
        return out, [(gold[k], chosen[k]) for k in sorted(gold)], errors
    rows, errs = [], 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for out, pairs, e in ex.map(one, games):
            rows += out
            errs += e
            for gp, cp in pairs:
                rec_total += 1
                rec_right += gp == cp
                if gp != cp:
                    confusion[("place" if gp else "none", "none" if cp is None else ("same" if cp == gp else "other place"))] += 1
    n = len(rows)
    exact = sum(set(r["model_not_searched"]) == set(r["not_searched"]) for r in rows)
    missing = sum(len(set(r["not_searched"]) - set(r["model_not_searched"])) for r in rows)
    extra = sum(len(set(r["model_not_searched"]) - set(r["not_searched"])) for r in rows)
    arrived_closed = sum(len(r["arrived_not_searched"]) for r in rows)
    lines = [f"# Seen-inside ledger offline: {len(games)} games, {rec_total} records, {n} logged steps", "",
             "Answer key: a record shows a place's contents when its feedback is \"On the P, you see ...\" or "
             "\"The P is open. In it, you see ...\"; reaching a closed place does not count.", "",
             f"- records right: {rec_right}/{rec_total} ({100 * rec_right / max(1, rec_total):.1f}%), unusable answers {errs}",
             f"- wrong records: " + ", ".join(f"key {a} -> model {b}: {v}" for (a, b), v in confusion.most_common()),
             f"- steps whose not-searched list is exact: {exact}/{n} ({100 * exact / max(1, n):.1f}%)",
             f"- unsearched places the model calls searched (summed over steps): {missing}; searched places it lists as unsearched: {extra}",
             f"- for comparison, places reached but never searched (the 'visited' ledger's blind spot, summed over steps): {arrived_closed}", ""]
    return rows, lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", required=True, choices=["object", "seen"])
    ap.add_argument("--wording", default="both", choices=["plain", "exact", "both"])
    ap.add_argument("--url", default=os.getenv("JEV_URL", "http://127.0.0.1:8000/v1/systemone"))
    ap.add_argument("--model", default=os.getenv("JEV_MODEL") or None)
    ap.add_argument("--limit-games", type=int, default=0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", default=str(ROOT / "runs/jev_checks"))
    a = ap.parse_args()
    out = Path(a.out) / a.check
    out.mkdir(parents=True, exist_ok=True)
    client = Client(a.url, a.model, out / "cache.jsonl")
    if a.check == "object":
        rows, lines = run_object(client, ["plain", "exact"] if a.wording == "both" else [a.wording], a.workers)
    else:
        rows, lines = run_seen(client, a.workers, a.limit_games)
    lines.append(f"Requests: {client.new} new, {client.reused} from cache; {client.seconds:.0f}s in new requests. Server {a.url}.")
    with (out / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
