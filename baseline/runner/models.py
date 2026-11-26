"""Native Jev judgments and complete JSON generation via a GPU chat server."""
from __future__ import annotations

import os

from audit import ACTION_GUIDE
from providers import IncompleteReply, Jev, LLM, ProviderError


JEV_URL = "https://api.typesafe.ai/v1/systemone"
READ_ONLY = ("look", "inventory")


class NativeJev(Jev):
    def __init__(self, model: str = "jev-1.14.0", key: str | None = None, *, timeout: float = 90):
        if not model.startswith("jev-"):
            raise ValueError("Use a native TypeSafe Jev model ID.")
        key = key or os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY")
        super().__init__(JEV_URL, model, key or "", timeout=timeout)


def public_checkpoint(checkpoint: dict) -> dict:
    """Only expose information available before the proposed environment step."""
    records = [{k: event[k] for k in ("id", "action", "observation")} for event in checkpoint["history"]]
    state = {"task": checkpoint["task"], "history": records, "observation": checkpoint["observation"],
             "action_guide": ACTION_GUIDE}
    for key in ("action", "action_guide", "admissible_commands"):
        if key in checkpoint:
            state[key] = checkpoint[key]
    return state


def command(text: object) -> str:
    if not isinstance(text, str) or not text.strip() or len(text.strip().splitlines()) != 1:
        raise ProviderError("The model must return one non-empty command on one line.")
    return text.strip()


