"""Decision adapter for an OpenRouter chat model (default qwen/qwen3.5-9b, the main
agent of the alfworld-9b-oneshot runs). Reported as api:openrouter/<model>, not as Jev.

  export OPENROUTER_API_KEY=...
  export OR_MODEL=qwen/qwen3.5-9b      # optional (default)
  export OR_PROVIDER=parasail          # optional; the provider those runs used. Empty = OpenRouter routing
  python scripts/run_offline.py --backend api --adapter adapters.openrouter_chat:choose --workers 8 ...

The prompt is the same rendered multiple-choice text as the local HF backend
(context, question, lettered options, "Answer with a single letter."), temperature 0,
reasoning off. Scores come from the first token's top_logprobs over the option
letters when the provider returns logprobs; otherwise the answer letter alone
(one-hot, counted in run_meta.json).
"""
from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.error
import urllib.request

URL = os.getenv("OR_URL", "https://openrouter.ai/api/v1/chat/completions")
RETRY = {408, 429, 500, 502, 503, 504}
SYSTEM = "You answer multiple-choice questions. Reply with the letter of one option only."


class ChatError(ValueError):
    """Malformed or unusable answer: the claim becomes UNKNOWN with an error."""


def model() -> str:
    return os.getenv("OR_MODEL", "qwen/qwen3.5-9b")


def describe() -> str:
    prov = os.getenv("OR_PROVIDER", "parasail")
    return f"openrouter/{model()}" + (f"@{prov}" if prov else "")


def render(context: str, question: str, options: list[tuple[str, str]]) -> str:
    # identical layout to aeda.prompts.MCQ.render, which the HF backend scores
    from aeda.prompts import MCQ
    return MCQ(context, question, list(options)).render()


def _key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("set OPENROUTER_API_KEY for adapters.openrouter_chat")
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
                raise RuntimeError(f"OpenRouter HTTP {e.code}: check the key, credits or model access") from None
            if e.code not in RETRY or i + 1 == attempts:
                raise RuntimeError(f"OpenRouter HTTP {e.code} after {i + 1} attempt(s)") from None
            ra = e.headers.get("Retry-After", "") if e.headers else ""
            time.sleep(min(60, int(ra)) if ra.isdigit() else min(60, 2 ** i * (4 if e.code == 429 else 1)))
        except (OSError, json.JSONDecodeError) as e:
            if i + 1 == attempts:
                raise RuntimeError(f"OpenRouter connection failed: {type(e).__name__}") from None
            time.sleep(2 ** i)
    raise RuntimeError("unreachable")


def letter_scores(result: dict, letters: list[str]) -> dict[str, float] | None:
    """Probabilities of the option letters at the first generated token, if logprobs came back."""
    try:
        first = result["choices"][0]["logprobs"]["content"][0]
    except (KeyError, IndexError, TypeError):
        return None
    cands = list(first.get("top_logprobs") or [])
    if first.get("token") is not None:
        cands.append({"token": first["token"], "logprob": first.get("logprob")})
    best: dict[str, float] = {}
    for t in cands:
        tok = str(t.get("token", "")).strip().rstrip(".:)").upper()
        lp = t.get("logprob")
        if tok in letters and isinstance(lp, (int, float)) and math.isfinite(lp):
            best[tok] = max(best.get(tok, -math.inf), lp)
    if not best:
        return None
    return {l: math.exp(best[l]) if l in best else 0.0 for l in letters}


def parse_letter(text: str, letters: list[str]) -> str:
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    if t[:1].upper() in letters and (len(t) == 1 or not t[1:2].isalpha()):
        return t[:1].upper()
    found = [m for m in re.findall(r"\b([A-Z])\b", t) if m in letters]
    if len(set(found)) == 1:
        return found[0]
    raise ChatError(f"no single option letter in answer {t[:80]!r}")


def choose(context: str, question: str, options: list[tuple[str, str]]) -> dict[str, float] | str:
    letters = [l for l, _ in options]
    payload = {
        "model": model(),
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": render(context, question, options)}],
        "temperature": 0,
        "max_tokens": 8,
        "logprobs": True,
        "top_logprobs": 20,
        "reasoning": {"enabled": False},
    }
    prov = os.getenv("OR_PROVIDER", "parasail")
    if prov:
        payload["provider"] = {"order": [prov], "allow_fallbacks": False}
    result = _post(payload)
    scores = letter_scores(result, letters)
    if scores is not None and sum(scores.values()) > 0:
        return scores
    try:
        text = result["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError, AttributeError):
        raise ChatError("OpenRouter response has no message") from None
    return parse_letter(text, letters)
