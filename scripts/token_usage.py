#!/usr/bin/env python3
"""Tokens each arm needs per game, as if every call were made fresh (cache hits counted at the size of the
original request). No API calls: everything is read from <dir>/<id>/calls.sqlite and <arm>.json.

  python scripts/token_usage.py runs/online/d1 --arms baseline,selfexplore,jevexplore

For each game and arm the calls of the arm's last complete run are taken from the cache log: the run starts at
the last occurrence of the arm's first request (the step-0 request, identical in every run of the arm), and each
request (cache key) is counted once. A cache
hit carries no token counts, so it is counted with the counts of the request that produced the answer (same key).
A failed request (e.g. an answer cut off at the output limit) is counted with its own tokens.
"baseline" is the scope "direct" (the baseline's own run, copied from baseline/oneshot12 for the d1 games).

Agent model (qwen3.5-9b): requests, input / output tokens, cost in USD as OpenRouter reported it.
Decision model (role "jev", jevexplore): requests and input tokens (the server's prompt tokens; one answer
token per question).

Only games that have every listed arm are compared. Writes <out> (default: <first dir>/tokens.md).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

SCOPE = {"baseline": "direct"}


def last_run(db: sqlite3.Connection, scope: str) -> list[tuple]:
    rows = db.execute("SELECT id, role, operation, key, reused, ok FROM requests WHERE scope=? ORDER BY id",
                      (scope,)).fetchall()
    if not rows:
        return []
    k0 = rows[0][3]
    start = max(i for i, r in enumerate(rows) if r[3] == k0)
    seen, out = set(), []
    for r in rows[start:]:   # each answer once (the baseline's own run also replayed its steps from the cache)
        if r[5] == 0:        # a failed request: never cached, its tokens were spent all the same
            out.append(r)
        elif r[1] == "jev" or r[3] not in seen:   # the same record can come up again in a game: each time a request
            seen.add(r[3])
            out.append(r)
    return out


def tokens_of(db: sqlite3.Connection, key: str, row_id: int | None = None) -> dict:
    """Tokens of the request that produced the answer for `key`, or of the failed request `row_id`."""
    row = (db.execute("SELECT transport FROM requests WHERE id=?", (row_id,)) if row_id is not None else
           db.execute("SELECT transport FROM requests WHERE key=? AND reused=0 AND ok=1 ORDER BY id LIMIT 1",
                      (key,))).fetchone()
    out = {"in": 0, "out": 0, "usd": 0.0, "known": row is not None}
    for call in (json.loads(row[0]) if row else []):   # every attempt (e.g. a retry with a larger output limit)
        out["in"] += call.get("input_tokens") or 0
        out["out"] += call.get("output_tokens") or 0
        out["usd"] += call.get("cost_usd") or 0.0
    return out


def game_usage(folder: Path, arm: str) -> dict:
    db = sqlite3.connect(f"file:{folder / 'calls.sqlite'}?mode=ro", uri=True)
    u = {"qwen_calls": 0, "qwen_in": 0, "qwen_out": 0, "usd": 0.0, "jev_calls": 0, "jev_in": 0, "unknown": 0,
         "by_op": {}}
    for rid, role, op, key, _, ok in last_run(db, SCOPE.get(arm, arm)):
        t = tokens_of(db, key, None if ok else rid)
        u["failed"] = u.get("failed", 0) + (not ok)
        u["unknown"] += not t["known"]
        if role == "jev":
            u["jev_calls"] += 1
            u["jev_in"] += t["in"]
        else:
            u["qwen_calls"] += 1
            u["qwen_in"] += t["in"]
            u["qwen_out"] += t["out"]
            u["usd"] += t["usd"]
        b = u["by_op"].setdefault(op, [0, 0, 0])
        b[0] += 1
        b[1] += t["in"]
        b[2] += t["out"]
    db.close()
    return u


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--arms", default="baseline,selfexplore,jevexplore")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    arms = a.arms.split(",")
    games = {}
    for d in a.dirs:
        for folder in sorted(p for p in Path(d).iterdir() if (p / "calls.sqlite").exists()):
            res = {}
            for arm in arms:
                if arm == "baseline":
                    any_arm = next((json.loads(f.read_text()) for f in sorted(folder.glob("*.json"))
                                    if f.stem not in ("direct",) and "baseline_won" in f.read_text()[:2000]), None)
                    if any_arm:
                        res[arm] = {"won": any_arm["baseline_won"], "steps": any_arm["baseline_steps"]}
                elif (folder / f"{arm}.json").exists():
                    r = json.loads((folder / f"{arm}.json").read_text())
                    res[arm] = {"won": r["won"], "steps": r["steps"]}
            if len(res) == len(arms):
                for arm in arms:
                    res[arm].update(game_usage(folder, arm))
                games[f"{Path(d).name}/{folder.name}"] = res
    if not games:
        raise SystemExit("no game has all of: " + ", ".join(arms))

    def tot(arm, k):
        return sum(g[arm][k] for g in games.values())
    base_in = tot(arms[0], "qwen_in") + tot(arms[0], "qwen_out")
    lines = [f"# Tokens per arm on {len(games)} games ({', '.join(a.dirs)})", "",
             "Every call counted as if made fresh (cache hits at the size of the original request). "
             f"Ratios are against {arms[0]}.", "",
             "| arm | wins | steps | 9B requests | 9B input tokens | 9B output tokens | 9B tokens vs " + arms[0] +
             " | 9B cost (USD) | decision-model requests | decision-model input tokens | failed requests (counted) | calls with no token record |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm in arms:
        q = tot(arm, "qwen_in") + tot(arm, "qwen_out")
        lines.append(f"| {arm} | {sum(g[arm]['won'] for g in games.values())} | {tot(arm, 'steps')} | "
                     f"{tot(arm, 'qwen_calls')} | {tot(arm, 'qwen_in'):,} | {tot(arm, 'qwen_out'):,} | "
                     f"{q / base_in:.2f}x | {tot(arm, 'usd'):.4f} | {tot(arm, 'jev_calls')} | {tot(arm, 'jev_in'):,} | "
                     f"{sum(g[arm].get('failed', 0) for g in games.values())} | {tot(arm, 'unknown')} |")
    lines += ["", "## Per operation (all games)", "", "| arm | operation | requests | input tokens | output tokens |",
              "|---|---|---|---|---|"]
    for arm in arms:
        ops = {}
        for g in games.values():
            for op, (n, i, o) in g[arm]["by_op"].items():
                s = ops.setdefault(op, [0, 0, 0])
                s[0] += n
                s[1] += i
                s[2] += o
        for op, (n, i, o) in sorted(ops.items()):
            lines.append(f"| {arm} | {op} | {n} | {i:,} | {o:,} |")
    lines += ["", "## Per game", "", "| game | " + " | ".join(f"{arm} (win, steps, 9B tokens)" for arm in arms) + " |",
              "|---|" + "---|" * len(arms)]
    for k, g in games.items():
        lines.append(f"| {k} | " + " | ".join(
            f"{'win' if g[arm]['won'] else '-'} {g[arm]['steps']} {g[arm]['qwen_in'] + g[arm]['qwen_out']:,}"
            for arm in arms) + " |")
    text = "\n".join(lines) + "\n"
    out = Path(a.out) if a.out else Path(a.dirs[0]) / "tokens.md"
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
