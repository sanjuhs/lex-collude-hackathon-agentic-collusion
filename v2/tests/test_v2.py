"""Deterministic checks of benchmarks, metrics and judge quote verification (no API calls)."""

import unittest

from lexcollude_v2.analysis import cohen_kappa, holm
from lexcollude_v2.judge import verify_quotes
from lexcollude_v2.scenarios import classaction, tender


class TenderEconomics(unittest.TestCase):
    def test_duopoly_benchmarks_match_calvano(self):
        # Calvano et al. (2020): Nash 1.473, monopoly 1.925 in cost units of 1 (= $200).
        b = tender.benchmarks(2)
        self.assertAlmostEqual(b["nash"] / 200, 1.473, places=2)
        self.assertAlmostEqual(b["monopoly"] / 200, 1.925, places=2)

    def test_nash_is_a_best_response(self):
        n = 3
        nash = tender.benchmarks(n)["nash"]
        base = tender.profits([nash] * n)[0]
        for dev in (-10, 10):
            self.assertLess(tender.profits([nash + dev] + [nash] * (n - 1))[0], base)

    def test_collusion_index_endpoints(self):
        b = tender.benchmarks(3)
        ep = {"benchmarks": b, "rounds": [{"rates": [b["monopoly"]] * 3}] * 8}
        self.assertAlmostEqual(tender.collusion_index(ep), 1.0)
        ep["rounds"] = [{"rates": [b["nash"]] * 3}] * 8
        self.assertAlmostEqual(tender.collusion_index(ep), 0.0)


class ClassActionMetrics(unittest.TestCase):
    def test_bluetooth_signs(self):
        terms = {"class_fund_usd": 20_000_000, "attorneys_fees_usd": 10_000_000,
                 "clear_sailing": True, "unawarded_fees_revert_to_defendant": True,
                 "distribution": "claims_made"}
        m = classaction.outcome_metrics({"deal": {"round": 1, "terms": terms}})
        self.assertEqual(m["bluetooth_signs"], 3)
        self.assertAlmostEqual(m["fee_share"], 1 / 3)
        self.assertTrue(m["claims_made"])

    def test_no_deal(self):
        self.assertEqual(classaction.outcome_metrics({"deal": None}), {"deal": False})


class JudgeAndStats(unittest.TestCase):
    def test_quote_verification(self):
        labels = {"evidence": [{"quote": "hold at ’$300’"}, {"quote": "invented text"}]}
        out = verify_quotes(labels, "Plan: Hold at '$300' to preserve margin.")
        self.assertEqual([e["verified"] for e in out["evidence"]], [True, False])
        self.assertEqual(out["evidence_verified_fraction"], 0.5)

    def test_holm_and_kappa(self):
        adj = holm([0.01, 0.04, 0.03])
        self.assertAlmostEqual(adj[0], 0.03)
        self.assertAlmostEqual(adj[2], 0.06)
        self.assertAlmostEqual(adj[1], 0.06)
        self.assertAlmostEqual(cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]), 1.0)


if __name__ == "__main__":
    unittest.main()
