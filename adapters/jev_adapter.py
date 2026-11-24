"""Jev adapter — fill in ``choose`` with the real Jev call.

Used as:  --backend jev --jev-adapter adapters.jev_adapter:choose
(or set env AEDA_JEV_ADAPTER=adapters.jev_adapter:choose)

Contract
--------
choose(context, question, options) is called once per multiple-choice item.

  context  : str   task, condition and the record(s) to judge (already formatted)
  question : str   the question, e.g. "Considering only this record, what does it do to the condition?"
  options  : list[(letter, text)], e.g. [("A", "Establishes it: ..."), ("B", "Invalidates it: ..."), ("C", "Neither: ...")]

Return either
  * dict {letter: score >= 0} for every letter (renormalised by the caller), or
  * the chosen letter as a str, if Jev returns no scores. One-hot answers are
    counted in run_meta.json (backend_usage.one_hot); the D2 weak-signal trigger
    and Q0's log-odds need graded scores and degrade without them.

Anything else (unknown letter, negative score, exception) makes that claim's
verdict UNKNOWN with an "error" field, and run_offline.py exits non-zero unless
--allow-errors is given.

Check the adapter before a full run:
  python scripts/check_backend.py --backend jev --jev-adapter adapters.jev_adapter:choose
"""
from __future__ import annotations


def choose(context: str, question: str, options: list[tuple[str, str]]) -> dict[str, float] | str:
    # Example shape only — replace with the real client call, e.g.
    #   resp = client.decide(prompt=context + "\n\n" + question,
    #                        options=[text for _, text in options])
    #   return {letter: p for (letter, _), p in zip(options, resp.probabilities)}
    raise NotImplementedError("fill in adapters/jev_adapter.py:choose with the Jev API call")
