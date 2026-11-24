"""Logic tests with the table backend (no model). Run: python -m unittest -v"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aeda.backends import JevBackend, TableBackend  # noqa: E402
from aeda.evaluate import join, paired_bootstrap, stratified_table  # noqa: E402
from aeda.schema import Sample, load_labels, load_samples  # noqa: E402
from aeda.verifiers import Config, Meter, m_D1, m_D2, m_U1, run  # noqa: E402

SMOKE = ROOT / "data" / "smoke"


def setup():
    samples = {s.sid: s for s in load_samples(SMOKE / "samples.jsonl")}
    backend = TableBackend.from_file(str(SMOKE / "mock_table.json"))
    return samples, backend


def claim(s, cid):
    return next(c for c in s.claims if c.cid == cid)


class TestOrdering(unittest.TestCase):
    def test_reestablishment_d1_vs_u1(self):
        samples, b = setup()
        s = samples["s1"]
        c = claim(s, "c1")
        v_d1, ev, _ = m_D1(s, c, Meter(b), Config(), {})
        v_u1, ev_u, _ = m_U1(s, c, Meter(b), Config(), {})
        self.assertEqual((v_d1, ev), ("SUPPORTED", [5]))
        self.assertEqual((v_u1, ev_u), ("CONTRADICTED", [3]))

    def test_early_stop_saves_calls_without_changing_verdict(self):
        samples, b = setup()
        s = samples["s4"]
        c = claim(s, "c5")
        m1, m2 = Meter(b), Meter(b)
        v1, _, _ = m_D1(s, c, m1, Config(early_stop=True), {})
        v2, _, _ = m_D1(s, c, m2, Config(early_stop=False), {})
        self.assertEqual(v1, v2)
        self.assertLessEqual(m1.calls, m2.calls)

    def test_weak_last_record_with_opposite_previous_is_unknown(self):
        samples, _ = setup()
        s = samples["s1"]
        c = claim(s, "c1")
        tab = {"record": {"c1|1": {"A": .9, "B": .05, "C": .05},
                          "c1|5": {"A": .4, "B": .3, "C": .3}}}
        tab["record"]["c1|3"] = {"A": .05, "B": .9, "C": .05}
        v, _, _ = m_D1(s, c, Meter(TableBackend(tab)), Config(), {})
        self.assertEqual(v, "UNKNOWN")


class TestCompositionAndDefaults(unittest.TestCase):
    def test_pair_repair_catches_composition(self):
        samples, b = setup()
        s = samples["s3"]
        c = claim(s, "c4")
        self.assertEqual(m_D1(s, c, Meter(b), Config(), {})[0], "SUPPORTED")
        v, ev, trace = m_D2(s, c, Meter(b), Config(), {})
        self.assertEqual((v, ev), ("CONTRADICTED", [2, 3]))
        self.assertTrue(trace["pair"]["triggered"])

    def test_single_weak_distractor_does_not_trigger(self):
        samples, b = setup()
        s = samples["s4"]
        v, _, trace = m_D2(s, claim(s, "c5"), Meter(b), Config(), {})
        self.assertEqual(v, "SUPPORTED")
        self.assertFalse(trace["pair"]["triggered"])

    def test_default_claim(self):
        samples, b = setup()
        s = samples["s5"]
        c = claim(s, "c6")
        self.assertEqual(m_D1(s, c, Meter(b), Config(), {})[0], "SUPPORTED_DEFAULT")
        s_inc = Sample(**{**s.__dict__, "window_complete": False})
        self.assertEqual(m_D1(s_inc, c, Meter(b), Config(), {})[0], "UNKNOWN")


class TestPlumbing(unittest.TestCase):
    def test_all_methods_run_and_evaluate(self):
        samples, b = setup()
        rows = run(list(samples.values()), ["H1", "H2", "U1", "D1", "D1f", "D2", "E1", "P0", "Q0"], b, Config())
        self.assertFalse([r for r in rows if "error" in r])
        joined, missing = join(rows, load_labels(SMOKE / "labels.jsonl"), list(samples.values()))
        self.assertEqual(missing, 0)
        self.assertTrue(stratified_table(joined))
        d = paired_bootstrap(joined, "D1", "U1", n_boot=200)
        self.assertGreater(d["diff"], 0)

    def test_missing_backend_stops_run(self):
        samples, _ = setup()
        with self.assertRaises(NotImplementedError):
            run([samples["s1"]], ["D1"], JevBackend(), Config())

    def test_label_field_in_visible_input_is_rejected(self):
        bad = json.loads((SMOKE / "samples.jsonl").read_text(encoding="utf-8").splitlines()[0])
        bad["claims"][0]["gold"] = "SUPPORTED"
        with self.assertRaises(TypeError):
            Sample.from_dict(bad)


if __name__ == "__main__":
    unittest.main()
