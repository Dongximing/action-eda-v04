"""Decision-model backends.

Every verifier talks to a backend through two calls:

* ``options(query)``  -> probability for each option letter, from ONE forward pass
  (single-token option readout, the "one-pass decision model" setting).
* ``generate(query)`` -> free text; only E1 (extract-then-track) needs it.

A ``Query`` carries both the rendered prompt and the structured fields, so a table
backend used in tests can answer from ids without parsing text.

Backends:
  HFOptionBackend   local HuggingFace causal LM (default Qwen/Qwen3-4B, thinking off)
  JevBackend        placeholder for the Jev API; fill in once the interface is known
  TableBackend      deterministic answers from a JSON table, for tests and smoke runs
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Query:
    kind: str                     # record|pair|holistic|q_source|q_delta|extract|map_choice|value_check|gen_claims
    prompt: str
    letters: list[str] = field(default_factory=list)
    cid: str | None = None
    rids: tuple[int, ...] = ()
    sid: str | None = None


@dataclass
class Usage:
    calls: int = 0
    cache_hits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0

    def as_dict(self) -> dict:
        return dict(self.__dict__)


class Backend(Protocol):
    name: str
    usage: Usage

    def options(self, q: Query) -> dict[str, float]: ...
    def generate(self, q: Query, max_new_tokens: int = 256) -> str: ...


def _softmax(xs: list[float]) -> list[float]:
    m = max(xs)
    es = [math.exp(x - m) for x in xs]
    s = sum(es)
    return [e / s for e in es]


class HFOptionBackend:
    """Single-forward-pass option readout from a local causal LM.

    Reads next-token logits of the option letters after the chat template's
    assistant prefix and renormalises over the offered letters. With Qwen3,
    ``enable_thinking=False`` inserts an empty think block so the first generated
    token is the answer.
    """

    def __init__(self, model_name: str = "Qwen/Qwen3-4B", device: str | None = None,
                 dtype: str = "bfloat16", enable_thinking: bool = False, cache: bool = True):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        if device is None:
            device = "cuda" if torch.cuda.is_available() else (
                "mps" if torch.backends.mps.is_available() else "cpu")
        self.device = device
        self.name = f"hf:{model_name}"
        self.enable_thinking = enable_thinking
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=getattr(torch, dtype)).to(device).eval()
        self.usage = Usage()
        self._cache: dict[tuple, Any] | None = {} if cache else None
        self._letter_ids: dict[str, int] = {}

    def _chat(self, prompt: str) -> str:
        msgs = [{"role": "user", "content": prompt}]
        try:
            return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                                enable_thinking=self.enable_thinking)
        except TypeError:  # templates without the enable_thinking switch
            return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    def _letter_id(self, letter: str) -> int:
        if letter not in self._letter_ids:
            ids = self.tok.encode(letter, add_special_tokens=False)
            if len(ids) != 1:
                raise ValueError(f"option {letter!r} is not a single token for {self.name}")
            self._letter_ids[letter] = ids[0]
        return self._letter_ids[letter]

    def options(self, q: Query) -> dict[str, float]:
        key = ("opt", q.prompt, tuple(q.letters))
        if self._cache is not None and key in self._cache:
            self.usage.cache_hits += 1
            return self._cache[key]
        t0 = time.time()
        enc = self.tok(self._chat(q.prompt), return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            logits = self.model(**enc).logits[0, -1].float()
        raw = [logits[self._letter_id(l)].item() for l in q.letters]
        out = dict(zip(q.letters, _softmax(raw)))
        self.usage.calls += 1
        self.usage.input_tokens += int(enc["input_ids"].shape[1])
        self.usage.seconds += time.time() - t0
        if self._cache is not None:
            self._cache[key] = out
        return out

    def generate(self, q: Query, max_new_tokens: int = 256) -> str:
        key = ("gen", q.prompt, max_new_tokens)
        if self._cache is not None and key in self._cache:
            self.usage.cache_hits += 1
            return self._cache[key]
        t0 = time.time()
        enc = self.tok(self._chat(q.prompt), return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            out_ids = self.model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False)
        new = out_ids[0, enc["input_ids"].shape[1]:]
        text = self.tok.decode(new, skip_special_tokens=True).strip()
        self.usage.calls += 1
        self.usage.input_tokens += int(enc["input_ids"].shape[1])
        self.usage.output_tokens += int(new.shape[0])
        self.usage.seconds += time.time() - t0
        if self._cache is not None:
            self._cache[key] = text
        return text


class JevBackend:
    """Placeholder for the Jev decision model.

    Fill in ``options`` with the real API call once its interface is confirmed:
    how many options per question, whether several questions can share one
    prompt, and whether it returns per-option probabilities or only a choice.
    If it returns only a choice, return {choice: 1.0, others: 0.0} and note that
    threshold-based rules (D2 weak-signal trigger, Q0 log-odds) degrade.
    """

    name = "jev"

    def __init__(self, **kwargs):
        self.usage = Usage()
        self.kwargs = kwargs

    def options(self, q: Query) -> dict[str, float]:
        raise NotImplementedError("Jev API not wired yet; see JevBackend docstring")

    def generate(self, q: Query, max_new_tokens: int = 256) -> str:
        raise NotImplementedError("Jev is a decision model; use a generative backend for E1")


class TableBackend:
    """Answers from a JSON table keyed by query kind and ids.

    Table format::

        {"record":   {"<cid>|<rid>": {"A": .., "B": .., "C": ..}},
         "pair":     {"<cid>|<rid1>|<rid2>": {...}},
         "holistic": {"<cid>|<rid,rid,...>": {...}, "<cid>|*": {...}},
         "q_source": {"<cid>|<rid>": {"A": .., "B": ..}},
         "q_delta":  {"<cid>|<rid>": {...}},
         "extract":  {"<sid>|<rid>": [{"entity":..,"attribute":..,"value":..}]},
         "map_choice":  {"<cid>": {"A": .., ..., "Z": ..}},      # E1 key choice
         "value_check": {"<cid>|<rid>": {"A": .., "B": .., "C": ..}}}

    Missing entries fall back to an uninformative answer (C for 3-option record
    queries, uniform otherwise). ``sid`` is not part of the key, so cids must be
    unique across a table.
    """

    name = "table"

    def __init__(self, table: dict):
        self.t = table
        self.usage = Usage()

    @classmethod
    def from_file(cls, path: str) -> "TableBackend":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    def _key(self, q: Query) -> str:
        return "|".join([q.cid or ""] + [str(r) for r in q.rids])

    def options(self, q: Query) -> dict[str, float]:
        self.usage.calls += 1
        self.usage.input_tokens += len(q.prompt) // 4
        tab = self.t.get(q.kind, {})
        if q.kind == "holistic":
            hit = tab.get(f"{q.cid}|{','.join(map(str, q.rids))}") or tab.get(f"{q.cid}|*")
        else:
            hit = tab.get(self._key(q))
        if hit is None:
            if q.kind == "record":
                hit = {"A": 0.05, "B": 0.05, "C": 0.9}
            elif q.kind == "pair":
                hit = {"A": 0.05, "B": 0.9, "C": 0.05}
            elif q.kind == "q_delta":
                hit = {"A": 0.95, "B": 0.05}
            elif q.kind == "q_source":
                hit = {"A": 0.05, "B": 0.95}
            else:
                hit = {l: 1 / len(q.letters) for l in q.letters}
        s = sum(hit.get(l, 0.0) for l in q.letters)
        return {l: hit.get(l, 0.0) / s for l in q.letters}

    def generate(self, q: Query, max_new_tokens: int = 256) -> str:
        self.usage.calls += 1
        if q.kind == "extract":
            return json.dumps(self.t.get("extract", {}).get(f"{q.sid}|{q.rids[0]}", []),
                              ensure_ascii=False)
        return ""


def make_backend(kind: str, **kw) -> Backend:
    if kind == "hf":
        return HFOptionBackend(**kw)
    if kind == "jev":
        return JevBackend(**kw)
    if kind == "table":
        return TableBackend.from_file(kw["table"])
    raise ValueError(f"unknown backend {kind!r}")
