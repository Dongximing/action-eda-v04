"""Data schema for offline pre-action verification samples.

Visible input (Sample) and private labels (Label) live in separate files so that
no verifier can read gold information (design doc v0.4 §6.4).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal

ClaimKind = Literal["state", "default"]
ClaimOrigin = Literal["fixed", "dynamic"]
Verdict3 = Literal["SUPPORTED", "CONTRADICTED", "UNKNOWN"]
# Verifier outputs may additionally use SUPPORTED_DEFAULT (doc §3.2).
VerdictOut = Literal["SUPPORTED", "SUPPORTED_DEFAULT", "CONTRADICTED", "UNKNOWN"]


@dataclass
class Record:
    rid: int                      # position in the history, strictly increasing
    source: str                   # "user" | "env" | "tool" | "agent" ...; agent thoughts are not env facts
    text: str
    entities: list[str] = field(default_factory=list)  # optional, used only by entity-filtered variants


@dataclass
class Claim:
    cid: str
    text: str
    kind: ClaimKind = "state"
    origin: ClaimOrigin = "fixed"
    entities: list[str] = field(default_factory=list)
    # Optional machine-checkable form for a deterministic tracker (T0), e.g.
    # {"type": "at", "loc": "sinkbasin 1"}. It restates the public precondition,
    # it is not a label.
    spec: dict | None = None


@dataclass
class Sample:
    sid: str
    episode_id: str               # grouping unit for splits and bootstrap
    task: str
    proposed_action: str
    action_reversible: bool
    records: list[Record]         # history prefix strictly before the proposed action
    claims: list[Claim]
    window_complete: bool = True  # whether the visible history covers the whole relevant interval

    @staticmethod
    def from_dict(d: dict) -> "Sample":
        return Sample(
            sid=d["sid"],
            episode_id=d["episode_id"],
            task=d["task"],
            proposed_action=d["proposed_action"],
            action_reversible=d["action_reversible"],
            records=[Record(**r) for r in d["records"]],
            claims=[Claim(**c) for c in d["claims"]],
            window_complete=d.get("window_complete", True),
        )


@dataclass
class Label:
    sid: str
    cid: str
    gold: Verdict3
    # Strata for analysis (doc §5.4). Missing keys are treated as unknown.
    order_sensitive: bool | None = None
    composition: bool | None = None
    indirect: bool | None = None
    implicit_order: bool | None = None
    synthetic: bool = False
    extra: dict = field(default_factory=dict)


def read_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_samples(path: str | Path) -> list[Sample]:
    samples = [Sample.from_dict(d) for d in read_jsonl(path)]
    for s in samples:
        rids = [r.rid for r in s.records]
        if rids != sorted(rids) or len(set(rids)) != len(rids):
            raise ValueError(f"sample {s.sid}: record ids must be strictly increasing")
    # Unknown keys (e.g. a stray "gold" field) already fail in Record(**)/Claim(**),
    # which keeps label information out of the visible input.
    return samples


def load_labels(path: str | Path) -> dict[tuple[str, str], Label]:
    out = {}
    for d in read_jsonl(path):
        lab = Label(**d)
        out[(lab.sid, lab.cid)] = lab
    return out
