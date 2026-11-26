"""Tests for data builders, ALFWorld tracker and the context option (no model)."""
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aeda import alfworld as A  # noqa: E402
from aeda import prompts as P  # noqa: E402
from aeda.backends import TableBackend  # noqa: E402
from aeda.schema import load_labels, load_samples  # noqa: E402
from aeda.verifiers import Config, Meter, m_T0, preceding, run  # noqa: E402

PY = sys.executable


class TestDiagnostic(unittest.TestCase):
    def test_generator_labels_consistent(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([PY, str(ROOT / "scripts/make_diagnostic.py"), "--out", d, "--n-per-cell", "1",
                            "--distract", "0,2"], check=True, capture_output=True)
            samples = load_samples(Path(d) / "samples.jsonl")
            labels = load_labels(Path(d) / "labels.jsonl")
            self.assertEqual(len(labels), sum(len(s.claims) for s in samples))
            for s in samples:
                lab = labels[(s.sid, s.claims[0].cid)]
                cell = lab.extra["cell"]
                self.assertEqual(lab.order_sensitive, cell in ("reest", "reest_inv", "def_resume"))
                self.assertEqual(lab.gold == "CONTRADICTED", cell in ("inv", "reest_inv", "comp", "def_withdraw"))
                # gold never appears in the visible sample
                self.assertNotIn("gold", json.dumps(s.__dict__, default=lambda o: o.__dict__))


class TestAlfworld(unittest.TestCase):
    def test_parse_and_replay(self):
        self.assertEqual(A.parse_action("put knife 1 in/on countertop 1"), ("put", ("knife 1", "countertop 1")))
        self.assertEqual(A.parse_action("clean knife 1 with sinkbasin 1"), ("clean", ("knife 1", "sinkbasin 1")))
        st = A.replay([("go to countertop 2", "You arrive at countertop 2."),
                       ("take knife 1 from countertop 2", "You pick up the knife 1."),
                       ("go to sinkbasin 1", "Nothing happens.")])
        self.assertEqual((st.loc, st.holding), ("countertop 2", "knife 1"))

    def test_converter_and_t0(self):
        traj = ROOT / "data/alfworld_example/trajectories.jsonl"
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([PY, str(ROOT / "scripts/convert_alfworld.py"), "--traj", str(traj), "--out", d],
                           check=True, capture_output=True)
            samples = load_samples(Path(d) / "samples.jsonl")
            labels = load_labels(Path(d) / "labels.jsonl")
            rows = run(samples, ["T0"], TableBackend({}), Config())
            self.assertTrue(all(r["verdict"] == labels[(r["sid"], r["cid"])].gold for r in rows))
            # the failed first clean is the one contradicted location claim
            bad = [l for l in labels.values() if l.gold == "CONTRADICTED"]
            self.assertEqual(len(bad), 1)
            self.assertFalse(bad[0].extra["action_succeeded"])
            # no future records in the prefix: the failed action itself is absent
            s = next(x for x in samples if x.sid == bad[0].sid)
            self.assertFalse(any("Nothing happens" in r.text for r in s.records))

    def test_t0_without_spec_is_unknown(self):
        s = load_samples(ROOT / "data/smoke/samples.jsonl")[0]
        self.assertEqual(m_T0(s, s.claims[0], Meter(TableBackend({})), Config(), {})[0], "UNKNOWN")


class TestContext(unittest.TestCase):
    def test_context_block_only_when_k_positive(self):
        s = load_samples(ROOT / "data/smoke/samples.jsonl")[0]
        c, r = s.claims[0], s.records[2]
        self.assertNotIn("Preceding records", P.record_judgment(s.task, s.proposed_action, c, r).render())
        self.assertEqual([x.rid for x in preceding(s, r, 2)], [1, 2])
        self.assertEqual(preceding(s, s.records[0], 3), [])
        txt = P.record_judgment(s.task, s.proposed_action, c, r, preceding(s, r, 1)).render()
        self.assertIn("Preceding records", txt)
        self.assertIn("Record to judge: [#3", txt)


if __name__ == "__main__":
    unittest.main()


class TestPrompts(unittest.TestCase):
    def test_mcq_parts_render_and_letters(self):
        s = load_samples(ROOT / "data/smoke/samples.jsonl")[0]
        c = s.claims[0]
        for mcq in [P.record_judgment(s.task, s.proposed_action, c, s.records[0]),
                    P.pair_judgment(s.task, s.proposed_action, c, s.records[0], s.records[1]),
                    P.holistic_judgment(s.task, s.proposed_action, c, s.records),
                    P.q_source(s.task, s.proposed_action, c, s.records[0]),
                    P.map_claim_choice(c, [("user", "request"), ("r1", "status")])]:
            txt = mcq.render()
            self.assertTrue(txt.endswith("Answer with a single letter."))
            for l, t in mcq.options:
                self.assertIn(f"{l}. {t}", txt)
        self.assertEqual(P.map_claim_choice(c, [("a", "b")]).letters, ["A", "Z"])


class TestPairedOutputs(unittest.TestCase):
    def test_natural_json_conversion(self):
        nat = {"game": "g", "family": "pick_clean_then_place_in_recep", "task": "put a clean knife in drawer.",
               "won": False, "end": "step_limit", "history": [
                   {"id": "r0", "action": "reset", "observation": "You see a countertop 1, a drawer 1."},
                   {"id": "r1", "action": "take knife 1 from countertop 1", "observation": "Nothing happens."},
                   {"id": "r2", "action": "go to countertop 1", "observation": "You arrive at countertop 1."},
                   {"id": "r3", "action": "take knife 1 from countertop 1", "observation": "You pick up the knife 1."},
                   {"id": "r4", "action": "move knife 1 to drawer 1", "observation": "Nothing happens."}]}
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src" / "game01"
            src.mkdir(parents=True)
            (src / "natural.json").write_text(json.dumps(nat))
            out = Path(d) / "out"
            subprocess.run([PY, str(ROOT / "scripts/convert_paired_outputs.py"), "--src", str(src.parent),
                            "--out", str(out)], check=True, capture_output=True)
            samples = load_samples(out / "samples.jsonl")
            labels = load_labels(out / "labels.jsonl")
            self.assertEqual([s.proposed_action for s in samples],
                             ["take knife 1 from countertop 1", "take knife 1 from countertop 1",
                              "move knife 1 to drawer 1"])
            gold = {(k[0], labels[k].extra["spec_type"]): labels[k].gold for k in labels}
            self.assertEqual(gold[("game01-t0", "at")], "CONTRADICTED")     # never went to countertop 1
            self.assertEqual(gold[("game01-t2", "at")], "SUPPORTED")
            self.assertEqual(gold[("game01-t3", "at")], "CONTRADICTED")     # at countertop 1, not drawer 1
            self.assertEqual(gold[("game01-t3", "holding")], "SUPPORTED")
            self.assertFalse(labels[("game01-t3", "game01-t3/c1")].extra["action_succeeded"])
            # the record list is the prefix only: the failed move itself is not visible
            self.assertEqual(len(samples[-1].records), 4)
            rows = run(samples, ["T0"], TableBackend({}), Config())
            run_dir = Path(d) / "run"
            run_dir.mkdir()
            (run_dir / "predictions.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
            r = subprocess.run([PY, str(ROOT / "scripts/action_level.py"), "--labels", str(out / "labels.jsonl"),
                                "--run", str(run_dir)], check=True, capture_output=True, text=True)
            self.assertIn("| T0 | env | 2 | 2 | 0 | 0 |", r.stdout)


class TestTypesafeAdapter(unittest.TestCase):
    def test_probabilities_and_missing_key(self):
        import os
        from unittest import mock
        from adapters import typesafe_jev as T
        self.assertEqual(T._probs({"probabilities": {"A": .7, "B": .2, "C": .1}}, ["A", "B", "C"]),
                         {"A": .7, "B": .2, "C": .1})
        self.assertIsNone(T._probs({"probabilities": {"A": 1.0}}, ["A", "B"]))
        self.assertEqual(T._probs({"probabilities": [.5, .5]}, ["A", "B"]), {"A": .5, "B": .5})
        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": "", "JEV_API_KEY": ""}):
            with self.assertRaises(RuntimeError):
                T.choose("ctx", "q?", [("A", "a"), ("B", "b")])

    def test_request_shape_and_letter_answer(self):
        import os
        from unittest import mock
        from adapters import typesafe_jev as T
        seen = {}

        def fake_post(payload, **kw):
            seen.update(payload)
            return {"answers": {"decision": {"choice": "B"}}}
        with mock.patch.object(T, "_post", fake_post), mock.patch.dict(os.environ, {"JEV_MODEL": "jev-x"}):
            self.assertEqual(T.choose("records", "What does it do?", [("A", "est"), ("B", "inv")]), "B")
        q = seen["questions"]["decision"]
        self.assertEqual((seen["model"], seen["state"], q["type"], q["criteria"]),
                         ("jev-x", {"context": "records"}, "choice", {"A": "est", "B": "inv"}))


class TestOpenRouterAdapter(unittest.TestCase):
    def test_logprobs_letter_fallback_and_request(self):
        import os
        from unittest import mock
        from adapters import openrouter_chat as O
        lp = {"choices": [{"message": {"content": "B"}, "logprobs": {"content": [{"token": "B", "logprob": -0.1,
              "top_logprobs": [{"token": "B", "logprob": -0.1}, {"token": " A", "logprob": -2.5},
                               {"token": "Hmm", "logprob": -3.0}]}]}}]}
        s = O.letter_scores(lp, ["A", "B", "C"])
        self.assertAlmostEqual(s["B"], math.exp(-0.1))
        self.assertAlmostEqual(s["A"], math.exp(-2.5))
        self.assertEqual(s["C"], 0.0)
        self.assertIsNone(O.letter_scores({"choices": [{"message": {"content": "A"}}]}, ["A", "B"]))
        self.assertEqual(O.parse_letter("C", ["A", "B", "C"]), "C")
        self.assertEqual(O.parse_letter("<think></think>\n\nB.", ["A", "B", "C"]), "B")
        self.assertEqual(O.parse_letter("The answer is A", ["A", "B", "C"]), "A")
        with self.assertRaises(ValueError):
            O.parse_letter("Both A and B", ["A", "B", "C"])
        seen = {}

        def fake_post(payload, **kw):
            seen.update(payload)
            return {"choices": [{"message": {"content": "A"}}]}
        with mock.patch.object(O, "_post", fake_post), mock.patch.dict(os.environ, {"OR_PROVIDER": "parasail"}):
            self.assertEqual(O.choose("ctx", "q?", [("A", "x"), ("B", "y")]), "A")
            self.assertEqual(O.describe(), "openrouter/qwen/qwen3.5-9b@parasail")
        self.assertEqual(seen["provider"], {"order": ["parasail"], "allow_fallbacks": False})
        self.assertTrue(seen["messages"][1]["content"].endswith("Answer with a single letter."))
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
            with self.assertRaises(RuntimeError):
                O.choose("ctx", "q?", [("A", "x"), ("B", "y")])


class TestThreadedRun(unittest.TestCase):
    def test_workers_give_same_rows(self):
        from aeda.backends import AdapterBackend
        samples = load_samples(ROOT / "data/smoke/samples.jsonl")
        meths = ["H1", "U1", "D1", "D2", "P0", "Q0"]
        seq = run(samples, meths, AdapterBackend("tests.fake_jev:good"), Config())
        par = run(samples, meths, AdapterBackend("tests.fake_jev:good"), Config(), workers=4)
        self.assertEqual(seq, par)
        self.assertTrue(AdapterBackend("tests.fake_jev:good").name.startswith("api:"))


class TestFewshot(unittest.TestCase):
    def test_build_and_use(self):
        from aeda.verifiers import load_fewshot
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "fs.json"
            subprocess.run([PY, str(ROOT / "scripts/make_fewshot.py"), "--out", str(out)], check=True,
                           capture_output=True)
            ex = json.loads(out.read_text())["examples"]
            self.assertEqual([e["answer"] for e in ex].count("C"), 2)
            self.assertEqual(len(ex), 8)
            s = load_samples(ROOT / "data/smoke/samples.jsonl")[0]
            c, r = s.claims[0], s.records[0]
            plain = P.record_judgment(s.task, s.proposed_action, c, r).render()
            shot = P.record_judgment(s.task, s.proposed_action, c, r, None, list(load_fewshot(str(out)))).render()
            self.assertNotIn("Worked examples", plain)
            self.assertIn("Example 8", shot)
            self.assertTrue(shot.endswith(plain.split("\n", 1)[1]))  # same real case after the examples
            # the CLI flag reaches the prompts: calls are made with a different (longer) prompt
            base = [PY, str(ROOT / "scripts/run_offline.py"), "--samples", str(ROOT / "data/smoke/samples.jsonl"),
                    "--backend", "api", "--adapter", "tests.fake_jev:good", "--methods", "D1"]
            subprocess.run(base + ["--out", f"{d}/r0"], check=True, capture_output=True, cwd=ROOT)
            subprocess.run(base + ["--out", f"{d}/r1", "--fewshot", str(out)], check=True, capture_output=True,
                           cwd=ROOT)
            ch = [sum(json.loads(l)["prompt_chars"] for l in open(f"{d}/{x}/predictions.jsonl")) for x in ("r0", "r1")]
            self.assertGreater(ch[1], ch[0])
            self.assertEqual(json.loads(Path(f"{d}/r1/run_meta.json").read_text())["config"]["fewshot"], str(out))


class TestStateStyle(unittest.TestCase):
    def test_state_options_and_wiring(self):
        q, o = P.state_options("x", {"type": "at", "loc": "fridge 1"})
        self.assertEqual((q, [l for l, _ in o], o[0][1]), ("Right after this record, where is the agent?",
                                                          ["A", "B", "C"], "At fridge 1."))
        self.assertEqual(P.state_options("x", {"type": "hand_empty"})[1][0][1], "Nothing.")
        self.assertIn("is this true: user wants it", P.state_options("user wants it", None)[0])
        s = load_samples(ROOT / "data/alfworld9b/samples.jsonl")[0]
        c, r = s.claims[0], s.records[-1]
        txt = P.record_state(s.task, s.proposed_action, c, r).render()
        self.assertNotIn("Condition:", txt)
        self.assertTrue(txt.endswith("Answer with a single letter."))
        from aeda.verifiers import judge_record
        with self.assertRaises(RuntimeError):
            judge_record(Meter(TableBackend({})), s, c, r, style="bogus")
        with tempfile.TemporaryDirectory() as d:
            base = [PY, str(ROOT / "scripts/run_offline.py"), "--samples", str(ROOT / "data/smoke/samples.jsonl"),
                    "--backend", "api", "--adapter", "tests.fake_jev:good", "--methods", "D1", "--out", d,
                    "--record-style", "state"]
            subprocess.run(base, check=True, capture_output=True, cwd=ROOT)
            self.assertEqual(json.loads(Path(d, "run_meta.json").read_text())["config"]["record_style"], "state")


class TestHolisticParity(unittest.TestCase):
    def test_h1_gets_same_examples_and_style(self):
        from aeda.verifiers import load_fewshot
        s = load_samples(ROOT / "data/alfworld9b/samples.jsonl")[0]
        c = s.claims[0]
        ex = list(load_fewshot(str(ROOT / "data/fewshot/alfworld_record_fewshot.json")))
        st = P.holistic_judgment(s.task, s.proposed_action, c, s.records, ex, "state").render()
        ef = P.holistic_judgment(s.task, s.proposed_action, c, s.records, ex, "effect").render()
        self.assertIn("Right now (after the last record)", st)
        self.assertIn("Example 8\nHistory (oldest first):", st)
        self.assertIn("Example 8\nCondition:", ef)
        self.assertEqual(P.holistic_judgment(s.task, s.proposed_action, c, s.records).render().count("Example"), 0)

    def test_default_rule_shared_by_h1(self):
        from aeda.backends import AdapterBackend
        from aeda.verifiers import m_H1
        s = next(x for x in load_samples(ROOT / "data/alfworld9b/samples.jsonl")
                 if any(c.kind == "default" for c in x.claims))
        c = next(c for c in s.claims if c.kind == "default")
        tab = TableBackend({"holistic": {f"{c.cid}|*": {"A": .1, "B": .1, "C": .8}}})
        self.assertEqual(m_H1(s, c, Meter(tab), Config(), {})[0], "SUPPORTED_DEFAULT")


class TestOnlineDecide(unittest.TestCase):
    def test_block_revise_and_budget(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from run_online import Check, decide
        bad = Check("CONTRADICTED", [{"claim": "The agent is currently at sinkbasin 1", "verdict": "CONTRADICTED",
                                      "evidence_records": ["r7"]}])
        ok = Check("SUPPORTED", [])
        seen = []

        def revise(a, fb):
            seen.append(fb)
            return "go to sinkbasin 1"
        checks = {"clean x 1 with sinkbasin 1": bad, "go to sinkbasin 1": Check("NONE")}
        act, rec = decide({}, "clean x 1 with sinkbasin 1", checks.get, revise, 1)
        self.assertEqual(act, "go to sinkbasin 1")
        self.assertTrue(rec["blocked"] and not rec["executed_despite_contradiction"])
        self.assertEqual(seen[0]["conditions"][0]["source_id"], "r7")
        # agent keeps its action -> executed despite contradiction, counted
        act, rec = decide({}, "clean x 1 with sinkbasin 1", checks.get, lambda a, fb: a, 1)
        self.assertEqual(act, "clean x 1 with sinkbasin 1")
        self.assertTrue(rec["executed_despite_contradiction"])
        # supported and no-precondition actions pass straight through
        self.assertEqual(decide({}, "take a 1 from b 1", lambda a: ok, revise, 1)[0], "take a 1 from b 1")
        self.assertIsNone(decide({}, "go to b 1", lambda a: Check("NONE"), revise, 1)[1])


class TestControlArms(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "scripts"))

    def _view(self, steps):
        hist = [{"id": "r0", "action": "reset", "observation": "You are in the middle of a room."}]
        hist += [{"id": f"r{i}", "action": a, "observation": o} for i, (a, o) in enumerate(steps, 1)]
        return {"task": "put a clean tomato in fridge.", "observation": hist[-1]["observation"], "history": hist}

    def test_tracker_check(self):
        from run_online import tracker_check
        v = self._view([("go to countertop 1", "You arrive at countertop 1. On the countertop 1, you see a tomato 2."),
                        ("take tomato 2 from countertop 1", "You pick up the tomato 2 from the countertop 1."),
                        ("go to sinkbasin 1", "You arrive at sinkbasin 1."),
                        ("go to fridge 1", "Nothing happens.")])
        self.assertEqual(tracker_check(v, "go to fridge 1").status, "NONE")
        ok = tracker_check(v, "clean tomato 2 with sinkbasin 1")
        self.assertEqual(ok.status, "SUPPORTED")
        self.assertEqual({c["evidence_records"][0] for c in ok.claims}, {"r3", "r2"})
        bad = tracker_check(v, "move tomato 2 to countertop 1")
        self.assertEqual(bad.status, "CONTRADICTED")
        at = next(c for c in bad.claims if "at countertop 1" in c["claim"])
        self.assertEqual((at["verdict"], at["evidence_records"]), ("CONTRADICTED", ["r3"]))  # failed r4 ignored
        self.assertEqual(tracker_check(v, "take apple 1 from countertop 1").status, "CONTRADICTED")
        self.assertEqual(tracker_check(self._view([]), "take apple 1 from countertop 1").claims[1]["evidence_records"], ["r0"])

    def test_hint_only_in_agent_view(self):
        from run_online import HINT, hinted
        v = self._view([("go to fridge 1", "You arrive at fridge 1."), ("open cabinet 3", "Nothing happens.")])
        h = hinted(v)
        self.assertTrue(h["history"][2]["observation"].endswith(HINT) and h["observation"].endswith(HINT))
        self.assertNotIn(HINT, h["history"][1]["observation"])
        self.assertNotIn(HINT, h["history"][0]["observation"])
        self.assertEqual(v["history"][2]["observation"], "Nothing happens.")  # env view untouched
        self.assertNotIn(HINT, hinted(self._view([("go to fridge 1", "You arrive at fridge 1.")]))["observation"])


class TestModelWritten(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import types
        self.asked = []
        mod = types.ModuleType("fake_mw_adapter")

        def choose(context, question, options):
            self.asked.append(context + "\n" + question)
            return "B" if "is this true" in question and "sinkbasin" in question else "C"
        mod.choose = choose
        sys.modules["fake_mw_adapter"] = mod

    def test_parse_claim(self):
        from aeda import alfworld as A
        self.assertEqual(A.parse_claim("The agent is at the sinkbasin 1."), {"type": "at", "loc": "sinkbasin 1"})
        self.assertEqual(A.parse_claim("Agent has ladle 1 in hand"), {"type": "holding", "obj": "ladle 1"})
        self.assertEqual(A.parse_claim("The agent's hand is empty"), {"type": "hand_empty"})
        self.assertIsNone(A.parse_claim("The microwave 1 is open"))

    def test_model_check_free_text(self):
        from run_online import model_check
        from aeda.backends import AdapterBackend
        from aeda.verifiers import Config
        hist = [{"id": "r0", "action": "reset", "observation": "You are in the middle of a room."},
                {"id": "r1", "action": "go to drawer 1", "observation": "You arrive at drawer 1."}]
        view = {"task": "clean a ladle", "observation": hist[-1]["observation"], "history": hist}
        conds = [{"claim": "The agent is at sinkbasin 1", "anchors": ["sinkbasin 1"]},
                 {"claim": "The ladle 1 has been seen", "anchors": ["ladle 1"]}]
        cfg = Config(fewshot=str(ROOT / "data/fewshot/alfworld_record_fewshot.json"), record_style="state")
        chk = model_check(view, "clean ladle 1 with sinkbasin 1", conds, "ep", AdapterBackend("fake_mw_adapter:choose"), cfg)
        self.assertEqual(chk.status, "CONTRADICTED")
        at, seen = chk.claims
        self.assertEqual((at["verdict"], at["evidence_records"], at["tracker"]), ("CONTRADICTED", ["r1"], "CONTRADICTED"))
        self.assertEqual((seen["verdict"], seen["eval_spec"], seen["tracker"]), ("UNKNOWN", None, None))
        # the judge sees only the text, and the worked examples in the same yes/no form
        self.assertTrue(all("where is the agent" not in q and "what is the agent holding" not in q for q in self.asked))
        self.assertIn("is this true: The agent is currently at fridge 1?", self.asked[0])
        self.assertEqual(model_check(view, "take a 1 from b 1", [], "ep", None, cfg).status, "EMPTY")


class TestConditionWriters(unittest.TestCase):
    def test_parse_and_prompt(self):
        from aeda import conditions as W
        rows = W.parse({"conditions": ["The agent is at sinkbasin 1.", "the agent is at sinkbasin 1.", " ",
                                       "The agent is holding towel 1.", "The towel 1 is dirty."]}, 2)
        self.assertEqual([r["claim"] for r in rows], ["The agent is at sinkbasin 1.", "The agent is holding towel 1."])
        self.assertEqual(rows[1]["anchors"], ["towel 1"])
        with self.assertRaises(ValueError):
            W.parse({"risks": []}, 3)
        v2, demo = W.instruction("v2", 3), W.instruction("v2demo", 3, "Action: go to fridge 1")
        self.assertIn("at most 3 conditions", v2)
        self.assertNotIn("<example>", v2)
        self.assertTrue(demo.startswith(v2) and demo.endswith("<example>\nAction: go to fridge 1\n</example>"))
        with self.assertRaises(ValueError):
            W.instruction("v2demo", 3)

    def test_write_uses_actor_client(self):
        from aeda import conditions as W

        class Fake:
            def _respond(self, state, prompt, max_tokens):
                self.seen = (state, prompt, max_tokens)
                return {"conditions": ["The agent is at fridge 1."]}

            def risks(self, cp, k):
                return [{"risk": "r", "claim": "x", "anchors": ["fridge 1"]}]
        f = Fake()
        out = W.write(f, {"task": "t", "action": "cool pan 1 with fridge 1"}, "v2", 3, lambda cp: {**cp, "pub": 1})
        self.assertEqual(out, [{"claim": "The agent is at fridge 1.", "anchors": ["fridge 1"]}])
        self.assertEqual(f.seen[0]["pub"], 1)
        self.assertEqual(W.write(f, {}, "risks", 3)[0]["claim"], "x")

    def test_score(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from eval_conditions import score
        h = [{"id": "r0", "action": "reset", "observation": "room"},
             {"id": "r1", "action": "go to drawer 1", "observation": "You arrive at drawer 1."}]
        cp = {"action": "clean towel 1 with sinkbasin 1", "history": h, "succeeded": False}
        s = score(cp, [{"claim": "The agent must be at sinkbasin 1."}, {"claim": "The towel 1 must be clean."}])
        self.assertEqual((s["need"], s["covered"], s["free"]), (2, 1, 1))
        self.assertTrue(s["catchable_failure"] and s["explained"] and s["effect"])
        ok = score({**cp, "succeeded": True, "action": "open drawer 1"}, [{"claim": "The agent is at drawer 1."}])
        self.assertFalse(ok["false_alarm"] or ok["effect"])
        self.assertEqual(ok["covered"], 1)


class TestContextJudges(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        hist = [{"id": "r0", "action": "reset", "observation": "You are in the middle of a room."},
                {"id": "r1", "action": "go to countertop 1", "observation": "You arrive at countertop 1."},
                {"id": "r2", "action": "take tomato 2 from countertop 1", "observation": "You pick up the tomato 2."},
                {"id": "r3", "action": "go to fridge 1", "observation": "You arrive at fridge 1."}]
        self.view = {"task": "put a cool tomato in countertop.", "observation": hist[-1]["observation"], "history": hist}

    def test_llm_check(self):
        from run_online import llm_check
        seen = []

        def ask(state):
            seen.append(state)
            return {"conditions": [{"condition": c, "reasoning": "...", "verdict": v, "record": r}
                                   for c, v, r in zip(state["conditions"], ["true", "false"], ["r2", "r3"])]}
        chk = llm_check(self.view, "move tomato 2 to countertop 1", ask)
        self.assertEqual(chk.status, "CONTRADICTED")
        self.assertEqual([c["verdict"] for c in chk.claims], ["SUPPORTED", "CONTRADICTED"])
        self.assertEqual(chk.claims[1]["evidence_records"], ["r3"])
        self.assertEqual(len(seen[0]["history"]), 4)  # the whole visible history, nothing else
        self.assertEqual(set(seen[0]), {"task", "proposed_action", "history", "conditions"})
        # unusable answer -> UNKNOWN, executed, error kept
        bad = llm_check(self.view, "move tomato 2 to countertop 1", lambda st: {"conditions": []})
        self.assertEqual(bad.status, "UNKNOWN")
        self.assertIn("expected 2", bad.error)
        # unknown on "holding nothing" keeps the default rule
        emp = llm_check(self.view, "take apple 1 from countertop 1",
                        lambda st: {"conditions": [{"verdict": "true", "record": "r1"}, {"verdict": "unknown", "record": None}]})
        self.assertEqual(emp.claims[1]["verdict"], "SUPPORTED_DEFAULT")
        self.assertEqual(llm_check(self.view, "go to sinkbasin 1", ask).status, "NONE")

    def test_h1_check(self):
        import types
        from run_online import check_action
        from aeda.backends import AdapterBackend
        from aeda.verifiers import Config
        asked = []
        mod = types.ModuleType("fake_h1_adapter")

        def choose(context, question, options):
            asked.append(context)
            return "B" if "where is the agent" in question else "A"
        mod.choose = choose
        sys.modules["fake_h1_adapter"] = mod
        cfg = Config(fewshot=str(ROOT / "data/fewshot/alfworld_record_fewshot.json"), record_style="state")
        chk = check_action(self.view, "move tomato 2 to countertop 1", "ep", AdapterBackend("fake_h1_adapter:choose"), cfg, method="H1")
        self.assertEqual(chk.status, "CONTRADICTED")
        self.assertEqual(len(asked), 2)  # one question per condition
        self.assertTrue(all("History (oldest first)" in c and "go to fridge 1" in c and "go to countertop 1" in c for c in asked))


class TestLoopCheck(unittest.TestCase):
    """Arm loop: block a command already run when nothing new has been observed since."""

    def setUp(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from run_online import loop_check
        self.check = loop_check

    def view(self, steps):
        hist = [{"id": "r0", "action": "reset", "observation": "You are in the middle of a room."}]
        hist += [{"id": f"r{i}", "action": a, "observation": o} for i, (a, o) in enumerate(steps, 1)]
        return {"task": "t", "observation": hist[-1]["observation"], "history": hist}

    def test_first_time_and_progress_pass(self):
        v = self.view([("go to drawer 1", "You arrive at drawer 1. It is open."),
                       ("go to sinkbasin 1", "You arrive at sinkbasin 1."),
                       ("clean knife 1 with sinkbasin 1", "You clean the knife 1.")])
        self.assertEqual(self.check(v, "go to countertop 1").status, "NONE")   # never run
        self.assertEqual(self.check(v, "go to drawer 1").status, "NONE")       # new observations since r1

    def test_repeated_look_blocked_from_third(self):
        one = [("go to cabinet 1", "You arrive at cabinet 1."), ("look", "You are facing the cabinet 1.")]
        self.assertEqual(self.check(self.view(one), "look").status, "NONE")     # situation changed since r2
        v = self.view(one + [("look", "You are facing the cabinet 1.")])
        c = self.check(v, "LOOK ")                                               # normalised
        self.assertEqual(c.status, "CONTRADICTED")
        self.assertEqual(c.claims[0]["evidence_records"], ["r3"])
        self.assertIn("just ran", c.claims[0]["claim"])

    def test_nothing_happens_repeat_blocked(self):
        v = self.view([("go to cabinet 1", "You arrive at cabinet 1."), ("close cabinet 1", "Nothing happens."),
                       ("go to cabinet 1", "Nothing happens.")])
        c = self.check(v, "go to cabinet 1")
        self.assertEqual(c.status, "CONTRADICTED")
        self.assertEqual(c.claims[0]["times_run"], 2)
        self.assertEqual(self.check(v, "close cabinet 1").status, "CONTRADICTED")

    def test_same_observation_but_moved_passes(self):
        # the put failed away from the drawer; the agent walked back (repeated arrival text): not blocked
        v = self.view([("go to drawer 1", "You arrive at drawer 1."), ("take knife 1 from drawer 1", "You pick up the knife 1."),
                       ("go to sinkbasin 1", "You arrive at sinkbasin 1."), ("move knife 1 to drawer 1", "Nothing happens."),
                       ("go to drawer 1", "You arrive at drawer 1.")])
        self.assertEqual(self.check(v, "move knife 1 to drawer 1").status, "NONE")

    def test_oscillation_blocked(self):
        v = self.view([("go to fridge 1", "You arrive at fridge 1."), ("go to countertop 1", "You arrive at countertop 1."),
                       ("go to fridge 1", "You arrive at fridge 1."), ("go to countertop 1", "You arrive at countertop 1.")])
        c = self.check(v, "go to fridge 1")
        self.assertEqual(c.status, "CONTRADICTED")
        self.assertEqual(c.claims[0]["evidence_records"], ["r3"])
        self.assertIn("since r3", c.claims[0]["claim"])

    def test_feedback_shape(self):
        from run_online import feedback
        v = self.view([("look", "You are facing nothing."), ("look", "You are facing nothing.")])
        fb = feedback(self.check(v, "look"))
        self.assertEqual(fb["conditions"][0]["source_id"], "r2")
        self.assertEqual(fb["conditions"][0]["status"], "CONTRADICTED")


class TestMultiRevision(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from run_online import decide, loop_check
        self.decide, self.loop = decide, loop_check
        steps = [("go to cabinet 1", "You arrive at cabinet 1."), ("look", "You face cabinet 1."), ("look", "You face cabinet 1."),
                 ("go to cabinet 1", "Nothing happens.")]
        hist = [{"id": "r0", "action": "reset", "observation": "You are in the middle of a room."}]
        hist += [{"id": f"r{i}", "action": a, "observation": o} for i, (a, o) in enumerate(steps, 1)]
        self.view = {"task": "t", "observation": hist[-1]["observation"], "history": hist}

    def test_rejected_list_and_escape(self):
        answers, fbs = iter(["go to cabinet 1", "go to drawer 1"]), []

        def revise(action, fb):
            fbs.append(fb)
            return next(answers)
        act, rec = self.decide(self.view, "look", lambda a: self.loop(self.view, a), revise, 3)
        self.assertEqual(act, "go to drawer 1")
        self.assertFalse(rec["executed_despite_contradiction"])
        self.assertNotIn("rejected_at_this_step", fbs[0])                 # first revision: same feedback as r1 runs
        self.assertEqual(fbs[1]["rejected_at_this_step"], ["look", "go to cabinet 1"])

    def test_one_revision_unchanged(self):
        act, rec = self.decide(self.view, "look", lambda a: self.loop(self.view, a), lambda a, fb: "go to cabinet 1", 1)
        self.assertEqual(act, "go to cabinet 1")
        self.assertTrue(rec["executed_despite_contradiction"])


class TestExplore(unittest.TestCase):
    def test_unvisited_note(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from run_online import explored, places
        hist = [{"id": "r0", "action": "reset", "observation": "You are in the middle of a room. Looking quickly around you, "
                 "you see a cabinet 2, a cabinet 1, a fridge 1, and a sinkbasin 1.\n\nYour task is to: put a cool apple 1 in sinkbasin."},
                {"id": "r1", "action": "go to fridge 1", "observation": "You arrive at fridge 1. The fridge 1 is closed."},
                {"id": "r2", "action": "go to cabinet 9", "observation": "Nothing happens."}]
        view = {"task": "t", "observation": hist[-1]["observation"], "history": hist}
        self.assertEqual(places(hist), (["cabinet 2", "cabinet 1", "fridge 1", "sinkbasin 1"], ["fridge 1"]))
        seen = explored(view)
        self.assertIn("Not visited yet (3 of 4 places", seen["observation"])
        self.assertIn("cabinet 2, cabinet 1, sinkbasin 1.", seen["observation"])
        self.assertEqual(seen["history"][-1]["observation"], seen["observation"])
        self.assertEqual(seen["history"][1], hist[1])                       # earlier records unchanged
        self.assertEqual(view["history"][-1]["observation"], "Nothing happens.")   # env history unchanged


class TestSelfExplore(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        hist = [{"id": "r0", "action": "reset", "observation": "You are in the middle of a room. Looking quickly around you, "
                 "you see a cabinet 1, a fridge 1, and a sinkbasin 1.\n\nYour task is to: put a cool apple in sinkbasin."},
                {"id": "r1", "action": "go to fridge 1", "observation": "You arrive at fridge 1. The fridge 1 is closed."}]
        self.view = {"task": "t", "observation": hist[-1]["observation"], "history": hist}

    def test_model_list_note_and_log(self):
        from run_online import explored, place_list_score, self_explored
        log, seen = [], []

        def ask(state):
            seen.append(state)
            return {"visited": ["Fridge 1"], "not_visited": ["cabinet 1", "sinkbasin 1"]}
        out = self_explored(self.view, ask, log)
        self.assertEqual(out["observation"], explored(self.view)["observation"])   # same note text as explore
        self.assertEqual(set(seen[0]), {"history"})
        self.assertEqual(place_list_score(log)["place_list_exact"], 1)

    def test_wrong_and_unusable(self):
        from run_online import place_list_score, self_explored
        log = []
        self_explored(self.view, lambda st: {"visited": [], "not_visited": ["cabinet 1", "fridge 1", "toaster 1"]}, log)
        out = self_explored(self.view, lambda st: {"places": []}, log)
        self.assertEqual(out, self.view)                                             # no note when unusable
        sc = place_list_score(log)
        self.assertEqual((sc["place_list_steps"], sc["place_list_errors"], sc["place_list_exact"]), (2, 1, 0))
        self.assertEqual((sc["place_list_missing"], sc["place_list_extra"]), (1, 2))  # sinkbasin 1 / fridge 1, toaster 1


class TestOneCall(unittest.TestCase):
    RUNNER = Path.home() / "Documents/Codex/2026-11-21/yo/outputs/alfworld-action-eda-oneshot-altprovider"

    def setUp(self):
        if not self.RUNNER.exists():
            self.skipTest("baseline runner not found")
        sys.path.insert(0, str(ROOT / "scripts"))
        sys.path.insert(0, str(self.RUNNER))
        hist = [{"id": "r0", "action": "reset", "observation": "You are in the middle of a room. Looking quickly around you, "
                 "you see a cabinet 1, a fridge 1, and a sinkbasin 1.\n\nYour task is to: put a cool apple in sinkbasin."},
                {"id": "r1", "action": "go to fridge 1", "observation": "You arrive at fridge 1. The fridge 1 is closed."}]
        self.view = {"task": "t", "observation": hist[-1]["observation"], "history": hist}

    def test_prompt_and_state_match_baseline(self):
        from models import GPUChat
        from pilot import public_checkpoint
        from run_online import onecall_action
        example = {"text": "DEMO TEXT"}
        got = []

        class Fake(GPUChat):
            def _respond(self, state, instruction, max_tokens, **kw):
                got.append((state, instruction))
                return {"action": "open fridge 1"} if len(got) == 1 else \
                    {"visited": ["fridge 1"], "not_visited": ["cabinet 1"], "action": "open fridge 1"}
        a = Fake("http://x", "m", "k")
        a.action_example = example
        cp = public_checkpoint(self.view, "")
        a.action(cp)
        onecall_action(a, cp, example)
        (s0, p0), (s1, p1) = got
        self.assertEqual(s0, s1)                                     # identical input state
        head, tail = p0.split('Return only a JSON object {"action":"..."} without explanation.')
        self.assertTrue(p1.startswith(head) and p1.endswith(tail))   # baseline wording + demo kept
        self.assertIn("not_visited", p1)

    def test_use_variant_differs_by_one_sentence(self):
        from run_online import ONECALL_ACTION, ONECALL_USE_ACTION, onecall_prompt
        self.assertNotEqual(ONECALL_ACTION, ONECALL_USE_ACTION)
        self.assertEqual(ONECALL_USE_ACTION.replace("Then, based on these two lists, propose the command.",
                                                    "Then propose the command."), ONECALL_ACTION)
        ex = {"text": "DEMO"}
        self.assertTrue(onecall_prompt(ex, True).startswith(ONECALL_USE_ACTION) and onecall_prompt(ex, True).endswith(
            onecall_prompt(ex).split(ONECALL_ACTION)[1]))

    def test_read_action_and_score(self):
        from run_online import onecall_read, place_list_score
        log = []
        act = onecall_read(self.view, {"visited": ["fridge 1"], "not_visited": ["cabinet 1", "sinkbasin 1"],
                                       "action": " open fridge 1 "}, log)
        self.assertEqual(act, "open fridge 1")
        act = onecall_read(self.view, {"action": "open fridge 1"}, log)   # lists missing: action still used
        self.assertEqual(act, "open fridge 1")
        self.assertIsNone(onecall_read(self.view, None, log, "IncompleteReply: limit"))   # failed call -> fallback
        self.assertEqual(log[-1]["fallback"], "baseline action call")
        sc = place_list_score(log)
        self.assertEqual((sc["place_list_steps"], sc["place_list_errors"], sc["place_list_exact"]), (3, 2, 1))
