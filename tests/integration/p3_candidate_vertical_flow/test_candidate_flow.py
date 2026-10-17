from __future__ import annotations

import json
import unittest
from pathlib import Path

from run_candidate_flow import _load_p2_v2_authority, run_synthetic

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_CANDIDATE_V4_ID = (
    "sha256:d171c71f88123d4a61d6c0e5089049404053e0600c33552b38db7a4113fface9"
)


class CandidateFlowIntegrationTests(unittest.TestCase):
    def test_synthetic_public_interfaces_connect_without_authority(self) -> None:
        result = run_synthetic()

        self.assertEqual(result["classification"], "FIXTURE_INTERFACE_CONNECTIVITY_ONLY")
        self.assertEqual(result["p2"]["status"], "TEST_FIXTURE_NOT_REAL_EVIDENCE")
        self.assertEqual(result["p4"]["status"], "PASS_TEST_FIXTURE_ONLY")
        self.assertEqual(result["p7"]["status"], "NOT_CONNECTED_CONTRACT_GAP")
        self.assertEqual(
            result["p4_to_p7_synthetic_provenance"],
            "NOT_CONNECTED_CONTRACT_GAP",
        )
        self.assertFalse(result["p7"]["roster_created"])
        self.assertFalse(result["p7"]["fabricated_authorization_ids"])
        self.assertEqual(result["p7_to_p8"], "SCHEMA_ONLY")
        self.assertEqual(result["p8"]["status"], "PASS_SCHEMA_FIXTURE_ONLY")
        self.assertFalse(result["p8"]["target_portfolio_created"])
        self.assertEqual(
            result["p8"]["identity"], "RFC8785_SHA256_FIXTURE_ID_VALIDATED"
        )
        self.assertEqual(result["p9"]["status"], "BLOCKED_SYNTHETIC_ONLY")
        self.assertEqual(result["p8_to_p9"], "PERMISSION_DENIAL_ONLY")
        self.assertFalse(result["p9"]["execution_permitted"])
        self.assertEqual(result["broker_write_calls"], 0)
        self.assertEqual(result["orders"], 0)
        self.assertFalse(result["sealed_oos_accessed"])

    def test_real_candidate_eligibility_is_derived_from_p2_authority(self) -> None:
        result = _load_p2_v2_authority(
            REAL_CANDIDATE_V4_ID,
            "INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION",
            "P2_CERTIFICATION_PROTOCOL_V1",
            REPO_ROOT,
        )
        self.assertEqual(
            result["eligibility"], "INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION"
        )
        self.assertFalse(result["candidate_in_frozen_cohort"])
        self.assertEqual(result["cohort_count"], 17)

    def test_candidate_self_report_cannot_override_p2_cohort_authority(self) -> None:
        with self.assertRaisesRegex(ValueError, "conflicts with P2 authority"):
            _load_p2_v2_authority(
                REAL_CANDIDATE_V4_ID,
                "CERTIFIED",
                "P2_CERTIFICATION_PROTOCOL_V2",
                REPO_ROOT,
            )

    def test_frozen_v2_cohort_membership_is_not_inferred_as_v4(self) -> None:
        cohort = json.loads(
            (
                REPO_ROOT
                / "40-certification-system/protocol/p2-formulaic-alpha-v2-candidate-cohort.json"
            ).read_text(encoding="utf-8")
        )
        with self.assertRaisesRegex(ValueError, "must not enter the frozen V2"):
            _load_p2_v2_authority(
                cohort["candidate_ids"][0],
                "INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION",
                "P2_CERTIFICATION_PROTOCOL_V2",
                REPO_ROOT,
            )


if __name__ == "__main__":
    unittest.main()
