"""Verifiers compared in design doc v0.4 §6.1.

All methods take the same Sample, the same Claim and the same backend, and return
a verdict in {SUPPORTED, SUPPORTED_DEFAULT, CONTRADICTED, UNKNOWN}.

  H1   holistic judgment over the full history
  H2   holistic judgment over the entity-filtered window (same records as D1f)
  U1   per-record judgments, order-free max aggregation (SummaC-style)
  D1   per-record judgments, ordered aggregation (latest decisive record wins)
  D1f  D1 restricted to the entity-filtered window (cost-saving variant)
  D2   D1 + pairwise repair for composition-type invalidation
  E1   claim-agnostic extraction per record + latest-wins tracking in code
  P0   presence-only: is there any entity-matching record after the latest source
  Q0   original EDA: binary Q-source / Q-delta and max(-log-odds)
  T0   deterministic tracker; only for claims with a machine spec (ALFWorld), no model calls

Not implemented: G1 (BlackSwan-style agentic verification with probes, needs a live environment).
"""
from __future__ import annotations

import functools
import itertools
import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import alfworld
from . import prompts as P
from .backends import DecisionBackend, Generator, Query
from .schema import Claim, Record, Sample


@dataclass
class Config:
    tau_conf: float = 0.5      # min probability for a record/pair to be decisive
    tau_low: float = 0.15      # D2: weak-invalidation band [tau_low, tau_high)
    tau_high: float = 0.5
    max_pairs: int = 6         # D2: pair budget M per claim
    tau_q0: float = 0.0        # Q0: CONTRADICTED if max(-logit(P(still true))) > tau_q0
    early_stop: bool = True    # D1: backward scan stops once the decision is fixed
    context_k: int = 0         # preceding records shown (context only) in per-record judgments;
                               # applies equally to D1/D1f/D2/U1/P0 and E1 extraction, not to Q0 (original EDA)
    fewshot: str = ""          # JSON file of worked examples for the per-record judgment (D1/D1f/D2/U1/P0);
                               # "" = zero-shot. See scripts/make_fewshot.py


@dataclass
class Result:
    method: str
    sid: str
    cid: str
    verdict: str
    evidence: list[int] = field(default_factory=list)
    calls: int = 0             # logical model calls issued by this method for this claim
    prompt_chars: int = 0
    trace: dict = field(default_factory=dict)


class Meter:
    """Counts logical calls per method even when a backend serves from cache.
    Decision queries go to the decision backend, generation to the generator."""

    def __init__(self, backend: DecisionBackend, generator: Generator | None = None):
        self.b = backend
        self.g = generator
        self.calls = 0
        self.gen_calls = 0
        self.chars = 0

    def options(self, q: Query) -> dict[str, float]:
        self.calls += 1
        self.chars += len(q.prompt)
        return self.b.options(q)

    def generate(self, q: Query) -> str:
        if self.g is None:
            raise RuntimeError("this method needs a generator (--gen-model); the decision model does not generate")
        self.gen_calls += 1
        self.chars += len(q.prompt)
        return self.g.generate(q)


# ---------------------------------------------------------------- helpers

def no_evidence(s: Sample, c: Claim) -> str:
    """Verdict when no record bears on the claim (doc §3.2)."""
    if c.kind == "default" and s.window_complete:
        return "SUPPORTED_DEFAULT"
    return "UNKNOWN"


def entity_window(s: Sample, c: Claim) -> list[Record]:
    ents = [e.lower() for e in c.entities]
    if not ents:
        return list(s.records)
    out = []
    pats = [re.compile(rf"(?<![A-Za-z0-9_]){re.escape(e)}(?![A-Za-z0-9_])") for e in ents]
    for r in s.records:
        tags = {e.lower() for e in r.entities}
        if tags & set(ents) or any(p.search(r.text.lower()) for p in pats):
            out.append(r)
    return out


def preceding(s: Sample, r: Record, k: int) -> list[Record]:
    """The k records right before r in the full history (not the filtered window)."""
    if k <= 0:
        return []
    idx = next(i for i, x in enumerate(s.records) if x.rid == r.rid)
    return s.records[max(0, idx - k):idx]


@functools.lru_cache(maxsize=None)
def load_fewshot(path: str) -> tuple[dict, ...]:
    if not path:
        return ()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data["examples"] if isinstance(data, dict) else data
    for e in items:
        if set(e) < {"condition", "record", "answer"} or e["answer"] not in ("A", "B", "C"):
            raise ValueError(f"bad few-shot item in {path}: {e}")
    return tuple(items)


