#!/usr/bin/env python3
"""Offline check: can a Jev-style decision model keep the visited / not-visited place lists of selfexplore?

No game is played. Every step that the selfexplore arm logged (runs/online/*/<id>/selfexplore.json,
field place_lists) has the visible history and the code-derived answer (code_visited / code_not_visited,
from "You arrive at <place>"). The decision model answers questions about that same history, and its lists
are scored exactly like the 9B model's lists (run_online.place_list_score), on the same steps.

Two ways of asking (--mode):

  perplace     one request per logged step: state = the whole history so far; one yes/no question
               ("noul") per place named in the opening observation r0. P(yes) >= 0.5 -> visited.
  incremental  one request per record of the game: state = that record only (command + feedback);
               one choice question, options = the places of r0 plus "none". The chosen places are
               accumulated in order, so the lists at step k are the choices on records 1..k.

The candidate places are the ones the code finds in r0 (both modes), so this measures the visited /
not-visited judgment only. In an online arm the place names would come from one 9B call per game.

The model is reached through the System One HTTP API (TypeSafe Jev, or a local Flide server):

  flide serve --model <path to OneJev1.6-4B>          # in another terminal, serves localhost:8000
  python scripts/jev_places_offline.py --mode incremental
  python scripts/jev_places_offline.py --mode perplace --limit-games 10

  --url       default http://localhost:8000/v1/systemone (env JEV_URL)
  --model     sent as "model" only when given (the TypeSafe cloud needs it, e.g. jev-1.14.0)
  TYPESAFE_API_KEY / JEV_API_KEY, if set, is sent as a Bearer token.

Answers are cached in <out>/<mode>/cache.jsonl (keyed by the request), so a rerun resumes.
Writes <out>/<mode>/report.md and steps.jsonl (default out: runs/jev_places).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRS = [ROOT / "runs/online" / d for d in ("d1", "more", "more2", "more3")]
_PLACE = re.compile(r"\b([a-z]+ \d+)\b")
RETRY = {408, 429, 500, 502, 503, 504}

# Wording follows SELF_PLACES in run_online.py (no ALFWorld knowledge beyond it).
PERPLACE_STATE_NOTE = ("Interaction history: each record is a command and the environment's feedback, oldest first; "
                       "record r0 is the opening observation.")
PERPLACE_Q = "The agent has arrived at {place} in a record after r0."
INCR_Q = ("The record is a command and the environment's feedback. Which of these places did the agent arrive at "
          "with this command? Choose none if it did not arrive at any of them.")


# ------------------------------------------------------------------ data (same definitions as run_online)

def code_places(history: list[dict]) -> tuple[list[str], list[str]]:
    """Copy of run_online.places: (places named in r0, places visited so far)."""
    start = history[0]["observation"].lower().split("your task is to")[0]
    listed = list(dict.fromkeys(_PLACE.findall(start)))
    visited = []
    for h in history[1:]:
        m = re.match(r"you arrive at ([a-z]+ \d+)", h["observation"].strip().lower())
        if m and m.group(1) not in visited:
            visited.append(m.group(1))
    return listed, visited


def records(history: list[dict]) -> list[dict]:
    return [{k: h[k] for k in ("id", "action", "observation")} for h in history]


def load_games(dirs: list[Path], limit: int = 0) -> list[dict]:
    games = []
    for d in dirs:
        for f in sorted(d.glob("*/selfexplore.json")):
            r = json.loads(f.read_text())
            games.append({"folder": d.name, "id": r["id"], "history": r["history"], "place_lists": r["place_lists"]})
    return games[:limit] if limit else games


def score(entries: list[dict]) -> dict:
    """Same counts as run_online.place_list_score: exact = not-visited set equals the code's."""
    ok = [e for e in entries if "error" not in e]
    return {"steps": len(entries), "errors": len(entries) - len(ok),
            "exact": sum(set(e["model_not_visited"]) == set(e["code_not_visited"]) for e in ok),
            "missing": sum(len(set(e["code_not_visited"]) - set(e["model_not_visited"])) for e in ok),
            "extra": sum(len(set(e["model_not_visited"]) - set(e["code_not_visited"])) for e in ok)}


# ------------------------------------------------------------------ System One client with a request cache

