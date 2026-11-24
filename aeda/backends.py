"""Model backends.

Two roles are kept separate:

* **Decision backend** — ``options(query)`` returns a probability (or a one-hot
  choice) for each lettered option of a multiple-choice item, in one pass, without
  generating text. This is the Jev role in design doc v0.4. All verdicts of H1,
  H2, U1, D1, D1f, D2, P0, Q0 and E1's mapping/value steps come from it.
* **Generator** — ``generate(query)`` returns free text. Only E1's claim-agnostic
  extraction and scripts/generate_claims.py need it; Jev is not used for this.

Backends:
  JevBackend       the decision model of the study, called through a user adapter
                   (see adapters/jev_adapter.py); no default implementation
  HFOptionBackend  local HuggingFace causal LM: option readout from next-token
                   logits, and generation. Usable as the generator, or as an
                   explicitly named *comparison* decision model (e.g. the original
                   EDA's Qwen3-4B readout for Q0). It is not a Jev substitute.
  TableBackend     deterministic answers from a JSON table, for tests only
"""
from __future__ import annotations

import importlib
import json
import math
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from .prompts import MCQ


@dataclass
class Query:
    kind: str           # record|pair|holistic|q_source|q_delta|map_choice|value_check|extract|gen_claims
    mcq: MCQ | None = None      # decision queries
    text: str | None = None     # generation queries
    cid: str | None = None
    rids: tuple[int, ...] = ()
    sid: str | None = None

    @property
    def prompt(self) -> str:
        return self.mcq.render() if self.mcq is not None else (self.text or "")

    @property
    def letters(self) -> list[str]:
        return self.mcq.letters if self.mcq is not None else []


@dataclass
class Usage:
    calls: int = 0
    cache_hits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    one_hot: int = 0          # decision answers that carried no graded probabilities

    def as_dict(self) -> dict:
        return dict(self.__dict__)


class DecisionBackend(Protocol):
    name: str
    usage: Usage

    def options(self, q: Query) -> dict[str, float]: ...


class Generator(Protocol):
    name: str
    usage: Usage

    def generate(self, q: Query, max_new_tokens: int = 256) -> str: ...


def _softmax(xs: list[float]) -> list[float]:
    m = max(xs)
    es = [math.exp(x - m) for x in xs]
    s = sum(es)
    return [e / s for e in es]


def normalise_choice(raw: Any, letters: list[str]) -> dict[str, float]:
    """Validate a decision answer and return probabilities over exactly ``letters``.

    Accepts {letter: score>=0} (renormalised) or a single letter (one-hot).
    Raises ValueError on anything else, so a malformed answer never becomes a verdict.
    """
    if isinstance(raw, str):
        if raw not in letters:
            raise ValueError(f"choice {raw!r} not among options {letters}")
        return {l: float(l == raw) for l in letters}
    if not isinstance(raw, dict):
        raise ValueError(f"decision answer must be dict or letter, got {type(raw).__name__}")
    extra = set(raw) - set(letters)
    if extra:
        raise ValueError(f"answer has unknown options {sorted(extra)}; expected {letters}")
    vals = {l: float(raw.get(l, 0.0)) for l in letters}
    if any(v < 0 or math.isnan(v) for v in vals.values()):
        raise ValueError(f"negative or NaN score in {raw}")
    s = sum(vals.values())
    if s <= 0:
        raise ValueError(f"all-zero scores in {raw}")
    return {l: v / s for l, v in vals.items()}


class JevBackend:
    """Jev decision model, called through a user-supplied adapter function.

    The adapter is ``module:function`` (``--jev-adapter`` or env ``AEDA_JEV_ADAPTER``)
    with signature::

        def choose(context: str, question: str, options: list[tuple[str, str]]) -> dict[str, float] | str

    It returns a score per option letter, or just the chosen letter if the API
    gives no scores (counted in ``usage.one_hot``; threshold rules such as the D2
    weak-signal trigger and Q0 log-odds then degrade and this must be reported).
    """

    def __init__(self, adapter: str | None = None, cache: bool = True):
        spec = adapter or os.environ.get("AEDA_JEV_ADAPTER")
        if not spec or ":" not in spec:
            raise ValueError("JevBackend needs --jev-adapter module:function (see adapters/jev_adapter.py)")
        mod, fn = spec.split(":", 1)
        self.fn: Callable = getattr(importlib.import_module(mod), fn)
        self.name = f"jev:{spec}"
        self.usage = Usage()
        self._cache: dict | None = {} if cache else None

    def options(self, q: Query) -> dict[str, float]:
        if q.mcq is None:
            raise ValueError(f"Jev only answers multiple-choice queries, got {q.kind}")
        key = (q.mcq.context, q.mcq.question, tuple(q.mcq.options))
        if self._cache is not None and key in self._cache:
            self.usage.cache_hits += 1
            return self._cache[key]
        t0 = time.time()
        raw = self.fn(q.mcq.context, q.mcq.question, list(q.mcq.options))
        out = normalise_choice(raw, q.letters)
        self.usage.calls += 1
        self.usage.seconds += time.time() - t0
        if isinstance(raw, str) or max(out.values()) == 1.0:
            self.usage.one_hot += 1
        if self._cache is not None:
            self._cache[key] = out
        return out


class HFOptionBackend:
    """Local HuggingFace causal LM: single-forward-pass option readout and generation.

    Option readout = next-token logits of the option letters after the chat
    template's assistant prefix, renormalised over the offered letters. With Qwen3
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
        if q.mcq is None:
            raise ValueError(f"options() needs a multiple-choice query, got {q.kind}")
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


class TableBackend:
    """Deterministic answers from a JSON table keyed by query kind and ids (tests only).

    Table format::

        {"record":      {"<cid>|<rid>": {"A": .., "B": .., "C": ..}},
         "pair":        {"<cid>|<rid1>|<rid2>": {...}},
         "holistic":    {"<cid>|<rid,rid,...>": {...}, "<cid>|*": {...}},
         "q_source":    {"<cid>|<rid>": {"A": .., "B": ..}},
         "q_delta":     {"<cid>|<rid>": {...}},
         "extract":     {"<sid>|<rid>": [{"entity":..,"attribute":..,"value":..}]},
         "map_choice":  {"<cid>": {"A": .., ..., "Z": ..}},
         "value_check": {"<cid>|<rid>": {"A": .., "B": .., "C": ..}}}

    Missing entries fall back to an uninformative answer. cids must be unique.
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
        tab = self.t.get(q.kind, {})
        if q.kind == "holistic":
            hit = tab.get(f"{q.cid}|{','.join(map(str, q.rids))}") or tab.get(f"{q.cid}|*")
        else:
            hit = tab.get(self._key(q))
        if hit is None:
            defaults = {"record": {"A": .05, "B": .05, "C": .9}, "pair": {"A": .05, "B": .9, "C": .05},
                        "q_delta": {"A": .95, "B": .05}, "q_source": {"A": .05, "B": .95}}
            hit = defaults.get(q.kind) or {l: 1 / len(q.letters) for l in q.letters}
        hit = {l: v for l, v in hit.items() if l in q.letters}
        return normalise_choice(hit, q.letters)

    def generate(self, q: Query, max_new_tokens: int = 256) -> str:
        self.usage.calls += 1
        if q.kind == "extract":
            return json.dumps(self.t.get("extract", {}).get(f"{q.sid}|{q.rids[0]}", []), ensure_ascii=False)
        return ""
