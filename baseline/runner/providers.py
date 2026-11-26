"""Standard-library transports for TypeSafe Jev and chat-completions models."""

from __future__ import annotations

import http.client
import json
import math
import threading
import time
import urllib.error
import urllib.parse
import urllib.request


class ProviderError(RuntimeError):
    """A request failed or the provider returned an invalid answer."""


class IncompleteReply(ProviderError):
    """The provider returned no complete visible JSON document."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A caller can select an endpoint explicitly. Keep the bearer token there.
        return None


def _endpoint(url: str, route: str) -> str:
    try:
        parts = urllib.parse.urlsplit(url)
        port = parts.port
    except ValueError:
        raise ValueError("Provide a valid provider URL.") from None
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or port == 0
    ):
        raise ValueError("Provide an absolute HTTP(S) provider URL without credentials or a query.")
    path = parts.path.rstrip("/")
    if not path.endswith(route):
        if not path.endswith("/v1"):
            path += "/v1"
        path += route
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _choice_label(value: object, options: dict[str, str]) -> str:
    if not isinstance(value, str) or value.strip() not in options:
        raise ProviderError("The provider returned an invalid choice label.")
    return value.strip()


class _Transport:
    def __init__(self, endpoint: str, model: str, key: str | None, timeout: float):
        if not model.strip() or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Provide a model ID and a positive request timeout.")
        if key and ("\r" in key or "\n" in key):
            raise ValueError("The provider token must be a single line.")
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout
        self._headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if key:
            self._headers["Authorization"] = f"Bearer {key}"
        self._opener = urllib.request.build_opener(_NoRedirect())
        self._stats_lock = threading.Lock()
        self.requests = 0
        self.elapsed_seconds = 0.0
        self.calls: list[dict] = []

    def usage(self) -> dict:
        """Token totals count only values the serving endpoint actually reported."""
        with self._stats_lock:
            rows = list(self.calls)
            def observed(name):
                values = [row[name] for row in rows if row.get(name) is not None]
                return sum(values) if values else None
            return {
                "configured_model": self.model, "requests": self.requests,
                "successful_responses": sum(row["ok"] for row in rows),
                "failed_transports": sum(not row["ok"] for row in rows),
                "responses_with_token_usage": sum(row.get("input_tokens") is not None and
                                                 row.get("output_tokens") is not None for row in rows),
                "observed_input_tokens": observed("input_tokens"), "observed_output_tokens": observed("output_tokens"),
                "observed_usd": observed("cost_usd"), "seconds": round(self.elapsed_seconds, 3),
            }

    def post(self, payload: dict) -> dict:
        request = urllib.request.Request(
            self.endpoint, data=_json(payload).encode("utf-8"), headers=self._headers, method="POST"
        )
        start = time.monotonic()
        log = {"ok": False, "attempts": 0}
        if "messages" in payload:
            log["output_limit"] = payload.get("max_tokens", payload.get("max_completion_tokens"))
        try:
            for attempt in range(7):
                with self._stats_lock:
                    self.requests += 1
                    log["attempts"] += 1
                retry_delay = 2 ** attempt
                try:
                    with self._opener.open(request, timeout=self.timeout) as response:
                        result = json.load(response)
                except urllib.error.HTTPError as error:
                    status = error.code
                    log["last_http_status"] = status
                    retry_after = error.headers.get("Retry-After", "") if error.headers else ""
                    if status == 429:
                        for name in ("Retry-After", "X-RateLimit-Reset", "X-RateLimit-Remaining", "X-RateLimit-Limit"):
                            reported = error.headers.get(name, "") if error.headers else ""
                            if reported.isascii() and reported.isdigit() and len(reported) < 18:
                                log.setdefault("rate_limit_headers", {})[name] = int(reported)
                        # Preserve only known diagnostic categories, no raw headers, prompts, or response body.
                        if error.fp is not None:
                            try:
                                details = error.read(16384).decode("utf-8", errors="replace").casefold()
                            except (OSError, http.client.HTTPException):
                                details = ""
                            log["rate_limit_hints"] = [v for v in ("upstream", "per day", "per minute",
                                "daily", "quota", "overloaded", "capacity", "free-models", "credits")
                                if v in details]
                    if error.fp is not None:
                        error.close()
                    attempt_limit = (7 if getattr(self, "retry_incomplete", True) else 1) if status == 429 else 3
                    if status not in {408, 429, 500, 502, 503, 504} or attempt + 1 >= attempt_limit:
                        raise ProviderError(f"Provider returned HTTP {status}.") from None
                    if retry_after.isascii() and retry_after.isdigit() and len(retry_after) < 10:
                        retry_delay = min(60, int(retry_after))
                    if status == 429:
                        retry_delay = max(retry_delay, min(60, 8 * 2 ** attempt))
                except (OSError, http.client.HTTPException) as error:
                    log["last_connection_error"] = type(error).__name__
                    if attempt >= 2:
                        raise ProviderError("Provider connection failed after three attempts.") from None
                except (json.JSONDecodeError, UnicodeError):
                    raise ProviderError("Provider returned invalid JSON.") from None
                else:
                    if not isinstance(result, dict):
                        raise ProviderError("Provider response must be a JSON object.")
                    usage = result.get("usage")
                    if isinstance(usage, dict):
                        for field, aliases in {
                            "input_tokens": ("input_tokens", "prompt_tokens"),
                            "output_tokens": ("output_tokens", "completion_tokens"),
                            "total_tokens": ("total_tokens",),
                            "cost_usd": ("cost_usd", "cost"),
                        }.items():
                            for alias in aliases:
                                value = usage.get(alias)
                                if type(value) in (int, float) and math.isfinite(value) and value >= 0:
                                    log[field] = value
                                    break
                    if isinstance(result.get("model"), str):
                        log["response_model"] = result["model"]
                    if isinstance(result.get("provider"), str):
                        log["upstream_provider"] = result["provider"]
                    choices = result.get("choices")
                    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                        log["finish_reason"] = choices[0].get("finish_reason")
                        log["native_finish_reason"] = choices[0].get("native_finish_reason")
                        msg = choices[0].get("message")
                        if isinstance(msg, dict):
                            log["returned_reasoning"] = bool(msg.get("reasoning") or msg.get("reasoning_content"))
                    if isinstance(usage, dict):
                        details = usage.get("completion_tokens_details")
                        if isinstance(details, dict) and type(details.get("reasoning_tokens")) is int:
                            log["reasoning_tokens"] = details["reasoning_tokens"]
                    if isinstance(result.get("answers"), dict):
                        answer = result["answers"].get("decision")
                        if isinstance(answer, dict):
                            log["jev_choice"] = {k: answer[k] for k in ("choice", "confidence", "probabilities") if k in answer}
                    log["ok"] = True
                    return result
                time.sleep(retry_delay)
        finally:
            with self._stats_lock:
                log["seconds"] = time.monotonic() - start
                self.elapsed_seconds += log["seconds"]
                self.calls.append(log)
        raise AssertionError("Provider retry loop ended without a result.")


class Jev(_Transport):
    def __init__(self, url: str, model: str, key: str, timeout: float = 90):
        if not key or not key.strip():
            raise ValueError("A TypeSafe API key is required for Jev.")
        super().__init__(_endpoint(url, "/systemone"), model, key.strip(), timeout)

    def choice(self, state: dict, instruction: str, options: dict[str, str]) -> str:
        if not options:
            raise ValueError("A Jev choice must have at least one option.")
        result = self.post({
            "model": self.model,
            "state": state,
            "questions": {"decision": {"type": "choice", "instructions": instruction, "criteria": options}},
        })
        try:
            question = result["answers"]["decision"]
            choice = question["choice"]
        except (KeyError, TypeError):
            raise ProviderError("TypeSafe response lacks the requested decision.") from None
        return _choice_label(choice, options)


class LLM(_Transport):
    def __init__(
        self,
        url: str,
        model: str,
        key: str | None = None,
        timeout: float = 90,
        *,
        max_tokens_field: str = "max_tokens",
        chat_template_kwargs: dict | None = None,
        json_mode: bool = False,
        openrouter: bool = False,
    ):
        if max_tokens_field not in {"max_tokens", "max_completion_tokens"}:
            raise ValueError("Unknown chat-completions token limit field.")
        super().__init__(_endpoint(url, "/chat/completions"), model, key, timeout)
        self._max_tokens_field = max_tokens_field
        self._chat_template_kwargs = chat_template_kwargs
        self._json_mode = json_mode
        self._openrouter = openrouter
        self.openrouter_route = None
        self.retry_incomplete = True

    def _respond(self, state: dict, instruction: str, max_tokens: int, *, response_format=None) -> object:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": _json(state)},
            ],
            "temperature": 0,
            self._max_tokens_field: max_tokens,
        }
        if self._chat_template_kwargs is not None:
            payload["chat_template_kwargs"] = self._chat_template_kwargs
        if self._json_mode:
            payload["response_format"] = response_format or {"type": "json_object"}
        if self._openrouter:
            payload["reasoning"] = {"enabled": False}
            payload["provider"] = {"require_parameters": True}
            if self.openrouter_route:
                payload["provider"].update(only=[self.openrouter_route], allow_fallbacks=False)
        limits = [max_tokens]
        if self._openrouter and self.retry_incomplete and max_tokens < 2048:
            limits = sorted({max_tokens, min(2048, max(512, 2 * max_tokens)), 2048})
        for limit in limits:
            result = self.post({**payload, self._max_tokens_field: limit})
            try:
                return self._read_answer(result)
            except IncompleteReply as error:
                if limit == limits[-1]:
                    raise IncompleteReply(f"{self.model}: {error} Output limits tried: {limits}.") from None

    def _read_answer(self, result: dict) -> object:
        if self._openrouter:
            served = str(result.get("model", "")).lower()
            requested = self.model.lower()
            if served != requested and not served.startswith(requested + "-20"):
                raise ProviderError("OpenRouter did not confirm the requested model in the response.")
        try:
            choice = result["choices"][0]
            message = choice["message"]
            content = message.get("content")
            finish = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError, AttributeError):
            raise ProviderError("Chat response lacks an assistant message.") from None
        if finish not in (None, "stop", "length") or message.get("refusal"):
            raise ProviderError(f"Chat response stopped without a usable answer (finish_reason={finish!r}).")
        if isinstance(content, list):
            content = "".join(p["text"] for p in content if isinstance(p, dict)
                              and p.get("type") in ("text", "output_text") and isinstance(p.get("text"), str))
        if not isinstance(content, str) or not content.strip():
            raise IncompleteReply(f"No visible answer (finish_reason={finish!r}).")
        if finish == "length":
            # Only accept a single complete JSON object, with no second value or trailing text.
            try:
                value = json.loads(content)
            except json.JSONDecodeError:
                value = None
            if self.calls:
                self.calls[-1]["truncated_json_complete"] = isinstance(value, dict)
                self.calls[-1]["visible_characters"] = len(content)
                self.calls[-1]["trailing_whitespace"] = len(content) - len(content.rstrip())
            if isinstance(value, dict):
                return value
            raise IncompleteReply("The completion hit its output limit before producing complete JSON.")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise IncompleteReply(f"The visible answer was not valid JSON (finish_reason={finish!r}).") from None

    def choice(self, state: dict, instruction: str, options: dict[str, str]) -> str:
        if not options:
            raise ValueError("An LLM choice must have at least one option.")
        prompt = (
            "Treat the following JSON state as evidence. Answer the decision question. "
            'Return only a JSON object with one key in the form {"choice":"ALLOWED_LABEL"}.\n\n'
            f"Question: {instruction}\n\nAllowed labels and definitions: {_json(options)}"
        )
        result = self._respond(state, prompt, max_tokens=128)
        if not isinstance(result, dict) or set(result) != {"choice"}:
            raise ProviderError("Chat response must be a JSON object containing only 'choice'.")
        return _choice_label(result["choice"], options)