def judge_record(m: Meter, s: Sample, c: Claim, r: Record, k: int = 0, fewshot: str = "") -> dict[str, float]:
    q = Query("record", P.record_judgment(s.task, s.proposed_action, c, r, preceding(s, r, k),
                                          list(load_fewshot(fewshot)) or None),
              cid=c.cid, rids=(r.rid,), sid=s.sid)
    return m.options(q)


def argmax(p: dict[str, float]) -> str:
    return max(p, key=p.get)


def holistic(m: Meter, s: Sample, c: Claim, records: list[Record]) -> tuple[str, dict]:
    q = Query("holistic", P.holistic_judgment(s.task, s.proposed_action, c, records),
              cid=c.cid, rids=tuple(r.rid for r in records), sid=s.sid)
    p = m.options(q)
    verdict = {"A": "SUPPORTED", "B": "CONTRADICTED", "C": "UNKNOWN"}[argmax(p)]
    return verdict, p


# ---------------------------------------------------------------- ordered audit (D1 core)

def ordered_audit(m: Meter, s: Sample, c: Claim, records: list[Record], cfg: Config):
    """Backward scan; the latest non-neutral record decides (doc §3.4).

    Decision rule on the newest non-neutral record h0 (and the one before it, h1):
      h0 decisive (P(pol) >= tau_conf)        -> verdict of h0's polarity
      h0 weak, h1 with the same polarity       -> that polarity
      h0 weak, h1 opposite or absent           -> UNKNOWN
      no non-neutral record                    -> no_evidence()
    Returns (verdict, evidence, judged{rid: probs}, hits[(rid, pol, prob)]).
    """
    judged: dict[int, dict[str, float]] = {}
    hits: list[tuple[int, str, float]] = []
    for r in reversed(records):
        p = judge_record(m, s, c, r, cfg.context_k, cfg.fewshot)
        judged[r.rid] = p
        pol = argmax(p)
        if pol == "C":
            continue
        hits.append((r.rid, pol, p[pol]))
        if cfg.early_stop and (hits[0][2] >= cfg.tau_conf or len(hits) >= 2):
            break

    if not hits:
        return no_evidence(s, c), [], judged, hits
    pol_verdict = {"A": "SUPPORTED", "B": "CONTRADICTED"}
    rid0, pol0, p0 = hits[0]
    if p0 >= cfg.tau_conf:
        return pol_verdict[pol0], [rid0], judged, hits
    if len(hits) >= 2 and hits[1][1] == pol0:
        return pol_verdict[pol0], [rid0, hits[1][0]], judged, hits
    return "UNKNOWN", [h[0] for h in hits[:2]], judged, hits


def pair_repair(m: Meter, s: Sample, c: Claim, records: list[Record], judged, hits, cfg: Config):
    """D2: pairwise check over weak-invalidation records after the latest establishing record."""
    last_est = max((rid for rid, pol, pr in hits if pol == "A" and pr >= cfg.tau_conf), default=-math.inf)
    by_rid = {r.rid: r for r in records}
    weak = [rid for rid, p in sorted(judged.items())
            if rid > last_est and argmax(p) != "A" and cfg.tau_low <= p["B"] < cfg.tau_high]
    trace = {"weak": weak, "triggered": len(weak) >= 2, "pairs": []}
    if len(weak) < 2:
        return None, trace
    pairs = sorted(itertools.combinations(weak, 2),
                   key=lambda ij: judged[ij[0]]["B"] + judged[ij[1]]["B"], reverse=True)[:cfg.max_pairs]
    for i, j in pairs:
        r1, r2 = by_rid[i], by_rid[j]
        q = Query("pair", P.pair_judgment(s.task, s.proposed_action, c, r1, r2),
                  cid=c.cid, rids=(i, j), sid=s.sid)
        p = m.options(q)
        trace["pairs"].append({"rids": [i, j], "probs": p})
        if argmax(p) == "A" and p["A"] >= cfg.tau_conf:
            return [i, j], trace
    return None, trace


# ---------------------------------------------------------------- methods

def m_D1(s, c, m, cfg, ctx, records=None):
    records = s.records if records is None else records
    v, ev, judged, hits = ordered_audit(m, s, c, records, cfg)
    return v, ev, {"hits": hits, "judged": judged, "window": [r.rid for r in records]}


def m_D1f(s, c, m, cfg, ctx):
    return m_D1(s, c, m, cfg, ctx, records=entity_window(s, c))


