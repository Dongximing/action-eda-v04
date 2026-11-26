"""Experiment-local, per-game record of actual model responses and execution costs."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections import defaultdict


TOKEN_FIELDS = ("input_tokens", "output_tokens", "total_tokens")


def token_totals(rows):
    """Missing measurements propagate. An empty collection means zero measured requests."""
    rows = list(rows)
    totals = {field: (None if any(row[field] is None for row in rows)
                      else sum(row[field] for row in rows)) for field in TOKEN_FIELDS}
    return {"requests": sum(r["requests"] for r in rows),
            "requests_missing_usage": sum(r["requests_missing_usage"] for r in rows), **totals}


def response_tokens(log):
    inp, out = log.get("input_tokens"), log.get("output_tokens")
    total = log.get("total_tokens")
    if total is None and inp is not None and out is not None:
        total = inp + out
    return {"requests": 1, "requests_missing_usage": int(None in (inp, out, total)),
            "input_tokens": inp, "output_tokens": out, "total_tokens": total}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


def freeze(path, value):
    if not path.exists():
        save(path, value)
    elif canonical(load(path)) != canonical(value):
        raise ValueError(f"Frozen experiment input differs: {path}. Choose a fresh run directory.")


class CallBook:
    """Reuse a decision only for an identical model, operation and public input in this game."""
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS answers (key TEXT PRIMARY KEY, answer TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY, scope TEXT, role TEXT, operation TEXT, key TEXT, reused INTEGER,
                ok INTEGER, transport TEXT, error TEXT);
            CREATE INDEX IF NOT EXISTS request_origin ON requests(key) WHERE reused=0 AND ok=1;
        """)

    def last_request_id(self):
        return self.db.execute("SELECT COALESCE(MAX(id),0) FROM requests").fetchone()[0]

    def standalone_tokens(self, shared_actor_ids, after=None):
        """Price an arm running with its own cache. Shared prompts count once in each arm that needs them."""
        shared = list(shared_actor_ids)
        conditions, args = [], []
        if shared:
            conditions.append("r.id IN (" + ",".join("?" for _ in shared) + ")")
            args.extend(shared)
        if after is not None:
            conditions.append("r.id > ?")
            args.append(after)
        by_op = defaultdict(list)
        if conditions:
            query = """SELECT DISTINCT original.id, r.operation, original.transport FROM requests r
                JOIN requests original ON original.key=r.key AND original.reused=0 AND original.ok=1
                WHERE r.ok=1 AND (""" + " OR ".join(conditions) + ") ORDER BY original.id"
            for _, op, raw in self.db.execute(query, args):
                calls = json.loads(raw) or [{}]
                by_op[op].extend(response_tokens(c) for c in calls)
        breakdown = {op: token_totals(rows) for op, rows in by_op.items()}
        return {"totals": token_totals(breakdown.values()), "by_operation": breakdown}

    def ask(self, scope, role, operation, inputs, client, perform):
        key = digest([role, client.model, operation, inputs])
        cached = self.db.execute("SELECT answer FROM answers WHERE key=?", (key,)).fetchone()
        row = (scope, role, operation, key)
        if cached is not None:
            with self.db:
                self.db.execute("INSERT INTO requests VALUES(NULL,?,?,?,?,1,1,'[]',NULL)", row)
            return json.loads(cached[0])
        mark = len(client.calls)
        try:
            answer = perform()
        except Exception as error:
            with self.db:
                self.db.execute("INSERT INTO requests VALUES(NULL,?,?,?,?,0,0,?,?)",
                                (*row, canonical(client.calls[mark:]), type(error).__name__))
            raise
        with self.db:
            self.db.execute("INSERT INTO answers VALUES(?,?)", (key, canonical(answer)))
            self.db.execute("INSERT INTO requests VALUES(NULL,?,?,?,?,0,1,?,NULL)",
                            (*row, canonical(client.calls[mark:])))
        return answer

    def close(self):
        self.db.close()


def physical_usage(path):
    groups = {}
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='requests' AND type='table'").fetchone():
            return groups
        for scope, role, ok, raw in db.execute("SELECT scope, role, ok, transport FROM requests WHERE reused=0"):
            group = groups.setdefault((scope, role), {"attempts": 0, "failed_decisions": 0,
                "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                "input_reports": 0, "output_reports": 0, "total_reports": 0, "transport_records": 0,
                "reported_usd": 0.0, "cost_reports": 0, "seconds": 0.0})
            group["failed_decisions"] += int(not ok)
            for call in json.loads(raw):
                metered = response_tokens(call)
                group["transport_records"] += 1
                group["attempts"] += call["attempts"]
                for side in ("input", "output", "total"):
                    value = metered[f"{side}_tokens"]
                    if value is not None:
                        group[f"{side}_tokens"] += value
                        group[f"{side}_reports"] += 1
                group["seconds"] += call["seconds"]
                if "cost_usd" in call:
                    group["reported_usd"] += call["cost_usd"]
                    group["cost_reports"] += 1
    return groups
