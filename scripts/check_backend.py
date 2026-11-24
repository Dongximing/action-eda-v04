"""Sanity-check a decision backend before a full run.

Sends every query kind used by the verifiers for the 7 smoke claims (record,
pair, holistic, q_source, q_delta, map_choice, value_check), validates each
answer and prints the per-option probabilities next to what a careful reader
would answer for the per-record items. Nothing is scored; this only checks the
interface and gives a first look at the model's behaviour.

  python scripts/check_backend.py --backend jev --jev-adapter adapters.jev_adapter:choose
  python scripts/check_backend.py --backend hf --model Qwen/Qwen3-4B
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path.cwd()))

from aeda import prompts as P  # noqa: E402
from aeda.backends import HFOptionBackend, AdapterBackend, JevBackend, Query  # noqa: E402
from aeda.schema import load_samples  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# expected per-record reading for the smoke set (cid, rid) -> letter; A establish, B invalidate, C neither
EXPECTED = {("c1", 1): "A", ("c1", 3): "B", ("c1", 5): "A", ("c3", 3): "B",
            ("c4", 1): "A", ("c5", 1): "A", ("c7", 3): "B"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["jev", "api", "hf"], required=True)
    ap.add_argument("--jev-adapter", default=None)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--context-k", type=int, default=0)
    a = ap.parse_args()
    if a.backend == "jev":
        b = JevBackend(a.jev_adapter)
    elif a.backend == "api":
        b = AdapterBackend(a.adapter)
    else:
        if not a.model:
            ap.error("--model is required for --backend hf")
        b = HFOptionBackend(a.model)

    samples = load_samples(ROOT / "data/smoke/samples.jsonl")
    n_ok = n_bad = 0
    agree = 0
    for s in samples:
        for c in s.claims:
            qs = []
            for i, r in enumerate(s.records):
                ctx = s.records[max(0, i - a.context_k):i] if a.context_k else None
                qs.append(Query("record", P.record_judgment(s.task, s.proposed_action, c, r, ctx), cid=c.cid, rids=(r.rid,)))
                qs.append(Query("q_source", P.q_source(s.task, s.proposed_action, c, r), cid=c.cid, rids=(r.rid,)))
                qs.append(Query("q_delta", P.q_delta(s.task, s.proposed_action, c, r), cid=c.cid, rids=(r.rid,)))
            qs.append(Query("holistic", P.holistic_judgment(s.task, s.proposed_action, c, s.records), cid=c.cid))
            if len(s.records) >= 2:
                qs.append(Query("pair", P.pair_judgment(s.task, s.proposed_action, c, s.records[-2], s.records[-1]), cid=c.cid))
            qs.append(Query("map_choice", P.map_claim_choice(c, [("user", "request"), ("item", "status")]), cid=c.cid))
            qs.append(Query("value_check", P.value_check(c, "item", "status", "active", s.records[0].rid), cid=c.cid))
            for q in qs:
                try:
                    p = b.options(q)
                    n_ok += 1
                except Exception as e:  # report and continue so all problems show at once
                    n_bad += 1
                    print(f"[FAIL] {q.kind} {c.cid} {q.rids}: {type(e).__name__}: {e}")
                    continue
                if q.kind == "record":
                    exp = EXPECTED.get((c.cid, q.rids[0]))
                    got = max(p, key=p.get)
                    if exp:
                        agree += got == exp
                    flag = "" if exp is None else ("  ok" if got == exp else f"  expected {exp}")
                    rec = next(r for r in s.records if r.rid == q.rids[0])
                    print(f"{c.cid} #{rec.rid} {rec.text[:28]:<28} " +
                          " ".join(f"{k}={v:.2f}" for k, v in p.items()) + flag)
    print(json.dumps({"backend": b.name, "answers_ok": n_ok, "answers_failed": n_bad,
                      "record_agreement": f"{agree}/{len(EXPECTED)}", "usage": b.usage.as_dict()},
                     ensure_ascii=False))
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