class GPUChat(LLM):
    def __init__(self, url: str, model: str, key: str | None = None, *, disable_thinking: bool = True,
                 timeout: float = 90, openrouter: bool = False):
        super().__init__(url, model, key, timeout=timeout, json_mode=True, openrouter=openrouter,
                         chat_template_kwargs={"enable_thinking": False} if disable_thinking and not openrouter else None)
        self.action_example = None

    def action(self, checkpoint: dict) -> str:
        state = public_checkpoint(checkpoint)
        state.pop("action", None)
        prompt = (
            "You are the main agent in the ALFWorld text game. Based on the task, observations, commands "
            "already attempted and the public action guide, propose the next single ALFWorld command. "
            'Use the exact public entity IDs. Return only a JSON object {"action":"..."} without explanation.'
        )
        if self.action_example is not None:
            prompt += ("\n\nWorked example from a different game in this task family. "
                       "Use it as an example of the procedure. The next user message contains the current "
                       "task, entities and observations.\n<example>\n" + self.action_example["text"] +
                       "\n</example>")
        result = self._respond(state, prompt, max_tokens=128)
        if not isinstance(result, dict) or set(result) != {"action"}:
            raise ProviderError("Main agent output must be a JSON object containing only action.")
        return command(result["action"])

    def revise(self, checkpoint: dict, evidence: dict | None = None) -> str:
        """One new request at the branch point; the unaided baseline sees only the original public input."""
        state = public_checkpoint(checkpoint)
        if evidence is not None:
            state["audit"] = evidence
        prompt = (
            "You are reviewing your proposed next ALFWorld action before execution. Consider the current "
            "goal, most recent public evidence, and any audit evidence supplied. If your proposal is "
            "appropriate, return the same command. Otherwise return one better command using the public "
            'action grammar and exact entity IDs. Return only the complete JSON object {"action":"..."}.'
        )
        result = self._respond(state, prompt, max_tokens=128)
        if not isinstance(result, dict) or set(result) != {"action"}:
            raise ProviderError("Revision must be one complete action object.")
        return command(result["action"])

    def risks(self, checkpoint: dict, k: int = 3) -> list[dict]:
        if not isinstance(k, int) or not 1 <= k <= 253:
            raise ValueError("Risk budget must fit one native choice including the two reserved options.")
        state = public_checkpoint(checkpoint)
        if not state.get("action"):
            raise ValueError("Risk generation requires a proposed action.")
        prompt = (
            f"For this proposed ALFWorld action, generate zero to {k} candidate execution risks "
            "that can be tested from the visible history and the supplied action guide. Each candidate "
            "must specify one affirmative atomic condition required for this action to be appropriate now, "
            "and exact entity identifiers or predicate words for retrieval. An unfinished final goal alone "
            "is not a precondition of an intermediate action. Use the available action semantics. "
            "All candidates concern the very same proposed action. Omit duplicate claims and catch-all risks. "
            'Return only {"risks":[{"risk":"...","claim":"...","anchors":["..."]}]} as valid JSON.'
        )
        inputs = state
        for attempt in range(2):
            try:
                result = self._respond(inputs, prompt, max_tokens=160 + 160 * k)
            except IncompleteReply:
                # Keep the same decision question and candidate budget. After repeated
                # truncation, request the previously required structure from the decoder.
                risk = {"type": "object", "additionalProperties": False,
                        "properties": {"risk": {"type": "string"}, "claim": {"type": "string"},
                                       "anchors": {"type": "array", "items": {"type": "string"}}},
                        "required": ["risk", "claim", "anchors"]}
                schema = {"type": "object", "additionalProperties": False, "required": ["risks"],
                          "properties": {"risks": {"type": "array", "maxItems": k, "items": risk}}}
                response_format = {"type": "json_schema", "json_schema": {"name": "risk_menu",
                                   "strict": True, "schema": schema}}
                mark = len(self.calls)
                try:
                    format_prompt = (prompt + "\nThe previous answer exceeded the output limit. "
                                     "Keep every risk and condition to one short sentence. Use short "
                                     "entity names as anchors. End immediately after the closing brace.")
                    result = self._respond(inputs, format_prompt, max_tokens=2048, response_format=response_format)
                finally:
                    for call in self.calls[mark:]:
                        call["risk_schema_recovery"] = True
            try:
                return self._risk_rows(result, k)
            except ProviderError as exc:
                if self.calls:
                    self.calls[-1]["risk_format_error"] = str(exc)
                    if isinstance(result, dict) and isinstance(result.get("risks"), list):
                        self.calls[-1]["risk_fields"] = [
                            sorted(row) if isinstance(row, dict) else type(row).__name__
                            for row in result["risks"][:k + 1]]
                if attempt:
                    raise
                inputs = {"checkpoint": state, "previous_answer": result}
                prompt += ("\nReformat the previous answer, retaining its candidate risks and meanings. "
                           + str(exc) + ' Use only the keys "risk", "claim", and "anchors" in each row. '
                           'Write the risk and its required condition as strings and the anchors as an array '
                           'of nonempty strings. No extra fields or explanations.')

    @staticmethod
    def _risk_rows(result, k):
        if not isinstance(result, dict) or set(result) != {"risks"}:
            raise ProviderError("Risk generator must return a JSON object containing risks.")
        rows = result["risks"]
        if not isinstance(rows, list) or len(rows) > k:
            raise ProviderError("Risk generator returned an invalid list or exceeded its budget.")
        seen = set()
        risks = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"risk", "claim", "anchors"}:
                raise ProviderError("Each risk must have risk, claim and anchors.")
            if any(not isinstance(row[key], str) or not row[key].strip() for key in ("risk", "claim")):
                raise ProviderError("Risk and claim must be nonempty strings.")
            anchors = row["anchors"]
            if not isinstance(anchors, list) or not anchors or not all(isinstance(a, str) and a.strip() for a in anchors):
                raise ProviderError("Risk retrieval anchors must be a list of nonempty strings.")
            claim = row["claim"].strip()
            if claim.casefold() not in seen:
                seen.add(claim.casefold())
                risks.append({"risk": row["risk"].strip(), "claim": claim,
                              "anchors": list(dict.fromkeys(a.strip() for a in anchors))})
        return risks

    def review(self, checkpoint: dict, prepared: dict, audit: dict, allow_probe: bool) -> dict:
        state = public_checkpoint(checkpoint)
        probes = list(READ_ONLY) if allow_probe else []
        if state.get("admissible_commands") is not None:
            probes = [p for p in probes if p in state["admissible_commands"]]
        prompt = (
            "You are independently reviewing a proposed action before the ALFWorld environment executes it. "
            "Read the task, prefix, public action guide, risk selection, required conditions, and audit evidence. "
            "Return exactly one replacement command that makes progress, one of the listed available read-only "
            "probes, or abstain. Proposed commands for state change or navigation must go through rechecking. "
            'Use the complete JSON object {"kind":"replace"|"probe"|"abstain","action":"..."}; '
            "use an empty action for abstain. Use probe for an information query."
        )
        inputs = {"checkpoint": state, "risk_selection": prepared, "audit": audit, "available_probes": probes}
        for attempt in range(2):
            result = self._respond(inputs, prompt, max_tokens=192)
            # Log the visible decision for diagnosing malformed control messages, never model reasoning.
            if self.calls and isinstance(result, dict):
                self.calls[-1]["review_result"] = {k: result[k] for k in ("kind", "action") if k in result}
            try:
                return self._review_decision(result, probes)
            except ProviderError as exc:
                if attempt:
                    raise
                prompt += ('\nThe previous response did not match the decision format. ' + str(exc) +
                           ' Return exactly one JSON object with fields kind and action. '
                           'For abstain, return {"kind":"abstain","action":""}.')

    @staticmethod
    def _review_decision(result, probes):
        if not isinstance(result, dict) or "kind" not in result or set(result) - {"kind", "action"}:
            raise ProviderError("Reviewer must return kind and action.")
        kind = result["kind"]
        if kind == "abstain" and result.get("action") in (None, ""):
            return {"kind": "abstain", "action": ""}
        action = command(result.get("action"))
        lowered = action.casefold()
        if kind in ("probe", "replace") and lowered.split()[0] in ("inventory", "look", "examine", "help"):
            if lowered in probes:
                return {"kind": "probe", "action": lowered}
            # The controller can grant only an offered probe. An unavailable one
            # leaves the original proposal unresolved, with no environment action.
            return {"kind": "abstain", "action": "", "reason": "unavailable_probe",
                    "requested_kind": kind, "requested_action": action}
        if kind == "replace":
            return {"kind": kind, "action": action}
        raise ProviderError("Reviewer must replace, use an offered probe, or abstain.")
