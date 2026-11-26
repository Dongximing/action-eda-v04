"""Side-by-side wins and steps of the online arms on the same games.

  python scripts/compare_arms.py runs/online/d1 runs/online/more runs/online/more2 runs/online/more3

Reads <dir>/<id>/{d1,t0,hint,mw}.json (each carries the baseline's won/steps for that game)
and writes runs/online/compare.md (or --out). Games missing an arm are reported, and each
arm is compared with the baseline only on the games it has.
"""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

ARMS = [("d1", "D1 (per record, choice)"), ("h1", "H1 (whole history, choice)"),
        ("llm", "LLM (whole history, reasoning)"), ("loop", "LOOP (repeat block)"), ("llmloop", "LLM + LOOP"), ("loop_r3", "LOOP r3"), ("explore", "EXPLORE (unvisited list)"), ("selfexplore", "SELF-EXPLORE (model's list)"), ("onecall", "ONE-CALL (lists + action, one call)"), ("onecall_use", "ONE-CALL-USE (action based on lists)"), ("llmloop_r3", "LLM + LOOP r3"), ("t0", "T0 (rule tracker)"), ("hint", "failure hint"),
        ("mw", "MW (model-written + D1)"), ("mw_v2", "MW-v2 (+ D1)"), ("mw_v2demo", "MW-v2demo (+ D1)")]


def sign_p(better: int, worse: int) -> float | None:
    """Two-sided exact sign test, ties dropped."""
    n = better + worse
    if n == 0:
        return None
    k = min(better, worse)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def load(dirs: list[str]) -> dict[str, dict]:
    games: dict[str, dict] = {}
    for d in dirs:
        for f in sorted(Path(d).glob("*/*.json")):
            if f.stem not in dict(ARMS):
                continue
            r = json.loads(f.read_text())
            g = games.setdefault(r["id"], {"family": r["family"], "baseline": (r["baseline_won"], r["baseline_steps"])})
            g[f.stem] = r
    return games


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", default="runs/online/compare.md")
    a = ap.parse_args()
    games = load(a.dirs)
    lines = [f"# Online arms on {len(games)} ALFWorld games", "",
             "| arm | games | baseline wins | arm wins | rescued | lost | both won: steps base/arm | faster | slower | sign p (steps) | blocked | new actor requests | judge calls |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm, label in ARMS:
        have = {k: g for k, g in games.items() if arm in g}
        if not have:
            continue
        bw = sum(g["baseline"][0] for g in have.values())
        aw = sum(g[arm]["won"] for g in have.values())
        rescued = sorted(k for k, g in have.items() if g[arm]["won"] and not g["baseline"][0])
        lost = sorted(k for k, g in have.items() if g["baseline"][0] and not g[arm]["won"])
        both = [g for g in have.values() if g["baseline"][0] and g[arm]["won"]]
        bs, as_ = sum(g["baseline"][1] for g in both), sum(g[arm]["steps"] for g in both)
        fast = sum(g[arm]["steps"] < g["baseline"][1] for g in both)
        slow = sum(g[arm]["steps"] > g["baseline"][1] for g in both)
        p = sign_p(fast, slow)
        blocked = sum(sum(d["blocked"] for d in g[arm]["decisions"]) for g in have.values())
        actor = sum(g[arm]["usage"]["new_actor_requests"] for g in have.values())
        judge = sum(g[arm]["usage"]["judge"]["calls"] for g in have.values())
        lines.append(f"| {label} | {len(have)} | {bw} | {aw} | {', '.join(rescued) or '-'} | {', '.join(lost) or '-'} | "
                     f"{bs}/{as_} ({len(both)} games) | {fast} | {slow} | {'-' if p is None else f'{p:.3g}'} | "
                     f"{blocked} | {actor} | {judge} |")
    missing = {arm: sorted(k for k, g in games.items() if arm not in g) for arm, _ in ARMS}
    lines += ["", "Missing: " + "; ".join(f"{arm} {len(v)}" for arm, v in missing.items()), "",
              "## Games where any arm's result differs from the baseline", "",
              "| game | family | baseline | " + " | ".join(l for _, l in ARMS) + " |",
              "|---|---|---|" + "---|" * len(ARMS)]

    def cell(won, steps):
        return f"{'win' if won else '-'} {steps}"
    for k in sorted(games):
        g = games[k]
        res = [(g[arm]["won"], g[arm]["steps"]) if arm in g else None for arm, _ in ARMS]
        if all(r is None or r == g["baseline"] for r in res):
            continue
        lines.append(f"| {k} | {g['family'].replace('_then_place_in_recep', '')} | {cell(*g['baseline'])} | "
                     + " | ".join("n/a" if r is None else cell(*r) for r in res) + " |")
    text = "\n".join(lines) + "\n"
    Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