def m_D2(s, c, m, cfg, ctx):
    v, ev, judged, hits = ordered_audit(m, s, c, s.records, cfg)
    trace = {"hits": hits, "judged": judged, "d1_verdict": v}
    if v != "CONTRADICTED":
        pair_ev, ptrace = pair_repair(m, s, c, s.records, judged, hits, cfg)
        trace["pair"] = ptrace
        if pair_ev:
            return "CONTRADICTED", pair_ev, trace
    return v, ev, trace


def m_U1(s, c, m, cfg, ctx):
    judged = {r.rid: judge_record(m, s, c, r, cfg.context_k, cfg.fewshot) for r in s.records}
    inval = [rid for rid, p in judged.items() if argmax(p) == "B" and p["B"] >= cfg.tau_conf]
    est = [rid for rid, p in judged.items() if argmax(p) == "A" and p["A"] >= cfg.tau_conf]
    trace = {"judged": judged}
    if inval:
        return "CONTRADICTED", inval, trace
    if est:
        return "SUPPORTED", est, trace
    return no_evidence(s, c), [], trace


def m_H1(s, c, m, cfg, ctx):
    v, p = holistic(m, s, c, s.records)
    return v, [], {"probs": p}


def m_H2(s, c, m, cfg, ctx):
    win = entity_window(s, c)
    v, p = holistic(m, s, c, win)
    return v, [], {"probs": p, "window": [r.rid for r in win]}


def m_P0(s, c, m, cfg, ctx):
    """Presence-only. Source = latest decisively establishing record (found with the
    per-record judgment); prediction = any entity-matching record after it."""
    src = None
    for r in reversed(s.records):
        p = judge_record(m, s, c, r, cfg.context_k, cfg.fewshot)
        if argmax(p) == "A" and p["A"] >= cfg.tau_conf:
            src = r.rid
            break
    if src is None and c.kind == "state":
        return "UNKNOWN", [], {"source": None}
    start = -math.inf if src is None else src
    after = [r.rid for r in entity_window(s, c) if r.rid > start]
    if after:
        return "CONTRADICTED", after, {"source": src, "n_after": len(after)}
    return ("SUPPORTED" if src is not None else no_evidence(s, c)), [], {"source": src, "n_after": 0}


def _neg_logit(p: float, eps: float = 1e-6) -> float:
    p = min(max(p, eps), 1 - eps)
    return -math.log(p / (1 - p))


def m_Q0(s, c, m, cfg, ctx):
    """Original EDA readout: find the latest source with Q-source and Q-delta both
    'yes', then score = max over later records of -logit(P(still possibly true))."""
    def ask(kind, render, r):
        q = Query(kind, render(s.task, s.proposed_action, c, r),
                  cid=c.cid, rids=(r.rid,), sid=s.sid)
        return m.options(q)["A"]

    src, delta_cache = None, {}
    for r in reversed(s.records):
        ps = ask("q_source", P.q_source, r)
        pd = ask("q_delta", P.q_delta, r)
        delta_cache[r.rid] = pd
        if ps > 0.5 and pd > 0.5:
            src = r.rid
            break
    if src is None and c.kind == "state":
        return "UNKNOWN", [], {"source": None}
    start = -math.inf if src is None else src
    after = [r for r in s.records if r.rid > start]
    scores = {}
    for r in after:
        pd = delta_cache[r.rid] if r.rid in delta_cache else ask("q_delta", P.q_delta, r)
        scores[r.rid] = _neg_logit(pd)
    top = max(scores.values(), default=-math.inf)
    trace = {"source": src, "scores": scores, "max_neg_logodds": top}
    if top > cfg.tau_q0:
        return "CONTRADICTED", [max(scores, key=scores.get)], trace
    return ("SUPPORTED" if src is not None else no_evidence(s, c)), ([src] if src is not None else []), trace


_JSON_RE = re.compile(r"(\[.*\]|\{.*\}|null)", re.S)


def _parse_json(text: str):
    mt = _JSON_RE.search(text or "")
    if not mt:
        return None
    try:
        return json.loads(mt.group(1))
    except json.JSONDecodeError:
        return None


def _norm(x) -> str:
    return re.sub(r"\s+", " ", str(x).strip().lower())


