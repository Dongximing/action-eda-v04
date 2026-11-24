"""Jev adapter for the TypeSafe systemone API (the same endpoint and request
shape as NativeJev in the alfworld-action-eda-oneshot-altprovider runner).

  export TYPESAFE_API_KEY=...            # or JEV_API_KEY
  export JEV_MODEL=jev-1.14.0            # optional, this is the default
  python scripts/run_offline.py --backend jev --jev-adapter adapters.typesafe_jev:choose ...

Request: {"model", "state": {"context": <records/claim text>},
          "questions": {"decision": {"type": "choice", "instructions": <question>,
                                      "criteria": {letter: option text}}}}
Return: the probability dict if the response carries one keyed by option letter,
otherwise the chosen letter (counted as one-hot in run_meta.json).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

URL = os.getenv("JEV_URL", "https://api.typesafe.ai/v1/systemone")
RETRY = {408, 429, 500, 502, 503, 504}


class JevError(RuntimeError):
    pass


def _key() -> str:
    key = (os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY") or "").strip()
    if not key:
        # RuntimeError is re-raised by aeda.verifiers.run, so a missing key stops the run at once
        raise RuntimeError("set TYPESAFE_API_KEY (or JEV_API_KEY) for the Jev adapter")
    return key


def _post(payload: dict, timeout: float = 90, attempts: int = 6) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json",
               "Authorization": f"Bearer {_key()}"}
    for i in range(attempts):
        req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403):
                raise RuntimeError(f"Jev HTTP {e.code}: check the key, balance or model access") from None
            if e.code not in RETRY or i + 1 == attempts:
                raise JevError(f"Jev HTTP {e.code}") from None
            ra = e.headers.get("Retry-After", "") if e.headers else ""
            time.sleep(min(60, int(ra)) if ra.isdigit() else min(60, 2 ** i * (4 if e.code == 429 else 1)))
        except (OSError, json.JSONDecodeError) as e:
            if i + 1 == attempts:
                raise JevError(f"Jev connection failed: {type(e).__name__}") from None
            time.sleep(2 ** i)
    raise JevError("unreachable")


def _probs(answer: dict, letters: list[str]) -> dict[str, float] | None:
    p = answer.get("probabilities")
    if isinstance(p, dict) and set(p) == set(letters):
        try:
            out = {k: float(v) for k, v in p.items()}
        except (TypeError, ValueError):
            return None
        return out if all(v >= 0 for v in out.values()) and sum(out.values()) > 0 else None
    if isinstance(p, list) and len(p) == len(letters):
        try:
            out = {l: float(v) for l, v in zip(letters, p)}
        except (TypeError, ValueError):
            return None
        return out if all(v >= 0 for v in out.values()) and sum(out.values()) > 0 else None
    return None


def choose(context: str, question: str, options: list[tuple[str, str]]) -> dict[str, float] | str:
    letters = [l for l, _ in options]
    result = _post({
        "model": os.getenv("JEV_MODEL", "jev-1.14.0"),
        "state": {"context": context},
        "questions": {"decision": {"type": "choice", "instructions": question,
                                   "criteria": {l: t for l, t in options}}},
    })
    try:
        answer = result["answers"]["decision"]
        choice = answer["choice"]
    except (KeyError, TypeError):
        raise JevError("Jev response lacks answers.decision.choice") from None
    probs = _probs(answer, letters) if isinstance(answer, dict) else None
    if probs is not None:
        return probs
    if not isinstance(choice, str) or choice.strip() not in letters:
        raise JevError(f"Jev returned an unknown option: {choice!r}")
    return choice.strip()
