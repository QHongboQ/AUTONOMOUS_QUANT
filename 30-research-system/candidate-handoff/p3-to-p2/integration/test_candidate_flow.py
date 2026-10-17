from __future__ import annotations

import unittest

from run_candidate_flow import run_synthetic


class CandidateFlowIntegrationTests(unittest.TestCase):
    def test_synthetic_public_interfaces_connect_without_authority(self) -> None:
        result = run_synthetic()

        self.assertEqual(result["classification"], "FIXTURE_INTERFACE_CONNECTIVITY_ONLY")
        self.assertEqual(result["p2"]["status"], "TEST_FIXTURE_NOT_REAL_EVIDENCE")
        self.assertEqual(result["p4"]["status"], "PASS_TEST_FIXTURE_ONLY")
        self.assertEqual(result["p7"]["status"], "PASS_TEST_FIXTURE_ONLY")
        self.assertEqual(result["p7"]["roster_member_count"], 2)
        self.assertEqual(
            result["p7"]["effective_session_selection"],
            "PASS",
        )
        self.assertEqual(result["p8"]["status"], "PASS_SCHEMA_FIXTURE_ONLY")
        self.assertFalse(result["p8"]["target_portfolio_created"])
        self.assertEqual(result["p9"]["status"], "BLOCKED_SYNTHETIC_ONLY")
        self.assertFalse(result["p9"]["execution_permitted"])
        self.assertEqual(result["broker_write_calls"], 0)
        self.assertEqual(result["orders"], 0)
        self.assertFalse(result["sealed_oos_accessed"])


if __name__ == "__main__":
    unittest.main()