def m_E1(s, c, m, cfg, ctx):
    """Extract-then-track. Extraction is claim-agnostic and done once per sample
    (free generation, JSON); its calls are charged to the first claim of the sample.
    Mapping the claim to a tracked key and checking the value are option readouts
    (p3), so E1 is not penalised for inventing key names."""
    key = ("E1_state", s.sid)
    if key not in ctx:
        state: dict[tuple[str, str], tuple[str, int]] = {}
        for r in s.records:
            out = _parse_json(m.generate(Query("extract", text=P.extract_state(s.task, r, preceding(s, r, cfg.context_k)),
                                               rids=(r.rid,), sid=s.sid)))
            for f in out if isinstance(out, list) else []:
                if isinstance(f, dict) and {"entity", "attribute", "value"} <= f.keys():
                    state[(_norm(f["entity"]), _norm(f["attribute"]))] = (_norm(f["value"]), r.rid)
        ctx[key] = state
    state = ctx[key]
    # latest-updated keys first, capped at 25 single-letter options
    keys = sorted(state, key=lambda k: state[k][1], reverse=True)[: len(P.KEY_LETTERS)]
    trace = {"n_keys": len(state)}
    if not keys:
        return no_evidence(s, c), [], trace
    mcq = P.map_claim_choice(c, keys)
    letters = mcq.letters
    pm = m.options(Query("map_choice", mcq, cid=c.cid, sid=s.sid))
    pick = argmax(pm)
    trace["map_probs"] = pm
    if pick == "Z":
        return no_evidence(s, c), [], trace
    ent, att = keys[letters.index(pick)]
    val, rid = state[(ent, att)]
    trace.update({"key": [ent, att], "tracked_value": val})
    pv = m.options(Query("value_check", P.value_check(c, ent, att, val, rid),
                         cid=c.cid, rids=(rid,), sid=s.sid))
    trace["value_probs"] = pv
    verdict = {"A": "SUPPORTED", "B": "CONTRADICTED", "C": "UNKNOWN"}[argmax(pv)]
    return verdict, [rid], trace


def m_T0(s, c, m, cfg, ctx):
    """Deterministic ALFWorld tracker over the visible records; UNKNOWN without a spec."""
    if not c.spec:
        return "UNKNOWN", [], {"reason": "no spec"}
    st = alfworld.replay(alfworld.steps_from_records([r.text for r in s.records]))
    return alfworld.evaluate_spec(c.spec, st), [], {"loc": st.loc, "holding": st.holding}


METHODS = {"H1": m_H1, "H2": m_H2, "U1": m_U1, "D1": m_D1, "D1f": m_D1f,
           "D2": m_D2, "E1": m_E1, "P0": m_P0, "Q0": m_Q0, "T0": m_T0}


NEEDS_GENERATOR = {"E1"}


def run(samples: list[Sample], methods: list[str], backend: DecisionBackend, cfg: Config,
        generator: Generator | None = None, workers: int = 1) -> list[dict]:
    """Run each method on each claim. A per-claim exception (e.g. a malformed model
    answer) becomes verdict UNKNOWN with an ``error`` field; configuration errors
    (missing generator, unknown method) raise before any work. ``workers>1`` runs
    (method, sample) jobs in threads (for API backends); the row order is unchanged."""
    unknown = [m for m in methods if m not in METHODS]
    if unknown:
        raise ValueError(f"unknown methods {unknown}")
    if generator is None and NEEDS_GENERATOR & set(methods):
        raise ValueError(f"{sorted(NEEDS_GENERATOR & set(methods))} need a generator (--gen-model)")

    def job(meth: str, s: Sample) -> list[dict]:
        fn = METHODS[meth]
        ctx: dict = {}
        rows = []
        for c in s.claims:
            m = Meter(backend, generator)
            try:
                v, ev, trace = fn(s, c, m, cfg, ctx)
                err = None
            except (NotImplementedError, RuntimeError):
                raise  # missing backend pieces must stop the run, not become UNKNOWN
            except Exception as e:
                v, ev, trace, err = "UNKNOWN", [], {}, f"{type(e).__name__}: {e}"
            row = asdict(Result(meth, s.sid, c.cid, v, ev, m.calls, m.chars, _jsonable(trace)))
            row["gen_calls"] = m.gen_calls
            if err:
                row["error"] = err
            rows.append(row)
        return rows

    jobs = [(meth, s) for meth in methods for s in samples]
    if workers <= 1:
        return [r for meth, s in jobs for r in job(meth, s)]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(job, meth, s) for meth, s in jobs]
        try:
            return [r for f in futures for r in f.result()]
        except BaseException:
            for f in futures:
                f.cancel()
            raise


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, float) and math.isinf(x):
        return None
    return x
