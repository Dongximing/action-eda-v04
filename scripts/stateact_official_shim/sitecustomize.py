"""Request settings for the official StateAct run (scripts/run_stateact_official.sh); their code is not changed.

Loaded through PYTHONPATH in that run only. Every chat request their llamp OpenAIChatText sends gets the same
OpenRouter settings as our own arms: reasoning off (otherwise qwen3.5-9b spends the reply on reasoning and the
"\\n\\n" stop leaves no answer), the provider route of routing.json, require_parameters. Their messages,
temperature and stop sequences are sent as they are. OpenRouter's reported usage of every request is appended
to $STATEACT_USAGE_LOG (one JSON line: tokens, cost, finish reason). A hanging request times out after
$STATEACT_TIMEOUT seconds (default 120) and is retried by their OpenAI client.
"""
import json
import os
import time

ROUTE = os.environ.get("STATEACT_ROUTE", "parasail")
LOG = os.environ.get("STATEACT_USAGE_LOG")

try:
    from openai.resources.chat.completions import Completions

    _create = Completions.create

    def create(self, *args, **kwargs):
        body = dict(kwargs.pop("extra_body", None) or {})
        body.setdefault("reasoning", {"enabled": False})
        body.setdefault("provider", {"require_parameters": True, "only": [ROUTE], "allow_fallbacks": False})
        body.setdefault("usage", {"include": True})
        # a request that hangs is abandoned after 2 minutes; their OpenAI client then retries it (max_retries 2)
        kwargs.setdefault("timeout", float(os.environ.get("STATEACT_TIMEOUT", "120")))
        t = time.time()
        out = _create(self, *args, extra_body=body, **kwargs)
        if LOG:
            u = getattr(out, "usage", None)
            ch = out.choices[0] if getattr(out, "choices", None) else None
            row = {"time": round(t, 3), "seconds": round(time.time() - t, 3), "model": getattr(out, "model", None),
                   "provider": getattr(out, "provider", None),
                   "input_tokens": getattr(u, "prompt_tokens", None), "output_tokens": getattr(u, "completion_tokens", None),
                   "cost_usd": getattr(u, "cost", None), "finish_reason": getattr(ch, "finish_reason", None),
                   "empty_content": not (ch and ch.message and ch.message.content)}
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        return out

    Completions.create = create
except Exception as e:  # never break the run because of the shim; say so
    print(f"[stateact shim] not installed: {type(e).__name__}: {e}")
