import unittest

from aq_pit.reconciliation import (
    EVIDENCE_SPECS,
    FINDING_RESOLUTIONS,
    IDENTITY_SPECS,
    OVERLAY_CASE_SPECS,
    build_evidence_manifests,
    build_identity_events,
)


class ReconciliationImplementationTests(unittest.TestCase):
    def test_accepted_evidence_packages_are_unique(self):
        self.assertEqual(len(EVIDENCE_SPECS), 30)
        self.assertEqual(len({item.evidence_id for item in EVIDENCE_SPECS}), 30)
        self.assertTrue(all(item.url.startswith("https://") for item in EVIDENCE_SPECS))

    def test_identity_event_set_is_exact_and_deterministic(self):
        manifests = build_evidence_manifests()
        first = build_identity_events(manifests)
        second = build_identity_events(manifests)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 20)
        self.assertEqual(len({item.event_id for item in first}), 20)
        self.assertEqual({(item.old_ticker, item.new_ticker) for item in first}, {
            (item.old_ticker, item.new_ticker) for item in IDENTITY_SPECS
        })

    def test_overlay_cases_are_exact_and_not_runtime_branches(self):
        self.assertEqual(tuple(item.case_id for item in OVERLAY_CASE_SPECS), tuple(f"O{n}" for n in range(1, 10)))
        gas = next(item for item in OVERLAY_CASE_SPECS if item.case_id == "O6")
        self.assertEqual(gas.start_session, "2011-12-13")

    def test_all_canonical_findings_have_one_resolution(self):
        self.assertEqual(len(FINDING_RESOLUTIONS), 37)
        self.assertEqual(len({item[0] for item in FINDING_RESOLUTIONS}), 37)
        counts = {}
        for _, resolution, _ in FINDING_RESOLUTIONS:
            counts[resolution] = counts.get(resolution, 0) + 1
        self.assertEqual(counts, {
            "GENUINE_RENAME": 7,
            "SOURCE_BACKFILL": 8,
            "TICKER_REUSE": 5,
            "MEMBERSHIP_EXIT_REENTRY": 7,
            "CORPORATE_SUCCESSION_NOT_MEMBERSHIP_TRANSFER": 1,
            "FALSE_DIAGNOSTIC_BOUNDARY": 9,
        })


if __name__ == "__main__":
    unittest.main()
