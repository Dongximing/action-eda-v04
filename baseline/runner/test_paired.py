"""Regression checks for paired execution. Fixtures run in temporary directories."""
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from alf_env import Episode, PROBE_GAME
from models import GPUChat, NativeJev
from providers import ProviderError
from paired import digest, judged_action, natural_rollout, replay, rollout_branch, run_game, select_route, slot_for, summarize
from paired_store import CallBook, freeze, load, physical_usage, response_tokens, token_totals
from trajectories import export, trajectory_rows


class PairedTests(unittest.TestCase):
    def test_risk_schema_correction_retains_budget_and_rejects_invalid_repair(self):
        actor = GPUChat("http://127.0.0.1:8000/v1", "fixture-9b")
        cp = {"task": "clean a cup", "history": [], "observation": "cup 1", "action": "take cup 1 from table 1"}
        row = {"risk": "Cup may be absent", "claim": "The cup is on the table", "anchors": ["cup 1"]}
        malformed = {"risks": [{"candidate": row["risk"]}]}
        with patch.object(actor, "_respond", side_effect=[malformed, {"risks": [row]}]) as ask:
            self.assertEqual(actor.risks(cp, k=1), [row])
            self.assertEqual(ask.call_count, 2)
            self.assertEqual(ask.call_args.args[0]["previous_answer"], malformed)
        over_budget = {"risks": [row, row]}
        with patch.object(actor, "_respond", return_value=over_budget) as ask:
            with self.assertRaises(ProviderError):
                actor.risks(cp, k=1)
            self.assertEqual(ask.call_count, 2)

    def test_reviewer_respects_probe_budget_and_repairs_malformed_envelopes(self):
        actor = GPUChat("http://127.0.0.1:8000/v1", "fixture-9b")
        cp = {"task": "clean a knife", "observation": "A countertop.", "history": []}
        for reply, available, expected in [
            ({"kind": "abstain", "action": None}, True, {"kind": "abstain", "action": ""}),
            ({"kind": "replace", "action": "LOOK"}, True, {"kind": "probe", "action": "look"}),
            ({"kind": "probe", "action": "inventory"}, False,
             {"kind": "abstain", "action": "", "reason": "unavailable_probe",
              "requested_kind": "probe", "requested_action": "inventory"}),
        ]:
            with self.subTest(reply=reply), patch.object(actor, "_respond", return_value=reply):
                self.assertEqual(actor.review(cp, {}, {}, available), expected)
        with patch.object(actor, "_respond", side_effect=[{}, {"kind": "replace", "action": "go to drawer 1"}]) as send:
            self.assertEqual(actor.review(cp, {}, {}, False), {"kind": "replace", "action": "go to drawer 1"})
            self.assertEqual(send.call_count, 2)
        with patch.object(actor, "_respond", return_value={}) as send, self.assertRaises(ProviderError):
            try:
                actor.review(cp, {}, {}, False)
            finally:
                self.assertEqual(send.call_count, 2)

    def test_preflight_skips_reasoning_provider_and_pins_the_same_endpoint_on_resume(self):
        actor = GPUChat("https://openrouter.ai/api/v1", "qwen/qwen3.5-9b", openrouter=True)
        sent = []
        def reply(request, timeout):
            body = json.loads(request.data)
            route, = body["provider"]["only"]
            self.assertFalse(body["provider"]["allow_fallbacks"])
            self.assertEqual(body["reasoning"], {"enabled": False})
            sent.append(route)
            action = "main agent" in body["messages"][0]["content"]
            answer = {"action": "look"} if action else {"choice": "yes"}
            result = {"model": actor.model, "provider": route, "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(answer)}}],
                      "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                                "completion_tokens_details": {"reasoning_tokens": int(route == "deepinfra")}}}
            return io.BytesIO(json.dumps(result).encode())
        with tempfile.TemporaryDirectory() as tmp, patch("paired.Episode") as env, patch.object(actor._opener, "open", side_effect=reply):
            env.return_value.reset.return_value = {"task": "move a cup", "observation": "cup 1", "history": [
                {"id": "r0", "action": "reset", "observation": "cup 1"}]}
            for _ in range(2):
                self.assertEqual(select_route(Path(tmp), actor, Path("fixture")), "siliconflow")
            self.assertEqual(sent, ["deepinfra", "deepinfra", "siliconflow", "siliconflow"])
            self.assertEqual(len(load(Path(tmp) / "routing.json")["checks"]), 2)

    def test_openrouter_recovery_bills_every_completion_and_caches_only_the_final_answer(self):
        client = GPUChat("https://openrouter.ai/api/v1", "qwen/qwen3.5-9b", openrouter=True)
        cp = {"task": "clean a knife", "history": [], "observation": "A countertop."}
        payloads = []
        def reply(request, timeout):
            payloads.append(json.loads(request.data))
            responses = [
                ("length", None, 128),
                ("stop", [], 20),
                ("stop", [{"type": "text", "text": '{"action":"look"}'}], 6),
            ]
            reason, content, tokens = responses[len(payloads) - 1]
            result = {"model": client.model, "choices": [{"finish_reason": reason,
                      "message": {"content": content, "reasoning": '{"action":"wrong"}'}}],
                      "usage": {"prompt_tokens": 7, "completion_tokens": tokens,
                                "completion_tokens_details": {"reasoning_tokens": 2}}}
            return io.BytesIO(json.dumps(result).encode())
        with tempfile.TemporaryDirectory() as tmp, patch.object(client._opener, "open", side_effect=reply):
            path = Path(tmp) / "calls.sqlite"
            book = CallBook(path)
            try:
                for _ in range(2):
                    answer = book.ask("direct", "qwen", "actor", cp, client, lambda: client.action(cp))
                    self.assertEqual(answer, "look")
                self.assertEqual([p["max_tokens"] for p in payloads], [128, 512, 2048])
                self.assertEqual(len({json.dumps(p["messages"]) for p in payloads}), 1)
                stats = physical_usage(path)[("direct", "qwen")]
                self.assertEqual((stats["attempts"], stats["output_tokens"]), (3, 154))
                self.assertEqual(book.standalone_tokens([], after=0)["totals"]["output_tokens"], 154)
                self.assertEqual(client.calls[0]["finish_reason"], "length")
                self.assertEqual(client.calls[0]["reasoning_tokens"], 2)
            finally:
                book.close()

    def test_openrouter_recovery_stops_at_cap_and_respects_filtering(self):
        client = GPUChat("https://openrouter.ai/api/v1", "qwen/qwen3.5-9b", openrouter=True)
        for reason, expected in [("length", 3), ("content_filter", 1)]:
            reply = {"model": client.model, "choices": [{"finish_reason": reason, "message": {"content": None}}]}
            with patch.object(client, "post", return_value=reply) as post, self.assertRaises(ProviderError):
                client.choice({}, "Choose", {"yes": "Yes"})
            self.assertEqual(post.call_count, expected)
        with patch.object(client, "post", return_value={"model": "wrong-model"}) as post, self.assertRaises(ProviderError):
            client.choice({}, "Choose", {"yes": "Yes"})
        self.assertEqual(post.call_count, 1)

    def test_missing_usage_is_not_zero(self):
        reported = response_tokens({"input_tokens": 7, "output_tokens": 3})
        self.assertEqual(reported["total_tokens"], 10)
        partly_reported = response_tokens({"input_tokens": 4})
        total = token_totals([reported, partly_reported])
        self.assertEqual((total["input_tokens"], total["requests_missing_usage"]), (11, 1))
        self.assertIsNone(total["output_tokens"])
        self.assertIsNone(total["total_tokens"])

    def test_9b_reviews_only_when_evidence_requires_it(self):
        cp = {"task": "clean the knife", "action": "clean butterknife 1 with sinkbasin 1",
              "observation": "You arrive at countertop 2.", "history": [
                  {"id": "r0", "action": "reset", "observation": "There is a sinkbasin 1."},
                  {"id": "r1", "action": "go to countertop 2", "observation": "You arrive at countertop 2."}]}
        actor = GPUChat("http://127.0.0.1:8000/v1", "fixture-9b")
        def choose(state, question, options):
            return "none" if "none" in options else "no"
        with tempfile.TemporaryDirectory() as tmp:
            db = CallBook(Path(tmp) / "calls.sqlite")
            try:
                with patch.object(actor, "risks", return_value=[]), patch.object(actor, "choice", side_effect=choose), \
                     patch.object(actor, "revise", return_value="go to sinkbasin 1") as revise:
                    trace = []
                    choice = judged_action(cp, "llm_eda", actor, None, db, trace)
                    self.assertEqual(choice, "go to sinkbasin 1")
                    revise.assert_called_once()
                    self.assertEqual(revise.call_args.args[1]["status"], "CONTRADICTED")
                    self.assertIn("revise", db.standalone_tokens([], after=0)["by_operation"])
            finally:
                db.close()

    def test_rejected_replacement_is_audited_before_abstaining(self):
        cp = {"task": "clean a knife", "action": "clean knife 1 with sinkbasin 1",
              "observation": "You are at countertop 1.", "history": [
                  {"id": "r0", "action": "reset", "observation": "You are at countertop 1."}]}
        actor = GPUChat("http://127.0.0.1:8000/v1", "fixture-9b")
        replacement = "take knife 1 from countertop 1"
        def judge(state, instruction, options):
            return "none" if "none" in options else "no"
        with tempfile.TemporaryDirectory() as tmp:
            book = CallBook(Path(tmp) / "calls.sqlite")
            try:
                with patch.object(actor, "risks", return_value=[]), patch.object(actor, "choice", side_effect=judge), \
                     patch.object(actor, "review", return_value={"kind": "replace", "action": replacement}) as review:
                    trace = []
                    result = judged_action(cp, "llm_eda", actor, None, book, trace, query=self.fail)
                    self.assertIsNone(result)
                    self.assertEqual([r["action"] for r in trace if "audit" in r], [cp["action"], replacement])
                    self.assertEqual(review.call_count, 1)
            finally:
                book.close()

    def test_first_write_and_first_process_are_distinct(self):
        self.assertEqual(slot_for("take mug 1 from shelf 2"), "first_other_write")
        self.assertEqual(slot_for("clean mug 1 with sinkbasin 1"), "first_process")
        self.assertIsNone(slot_for("go to shelf 2"))

    def test_complete_actions_and_native_choice_contract(self):
        checkpoint = {"task": "clean the knife", "history": [], "observation": "at the counter",
                      "action": "clean butterknife 1 with sinkbasin 1"}
        actor = GPUChat("http://127.0.0.1:8000/v1", "Qwen/Qwen3.5-9B")
        answer = {"choices": [{"message": {"content": '{"action":"go to sinkbasin 1"}'}}]}
        with tempfile.TemporaryDirectory() as tmp:
            book = CallBook(Path(tmp) / "calls.sqlite")
            try:
                with patch.object(actor, "post", return_value=answer) as transport:
                    self.assertEqual(judged_action(checkpoint, "direct", actor, None, book, []), checkpoint["action"])
                    transport.assert_not_called()
                    chosen = judged_action(checkpoint, "self_revise", actor, None, book, [])
                    self.assertEqual(chosen, "go to sinkbasin 1")
                    outgoing = transport.call_args.args[0]
                    self.assertEqual(len(transport.call_args_list), 1)
                    state = json.loads(outgoing["messages"][1]["content"])
                    self.assertEqual(state["action"], checkpoint["action"])
                    self.assertNotIn("audit", state)
                    self.assertNotIn("logprobs", outgoing)
                    self.assertEqual(judged_action(checkpoint, "self_revise", actor, None, book, []), chosen)
                    self.assertEqual(len(transport.call_args_list), 1)
            finally:
                book.close()
        native = NativeJev(key="offline-test-placeholder")
        with patch.object(native, "post", return_value={"answers": {"decision": {"choice": "ok"}}}) as post:
            self.assertEqual(native.choice({"record": "at the sink"}, "Which state?", {"ok": "At sink"}), "ok")
            self.assertEqual(post.call_args.args[0]["questions"]["decision"]["type"], "choice")

    def test_resume_and_empty_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "protocol.json"
            freeze(path, {"slots": ("first", "second")})
            freeze(path, {"slots": ("first", "second")})
            with self.assertRaises(ValueError):
                freeze(path, {"slots": ["second", "first"]})
            db = Path(tmp) / "initializing.sqlite"
            sqlite3.connect(db).close()
            self.assertEqual(physical_usage(db), {})


@unittest.skipUnless(os.getenv("ALFWORLD_VALID_SEEN"), "Set ALFWORLD_VALID_SEEN for real environment tests.")
class EnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = Path(os.environ["ALFWORLD_VALID_SEEN"]) / PROBE_GAME
        source = Path(__file__).parent / "smoke/prefixes.jsonl"
        cls.rows = [json.loads(line) for line in source.read_text().splitlines()]

    def test_all_real_replays_and_corrupted_hash(self):
        env = Episode(self.game)
        try:
            for row in self.rows:
                prefix, action = row["prefix"], row["proposed_action"]
                fork = {"prefix": prefix, "proposal": action, "step": len(prefix["history"]) - 1,
                        "hash": digest([prefix, action])}
                self.assertEqual(replay(env, fork), prefix)
                with self.assertRaises(ValueError):
                    replay(env, {**fork, "hash": "wrong"})
        finally:
            env.close()

    def test_full_game_9b_vs_9b_costs_and_resume(self):
        split = Path(os.environ["ALFWORLD_VALID_SEEN"])
        family = "pick_clean_then_place_in_recep"
        demo = load(Path(__file__).parent / "one_shot_examples.json")["examples"][family]
        row = {"id": "game01", "family": family, "game": str(PROBE_GAME),
               "action_example_id": demo["id"], "action_example_sha256": digest(demo)}
        script = [r["action"] for r in self.rows[1]["prefix"]["history"][1:]]
        script += [self.rows[1]["proposed_action"], "go to countertop 2", "move butterknife 1 to countertop 2"]
        actor = GPUChat("http://127.0.0.1:8000/v1", "fixture-9b", openrouter=True)

        def offline_transport(payload):
            self.assertEqual(payload["model"], actor.model)
            self.assertNotIn("logprobs", payload)
            instruction, public = (m["content"] for m in payload["messages"])
            state = json.loads(public)
            self.assertEqual(instruction.count(demo["text"]), int(instruction.startswith("You are the main agent")))
            self.assertNotIn(demo["text"], public)
            if instruction.startswith("You are the main agent"):
                value = {"action": script[len(state["history"]) - 1]}
            elif instruction.startswith("For this proposed ALFWorld action"):
                value = {"risks": []}
            elif "Which possible issue" in instruction:
                value = {"choice": "none"}
            else:
                self.assertIn("record", state)
                value = {"choice": "yes"}
            actor.calls.append({"ok": True, "attempts": 1, "seconds": 0, "input_tokens": 11, "output_tokens": 2})
            return {"model": actor.model, "choices": [{"message": {"content": json.dumps(value)}}]}

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            arms = ("direct", "llm_eda")
            job = (out, split, row, arms, "openrouter", len(script), "", "episode")
            with patch("paired.resources", return_value=actor), patch("paired.NativeJev", side_effect=AssertionError), \
                 patch.object(actor, "post", side_effect=offline_transport) as post:
                run_game((*job[:3], ("direct",), *job[4:]))
                self.assertFalse((out / "game01/episode_start/llm_eda.json").exists())
                run_game((*job[:3], ("llm_eda",), *job[4:]))
                billed = post.call_count
                run_game(job)
                self.assertEqual(post.call_count, billed)
            report = summarize(out, [row], arms, "episode")
            direct, eda = (report["results"][a] for a in arms)
            self.assertEqual((direct["successes"], eda["successes"], eda["actions_reviewed"]), (1, 1, 3))
            self.assertEqual(set(direct["tokens_by_operation"]), {"actor"})
            self.assertEqual(direct["tokens_by_operation"]["actor"], eda["tokens_by_operation"]["actor"])
            self.assertEqual(direct["standalone_tokens"]["total_tokens"], 13 * len(script))
            self.assertEqual(set(eda["tokens_by_operation"]), {"actor", "risk_menu", "select_risk", "eda_source", "eda_delta"})
            self.assertEqual(sum(g["total_tokens"] for g in report["physical_api_usage"]), 13 * billed)
            # Each distinct method request was either physically sent by llm_eda
            # or already sent by the direct actor for this identical trajectory.
            self.assertEqual(eda["standalone_tokens"]["total_tokens"], billed * 13)
            delta = report["paired_contrasts"]["llm_eda_vs_direct"]["extra_total_tokens"]
            self.assertEqual(delta, eda["standalone_tokens"]["total_tokens"] - 13 * len(script))
            self.assertEqual(export(out), 2)
            folder = out / "game01/episode_start"
            for arm in arms:
                lines = [json.loads(s) for s in (folder / f"{arm}.trajectory.jsonl").read_text().splitlines()]
                self.assertEqual(lines[0]["event"], "reset")
                self.assertEqual(lines[0]["action_example_sha256"], digest(demo))
                self.assertEqual([r["executed_action"] for r in lines[1:-1]], script)
                observations = [r["observation"] for r in load(folder / f"{arm}.json")["suffix"]]
                self.assertEqual([r["observation"] for r in lines[1:-1]], observations)
                self.assertEqual(lines[-1]["won"], True)
                self.assertEqual(lines[-1]["token_usage"]["totals"], report["results"][arm]["standalone_tokens"])
                self.assertEqual(sum("review" in row for row in lines), 3 if arm == "llm_eda" else 0)
            path = folder / "llm_eda.trajectory.jsonl"
            before = path.read_bytes()
            self.assertEqual(export(out), 2)
            self.assertEqual(path.read_bytes(), before)

    def test_real_probe_consumes_a_step_and_triggers_a_fresh_audit(self):
        split = Path(os.environ["ALFWORLD_VALID_SEEN"])
        row = {"id": "sample", "family": "clean", "game": str(PROBE_GAME)}
        actor = GPUChat("http://127.0.0.1:8000/v1", "fixture-9b")
        original = "take butterknife 1 from countertop 2"
        def judge(state, instruction, options):
            return "none" if "none" in options else "unknown"
        for maximum in (1, 3):
            with self.subTest(maximum=maximum), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                job = (out, split, row, ("direct", "llm_eda"), "openrouter", maximum, "", "episode")
                answers = [{"kind": "probe", "action": "inventory"}, {"kind": "abstain", "action": ""}]
                with patch("paired.resources", return_value=actor), patch.object(actor, "action", return_value=original), \
                     patch.object(actor, "risks", return_value=[]) as risks, patch.object(actor, "choice", side_effect=judge), \
                     patch.object(actor, "review", side_effect=answers) as review:
                    run_game(job)
                result = load(out / "sample/episode_start/llm_eda.json")
                fork = load(out / "sample/episode_start/prefix.json")
                rows = list(trajectory_rows(fork, result, "sample"))
                self.assertEqual([r["event"] for r in rows], ["reset", "probe", "not_executed", "end"])
                self.assertEqual((rows[1]["proposed_action"], rows[1]["executed_action"]), (original, "inventory"))
                self.assertIsNone(rows[2]["executed_action"])
                self.assertEqual(result["total_env_steps"], 1)
                self.assertEqual([r["action"] for r in result["suffix"]], ["inventory"])
                self.assertEqual(result["end"], "step_limit" if maximum == 1 else "abstain")
                self.assertEqual(review.call_args_list[0].args[3], True)
                if maximum > 1:
                    self.assertEqual(review.call_args_list[1].args[3], False)
                    rechecked = risks.call_args_list[1].args[0]
                    self.assertEqual(rechecked["action"], original)
                    self.assertEqual(rechecked["history"][-1]["action"], "inventory")

    def test_paired_branches_in_real_game(self):
        row = {"id": "sample", "family": "clean", "game": str(PROBE_GAME)}
        scripted = [r["action"] for r in self.rows[1]["prefix"]["history"][1:]] + [self.rows[1]["proposed_action"]]
        maximum = len(scripted)
        actor = GPUChat("http://127.0.0.1:8000/v1", "offline-test-fixture")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / row["id"]
            folder.mkdir()
            book = CallBook(folder / "calls.sqlite")
            try:
                def action(cp):
                    return scripted[len(cp["history"]) - 1]
                with patch.object(actor, "action", side_effect=action) as propose, \
                     patch.object(actor, "revise", side_effect=lambda cp, evidence: cp["action"]) as revise:
                    natural = natural_rollout(folder, self.game, row, actor, book, maximum)
                    self.assertEqual(set(natural["selected"]), {"first_other_write", "first_process"})
                    for slot in natural["selected"]:
                        work = folder / slot
                        fork = load(work / "prefix.json")
                        for arm in ("direct", "self_revise"):
                            rollout_branch(work, self.game, fork, natural, arm, actor, None, book, maximum)
                        direct, revised = (load(work / f"{arm}.json") for arm in ("direct", "self_revise"))
                        self.assertEqual(direct["suffix"], revised["suffix"])
                        self.assertEqual(direct["total_env_steps"], maximum)
                        self.assertEqual(direct["intervention"], [])
                        self.assertEqual(len(revised["intervention"]), 1)
                    self.assertEqual(propose.call_count, maximum)
                    self.assertEqual(revise.call_count, 2)
                report = summarize(root, [row], ["direct", "self_revise"])
                self.assertTrue(report["requested_arms_complete"])
                self.assertEqual(report["paired_contrasts"]["self_revise_vs_direct"]["paired_prefixes"], 2)
            finally:
                book.close()

    def test_rescue_scored_on_matching_prefix_only(self):
        row = {"id": "sample", "family": "clean", "game": str(PROBE_GAME)}
        # The fourth scripted command leaves the sink. Only going back at the
        # fork will allow the shared continuation to clean and place the knife.
        script = [r["action"] for r in self.rows[2]["prefix"]["history"][1:]]
        clean = self.rows[2]["proposed_action"]
        script += [clean, clean, "go to countertop 2", "move butterknife 1 to countertop 2"]
        actor = GPUChat("http://127.0.0.1:8000/v1", "offline-test-fixture")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / row["id"]
            folder.mkdir()
            book = CallBook(folder / "calls.sqlite")
            try:
                with patch.object(actor, "action", side_effect=lambda cp: script[len(cp["history"]) - 1]), \
                     patch.object(actor, "revise", return_value="go to sinkbasin 1") as revise:
                    natural = natural_rollout(folder, self.game, row, actor, book, len(script))
                    work = folder / "first_process"
                    fork = load(work / "prefix.json")
                    for arm in ("direct", "self_revise"):
                        rollout_branch(work, self.game, fork, natural, arm, actor, None, book, len(script))
                    self.assertEqual(revise.call_count, 1)
                report = summarize(root, [row], ["direct", "self_revise"])
                change = report["paired_contrasts"]["self_revise_vs_direct"]
                self.assertEqual((change["rescued"], change["lost"], change["paired_prefixes"]), (1, 0, 1))
                rows = list(trajectory_rows(fork, load(work / "self_revise.json"), "sample"))
                changed = [r for r in rows if r["event"] == "action" and r["proposed_action"] != r["executed_action"]]
                self.assertEqual([(r["proposed_action"], r["executed_action"]) for r in changed],
                                 [(clean, "go to sinkbasin 1")])
                self.assertFalse(report["requested_arms_complete"])
            finally:
                book.close()


if __name__ == "__main__":
    unittest.main()
