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
