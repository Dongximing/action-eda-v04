"""Tests for data builders, ALFWorld tracker and the context option (no model)."""
import json
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
    def test_context_zero_keeps_p1_prompt_and_k_adds_preceding(self):
        s = load_samples(ROOT / "data/smoke/samples.jsonl")[0]
        c, r = s.claims[0], s.records[2]
        self.assertNotIn("Preceding records", P.record_judgment(s.task, s.proposed_action, c, r))
        self.assertEqual([x.rid for x in preceding(s, r, 2)], [1, 2])
        self.assertEqual(preceding(s, s.records[0], 3), [])
        txt = P.record_judgment(s.task, s.proposed_action, c, r, preceding(s, r, 1))
        self.assertIn("Preceding records", txt)
        self.assertIn("Record to judge: [#3", txt)


if __name__ == "__main__":
    unittest.main()
