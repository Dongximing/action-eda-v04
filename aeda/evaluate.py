"""Stratified metrics and grouped-bootstrap paired differences (doc v0.4 §6.1-6.2)."""
from __future__ import annotations

import random
from collections import defaultdict

from .schema import Label, Sample

DEFAULT_PAIRS = [("D1", "U1"), ("D1", "H2"), ("D1", "H1"), ("D1", "E1"),
                 ("D2", "D1"), ("D1", "D1f"), ("H2", "U1"), ("D1", "P0"), ("D1", "Q0"), ("D1", "T0")]


def norm_pred(v: str) -> str:
    return "SUPPORTED" if v == "SUPPORTED_DEFAULT" else v


def strata_of(lab: Label, claim_meta: dict) -> dict[str, str]:
    st = {"all": "all", "kind": claim_meta["kind"], "origin": claim_meta["origin"],
          "synthetic": str(lab.synthetic)}
    for k in ("order_sensitive", "composition", "indirect", "implicit_order"):
        v = getattr(lab, k)
        st[k] = "?" if v is None else str(v)
    # optional strata written by data builders (e.g. make_diagnostic.py)
    for k in ("cell", "n_distract", "ref", "lang", "domain", "label_source"):
        if k in lab.extra:
            st[k] = str(lab.extra[k])
    return st


def metrics(rows: list[tuple[dict, Label]]) -> dict:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    acc3 = sum(norm_pred(r["verdict"]) == l.gold for r, l in rows) / n
    dec = [(norm_pred(r["verdict"]), l.gold) for r, l in rows if l.gold != "UNKNOWN"]
    tp = sum(p == "CONTRADICTED" and g == "CONTRADICTED" for p, g in dec)
    fp = sum(p == "CONTRADICTED" and g == "SUPPORTED" for p, g in dec)
    fn = sum(p != "CONTRADICTED" and g == "CONTRADICTED" for p, g in dec)
    n_sup = sum(g == "SUPPORTED" for _, g in dec)
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    f1 = 2 * prec * rec / (prec + rec) if prec and rec else None
    return {
        "n": n,
        "n_decidable": len(dec),
        "acc3": acc3,
        "acc_decidable": (sum(p == g for p, g in dec) / len(dec)) if dec else None,
        "contra_precision": prec,
        "contra_recall": rec,
        "contra_f1": f1,
        "false_block_rate": fp / n_sup if n_sup else None,
        "unknown_rate": sum(r["verdict"] == "UNKNOWN" for r, _ in rows) / n,
        "default_rate": sum(r["verdict"] == "SUPPORTED_DEFAULT" for r, _ in rows) / n,
        "mean_calls": sum(r["calls"] for r, _ in rows) / n,
        "errors": sum("error" in r for r, _ in rows),
    }


def join(preds: list[dict], labels: dict, samples: list[Sample]):
    meta = {(s.sid, c.cid): {"kind": c.kind, "origin": c.origin, "episode": s.episode_id}
            for s in samples for c in s.claims}
    out = defaultdict(list)  # method -> [(row, label, meta)]
    missing = 0
    for r in preds:
        key = (r["sid"], r["cid"])
        if key not in labels:
            missing += 1
            continue
        out[r["method"]].append((r, labels[key], meta[key]))
    return out, missing


def stratified_table(joined) -> list[dict]:
    table = []
    for meth, items in joined.items():
        groups = defaultdict(list)
        for r, l, mt in items:
            for dim, val in strata_of(l, mt).items():
                groups[(dim, val)].append((r, l))
        for (dim, val), rows in sorted(groups.items()):
            table.append({"method": meth, "stratum": dim, "value": val, **metrics(rows)})
    return table


def paired_bootstrap(joined, a: str, b: str, stratum: tuple[str, str] = ("all", "all"),
                     n_boot: int = 2000, seed: int = 0) -> dict | None:
    """Difference in decidable accuracy (a - b), resampling episodes."""
    if a not in joined or b not in joined:
        return None
    dim, val = stratum

    def per_claim(meth):
        d = {}
        for r, l, mt in joined[meth]:
            if l.gold == "UNKNOWN" or strata_of(l, mt).get(dim) != val:
                continue
            d[(r["sid"], r["cid"])] = (mt["episode"], float(norm_pred(r["verdict"]) == l.gold))
        return d

    da, db = per_claim(a), per_claim(b)
    keys = sorted(da.keys() & db.keys())
    if not keys:
        return None
    by_ep = defaultdict(list)
    for k in keys:
        by_ep[da[k][0]].append(da[k][1] - db[k][1])
    eps = sorted(by_ep)
    point = sum(sum(v) for v in by_ep.values()) / len(keys)
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        pick = [eps[rng.randrange(len(eps))] for _ in eps]
        tot = sum(sum(by_ep[e]) for e in pick)
        cnt = sum(len(by_ep[e]) for e in pick)
        boots.append(tot / cnt)
    boots.sort()
    lo, hi = boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]
    return {"a": a, "b": b, "stratum": f"{dim}={val}", "n_claims": len(keys),
            "n_episodes": len(eps), "diff": point, "ci95": [lo, hi]}


def fmt(x) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def to_markdown(table: list[dict], diffs: list[dict]) -> str:
    cols = ["method", "stratum", "value", "n", "n_decidable", "acc3", "acc_decidable",
            "contra_precision", "contra_recall", "false_block_rate", "unknown_rate",
            "default_rate", "mean_calls", "errors"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in table:
        lines.append("| " + " | ".join(fmt(row.get(c)) for c in cols) + " |")
    lines += ["", "| a | b | stratum | n_claims | n_episodes | diff (a-b) | 95% CI |", "|---|---|---|---|---|---|---|"]
    for d in diffs:
        lines.append(f"| {d['a']} | {d['b']} | {d['stratum']} | {d['n_claims']} | {d['n_episodes']} | "
                     f"{d['diff']:.3f} | [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}] |")
    return "\n".join(lines)