class Client:
    def __init__(self, url: str, model: str | None, cache: Path, timeout: float = 300):
        self.url, self.model, self.timeout = url, model, timeout
        key = (os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY") or "").strip()
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if key:
            self.headers["Authorization"] = f"Bearer {key}"
        self.cache_path = cache
        self.cache: dict[str, dict] = {}
        if cache.exists():
            for line in cache.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.cache[row["key"]] = row["response"]
        self.lock = threading.Lock()
        self.new = self.reused = 0
        self.seconds = 0.0

    def ask(self, state: dict, questions: dict) -> dict:
        payload = {"state": state, "questions": questions}
        if self.model:
            payload["model"] = self.model
        key = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        with self.lock:
            if key in self.cache:
                self.reused += 1
                return self.cache[key]
        t = time.time()
        resp = self._post(payload)
        with self.lock:
            self.seconds += time.time() - t
            self.new += 1
            self.cache[key] = resp
            with self.cache_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"key": key, "response": resp}, ensure_ascii=False) + "\n")
        return resp

    def _post(self, payload: dict, attempts: int = 6) -> dict:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        for i in range(attempts):
            req = urllib.request.Request(self.url, data=data, headers=self.headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                body = e.read()[:300].decode("utf-8", "replace") if e.fp else ""
                if e.code in (401, 402, 403):
                    sys.exit(f"HTTP {e.code} from {self.url}: check the key, balance or model access")
                if e.code not in RETRY or i + 1 == attempts:
                    raise RuntimeError(f"HTTP {e.code} from {self.url}: {body}") from None
                time.sleep(min(60, 2 ** i))
            except (OSError, json.JSONDecodeError) as e:
                if i + 1 == attempts:
                    raise RuntimeError(f"cannot reach {self.url} ({type(e).__name__}: {e}); "
                                       "is the server running?") from None
                time.sleep(2 ** i)
        raise RuntimeError("unreachable")


def yes_prob(answer: dict) -> float:
    v = answer.get("noul") if isinstance(answer, dict) else None
    if isinstance(v, dict):  # tolerate {"noul": {"yes": p}} style
        v = v.get("yes", v.get("probability"))
    if not isinstance(v, (int, float)):
        raise ValueError(f"no yes-probability in answer {str(answer)[:200]}")
    return float(v)


def choice_of(answer: dict, labels: list[str]) -> str:
    p = answer.get("probabilities") if isinstance(answer, dict) else None
    if isinstance(p, dict) and p and set(p) <= set(labels):
        return max(p, key=lambda k: float(p[k]))
    if isinstance(p, list) and len(p) == len(labels):
        return labels[max(range(len(p)), key=lambda i: float(p[i]))]
    c = answer.get("choice") if isinstance(answer, dict) else None
    if isinstance(c, str) and c.strip() in labels:
        return c.strip()
    raise ValueError(f"no usable choice in answer {str(answer)[:200]}")


# ------------------------------------------------------------------ the two ways of asking

def run_perplace(game: dict, client: Client) -> list[dict]:
    out = []
    for e in game["place_lists"]:
        prefix = game["history"][: e["step"] + 1]
        listed, visited = code_places(prefix)
        assert (visited, [p for p in listed if p not in visited]) == (e["code_visited"], e["code_not_visited"]), game["id"]
        qs = {f"p{i}": {"type": "noul", "instructions": PERPLACE_Q.format(place=p)} for i, p in enumerate(listed)}
        row = {"folder": game["folder"], "id": game["id"], "step": e["step"],
               "code_visited": e["code_visited"], "code_not_visited": e["code_not_visited"]}
        try:
            resp = client.ask({"note": PERPLACE_STATE_NOTE, "history": records(prefix)}, qs)
            ans = resp["answers"]
            probs = {p: yes_prob(ans[f"p{i}"]) for i, p in enumerate(listed)}
        except (KeyError, TypeError, ValueError) as err:
            row["error"] = f"{type(err).__name__}: {err}"
            out.append(row)
            continue
        row.update(model_visited=[p for p in listed if probs[p] >= 0.5],
                   model_not_visited=[p for p in listed if probs[p] < 0.5], p_yes=probs)
        out.append(row)
    return out


def run_incremental(game: dict, client: Client) -> list[dict]:
    hist = game["history"]
    listed, _ = code_places(hist[:1])
    labels = listed + ["none"]
    crit = {p: p for p in listed}
    crit["none"] = "none of these places"
    arrived: dict[int, str | None] = {}  # record index -> chosen place (None = none / error)
    errors: dict[int, str] = {}
    last = max([e["step"] for e in game["place_lists"]], default=0)
    for k in range(1, last + 1):
        rec = {kk: hist[k][kk] for kk in ("action", "observation")}
        try:
            resp = client.ask({"record": rec}, {"arrived": {"type": "choice", "instructions": INCR_Q, "criteria": crit}})
            c = choice_of(resp["answers"]["arrived"], labels)
        except (KeyError, TypeError, ValueError) as err:
            errors[k] = f"{type(err).__name__}: {err}"
            c = "none"
        arrived[k] = None if c == "none" else c
    out = []
    for e in game["place_lists"]:
        vis = list(dict.fromkeys(p for k in range(1, e["step"] + 1) if (p := arrived.get(k))))
        row = {"folder": game["folder"], "id": game["id"], "step": e["step"],
               "code_visited": e["code_visited"], "code_not_visited": e["code_not_visited"],
               "model_visited": vis, "model_not_visited": [p for p in listed if p not in vis],
               "record_errors": sum(1 for k in errors if k <= e["step"])}
        out.append(row)
    return out


# ------------------------------------------------------------------ report

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True, choices=["perplace", "incremental"])
    ap.add_argument("--url", default=os.getenv("JEV_URL", "http://localhost:8000/v1/systemone"))
    ap.add_argument("--model", default=os.getenv("JEV_MODEL") or None)
    ap.add_argument("--limit-games", type=int, default=0, help="only the first N games (0 = all 68)")
    ap.add_argument("--workers", type=int, default=1, help="games in parallel (requests in flight)")
    ap.add_argument("--out", default=str(ROOT / "runs/jev_places"))
    a = ap.parse_args()

    out = Path(a.out) / a.mode
    out.mkdir(parents=True, exist_ok=True)
    games = load_games(DIRS, a.limit_games)
    client = Client(a.url, a.model, out / "cache.jsonl")
    fn = run_perplace if a.mode == "perplace" else run_incremental
    print(f"{len(games)} games, mode {a.mode}, {a.url}", flush=True)
    rows: list[dict] = []
    done = [0]

    def one(g):
        r = fn(g, client)
        with client.lock:
            done[0] += 1
            n = client.new
            per = client.seconds / n if n else 0
        print(f"[{done[0]}/{len(games)}] {g['folder']}/{g['id']}: {sum(set(x.get('model_not_visited', [None])) == set(x['code_not_visited']) for x in r)}/{len(r)} steps exact"
              f"  (new requests {n}, {per:.1f}s each)", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        for r in ex.map(one, games):
            rows.extend(r)

    with (out / "steps.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    keys = {(r["folder"], r["id"], r["step"]) for r in rows}
    nine_b = [dict(e, folder=g["folder"], id=g["id"]) for g in games for e in g["place_lists"]
              if (g["folder"], g["id"], e["step"]) in keys]
    jev, base = score(rows), score(nine_b)

    def line(name, s):
        n = s["steps"]
        return (f"| {name} | {n} | {s['errors']} | {s['exact']} ({100 * s['exact'] / n:.1f}%) | "
                f"{s['missing']} | {s['extra']} |")
    model = a.model or "local server"
    text = "\n".join([
        f"# Place lists offline: decision model ({a.mode}) vs the 9B model's own lists", "",
        f"Server {a.url}, model {model}. {len(games)} games, {len(rows)} logged selfexplore steps. "
        "Answer key: the code's lists from \"You arrive at <place>\" (code_visited / code_not_visited).", "",
        "| who writes the lists | steps | unusable answers | not-visited list exact | missing (unvisited places left out) | extra (visited places listed as unvisited) |",
        "|---|---|---|---|---|---|",
        line(f"decision model, {a.mode}", jev),
        line("qwen3.5-9b (selfexplore, logged)", base), "",
        f"Requests: {client.new} new, {client.reused} from cache; {client.seconds:.0f}s in new requests."]
        + (["An unusable answer on a record counts as \"none\" for that record "
            f"({sum(r.get('record_errors', 0) > 0 for r in rows)} steps affected)."] if a.mode == "incremental" else [])
        + [""])
    (out / "report.md").write_text(text, encoding="utf-8")
    print("\n" + text)


if __name__ == "__main__":
    main()
