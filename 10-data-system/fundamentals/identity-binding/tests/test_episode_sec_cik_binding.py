from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import ValidationError

CONTRACT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONTRACT_ROOT))

from aq_episode_sec_cik_binding import (
    EpisodeSecCikBindingV1,
    EpisodeSecCikExclusionV1,
    binding_id_for,
    classify_episode_coverage,
    exclusion_decision_id_for,
    validate_binding_record,
    validate_binding_set,
    validate_exclusion_record,
    validate_exclusion_set,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "poc-bindings-v1.json").read_text(
        encoding="utf-8"
    )
)


class EpisodeSecCikBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = FIXTURE["authoritative_episodes"]
        cls.bindings = FIXTURE["bindings"]
        cls.by_episode = {item["episode_id"]: item for item in cls.authority}
        cls.schema = json.loads(
            (CONTRACT_ROOT / "episode-sec-cik-binding-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator.check_schema(cls.schema)

    def validate(self, payload: dict[str, object]) -> EpisodeSecCikBindingV1:
        return validate_binding_record(payload, authoritative_episodes=self.authority)

    def record_with(self, base: dict[str, object], **changes: object) -> dict[str, object]:
        payload = copy.deepcopy(base)
        payload.update(changes)
        projection = {key: value for key, value in payload.items() if key != "binding_id"}
        payload["binding_id"] = binding_id_for(projection)
        return payload

    def test_exact_public_contract_and_schema(self) -> None:
        expected = {
            "episode_id",
            "cik",
            "valid_from",
            "valid_to",
            "binding_classification",
            "evidence_source_identities",
            "binding_id",
        }
        self.assertEqual(expected, set(self.schema["required"]))
        self.assertEqual(expected, set(self.schema["properties"]))
        self.assertFalse(self.schema["additionalProperties"])

    def test_six_poc_bindings_validate_with_exact_ids(self) -> None:
        for payload in self.bindings:
            with self.subTest(episode_id=payload["episode_id"]):
                Draft202012Validator(self.schema).validate(payload)
                binding = self.validate(payload)
                self.assertEqual(payload["binding_id"], binding.binding_id)
                self.assertEqual(
                    payload["binding_id"],
                    binding_id_for({k: v for k, v in payload.items() if k != "binding_id"}),
                )

    def test_admit_reproduces_poc_identity(self) -> None:
        payload = self.bindings[0]
        projection = {key: value for key, value in payload.items() if key != "binding_id"}
        admitted = EpisodeSecCikBindingV1.admit(
            authoritative_episodes=self.authority, **projection
        )
        self.assertEqual(payload["binding_id"], admitted.binding_id)

    def test_raw_construction_without_p1_authority_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValidationError, "full P1"):
            EpisodeSecCikBindingV1.model_validate(self.bindings[0])

    def test_only_admissible_classifications_are_accepted(self) -> None:
        for negative in FIXTURE["non_admitted_cases"]:
            with self.subTest(case=negative["case"]), self.assertRaises(ValidationError):
                self.validate(negative["attempted_record"])

        no_filer = {**self.bindings[0], "binding_classification": "NO_SEC_FILER"}
        with self.assertRaises(ValidationError):
            self.validate(no_filer)

    def test_unknown_and_p2_window_episode_ids_fail_closed(self) -> None:
        ctl = self.bindings[1]
        for episode_id in (
            "P1EP-" + "f" * 64,
            "P1EP-48fadce4058bd19bb88271e6e42ca8edf32f43f5c3be064b09a3766a0b161022",
        ):
            payload = self.record_with(ctl, episode_id=episode_id)
            with self.subTest(episode_id=episode_id), self.assertRaisesRegex(
                ValidationError, "unknown"
            ):
                self.validate(payload)

    def test_invalid_cik_and_empty_or_duplicate_evidence_fail(self) -> None:
        base = self.bindings[0]
        cases = (
            {**base, "cik": "320193"},
            {**base, "evidence_source_identities": []},
            {**base, "evidence_source_identities": ["same", "same"]},
        )
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                self.validate(payload)

    def test_evidence_order_is_preserved_and_participates_in_identity(self) -> None:
        base = self.bindings[0]
        reversed_evidence = list(reversed(base["evidence_source_identities"]))
        changed = self.record_with(base, evidence_source_identities=reversed_evidence)
        binding = self.validate(changed)
        self.assertEqual(tuple(reversed_evidence), binding.evidence_source_identities)
        self.assertNotEqual(base["binding_id"], binding.binding_id)

    def test_episode_id_participates_in_identity(self) -> None:
        base = self.bindings[0]
        projection = {key: value for key, value in base.items() if key != "binding_id"}
        projection["episode_id"] = self.bindings[4]["episode_id"]
        self.assertNotEqual(base["binding_id"], binding_id_for(projection))

    def test_empty_reversed_and_out_of_episode_intervals_fail(self) -> None:
        base = self.bindings[0]
        cases = (
            {**base, "valid_to": base["valid_from"]},
            {**base, "valid_from": "2024-01-01", "valid_to": "2020-01-01"},
            self.record_with(base, valid_from="2009-12-31"),
            self.record_with(base, valid_to="2025-01-02"),
        )
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                self.validate(payload)

    def test_id_reuse_after_field_mutation_fails(self) -> None:
        base = self.bindings[0]
        for key, value in (
            ("cik", "0000018926"),
            ("valid_from", "2010-01-05"),
            ("binding_classification", "PASS_EXACT"),
        ):
            payload = {**base, key: value}
            with self.subTest(field=key), self.assertRaisesRegex(
                ValidationError, "binding_id"
            ):
                self.validate(payload)

    def test_extra_field_fails_closed(self) -> None:
        with self.assertRaises(ValidationError):
            self.validate({**self.bindings[0], "ticker": "AAPL"})

    def test_duplicate_binding_id_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate binding_id"):
            validate_binding_set(
                [self.bindings[0], copy.deepcopy(self.bindings[0])],
                authoritative_episodes=self.authority,
            )

    def test_same_cik_overlap_fails_closed(self) -> None:
        base = self.bindings[2]
        overlap = self.record_with(
            base,
            valid_from="2014-12-31",
            valid_to="2015-01-03",
            evidence_source_identities=["TEST:SAME_CIK_OVERLAP"],
        )
        with self.assertRaisesRegex(ValueError, "REDUNDANT_BINDING_OVERLAP"):
            validate_binding_set(
                [base, overlap], authoritative_episodes=self.authority
            )

    def test_conflicting_cik_overlap_fails_closed(self) -> None:
        base = self.bindings[2]
        overlap = self.record_with(
            base,
            cik="0001130713",
            valid_from="2014-12-31",
            valid_to="2015-01-03",
            evidence_source_identities=["TEST:CONFLICTING_CIK_OVERLAP"],
        )
        with self.assertRaisesRegex(ValueError, "CONFLICTING_CIK_OVERLAP"):
            validate_binding_set(
                [base, overlap], authoritative_episodes=self.authority
            )

    def test_adjacent_nonoverlapping_bindings_are_allowed(self) -> None:
        base = self.bindings[2]
        prefix = self.record_with(
            base,
            valid_from="2010-01-04",
            valid_to="2015-01-02",
            evidence_source_identities=["TEST:EARLIER_BOUNDED_AUTHORITY"],
        )
        validated = validate_binding_set(
            [prefix, base], authoritative_episodes=self.authority
        )
        self.assertEqual(2, len(validated))

    def test_coverage_is_descriptive_only(self) -> None:
        aapl = self.by_episode[self.bindings[0]["episode_id"]]
        bbby = self.by_episode[self.bindings[2]["episode_id"]]
        prefix = self.record_with(
            self.bindings[2],
            valid_from="2010-01-04",
            valid_to="2015-01-02",
            evidence_source_identities=["TEST:EARLIER_BOUNDED_AUTHORITY"],
        )
        self.assertEqual("FULL", classify_episode_coverage(aapl, [self.bindings[0]]))
        self.assertEqual("PARTIAL", classify_episode_coverage(bbby, [self.bindings[2]]))
        self.assertEqual("UNBOUND", classify_episode_coverage(bbby, []))
        self.assertEqual(
            "FULL", classify_episode_coverage(bbby, [prefix, self.bindings[2]])
        )

    def test_model_is_immutable(self) -> None:
        binding = self.validate(self.bindings[0])
        with self.assertRaises(ValidationError):
            binding.cik = "0000018926"


class EpisodeSecCikExclusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = FIXTURE["authoritative_episodes"]
        cls.schema = json.loads(
            (CONTRACT_ROOT / "episode-sec-cik-exclusion-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator.check_schema(cls.schema)

    def admitted(self, marker: int = 0) -> EpisodeSecCikExclusionV1:
        return EpisodeSecCikExclusionV1.admit(
            authoritative_episodes=self.authority,
            episode_id=self.authority[marker]["episode_id"],
            classification="INSUFFICIENT_EVIDENCE",
            reason="Date-valid authority does not cover the complete episode.",
            evidence_source_identities=("AUDIT:sha256:" + "a" * 64,),
        )

    def test_exact_public_contract_and_deterministic_identity(self) -> None:
        expected = {
            "episode_id",
            "classification",
            "reason",
            "evidence_source_identities",
            "decision_id",
        }
        self.assertEqual(expected, set(self.schema["required"]))
        self.assertEqual(expected, set(self.schema["properties"]))
        first = self.admitted()
        second = self.admitted()
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(
            first.decision_id,
            exclusion_decision_id_for(
                first.model_dump(mode="python", exclude={"decision_id"})
            ),
        )
        Draft202012Validator(self.schema).validate(first.model_dump(mode="json"))

    def test_unknown_episode_and_fake_classification_fail_closed(self) -> None:
        admitted = self.admitted().model_dump(mode="json")
        for payload in (
            {**admitted, "episode_id": "P1EP-" + "f" * 64},
            {**admitted, "classification": "PLACEHOLDER_CIK"},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                validate_exclusion_record(payload, authoritative_episodes=self.authority)

    def test_duplicate_episode_exclusions_fail_closed(self) -> None:
        first = self.admitted()
        changed = EpisodeSecCikExclusionV1.admit(
            authoritative_episodes=self.authority,
            episode_id=first.episode_id,
            classification="NO_FREE_UPSTREAM_COVERAGE",
            reason="No free date-valid upstream coverage exists.",
            evidence_source_identities=("AUDIT:sha256:" + "b" * 64,),
        )
        with self.assertRaisesRegex(ValueError, "duplicate exclusion episode_id"):
            validate_exclusion_set(
                [first, changed], authoritative_episodes=self.authority
            )

    def test_exclusion_is_immutable(self) -> None:
        exclusion = self.admitted()
        with self.assertRaises(ValidationError):
            exclusion.reason = "changed"


class AcceptedIdentityAuthorityLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.supplemental = json.loads(
            (
                CONTRACT_ROOT
                / "accepted_supplemental_episode_sec_cik_bindings.json"
            ).read_text(encoding="utf-8")
        )
        cls.exclusions = json.loads(
            (CONTRACT_ROOT / "accepted_episode_sec_cik_exclusions.json").read_text(
                encoding="utf-8"
            )
        )
        cls.exclusion_schema = json.loads(
            (CONTRACT_ROOT / "episode-sec-cik-exclusion-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )

    def test_two_supplemental_bindings_preserve_accepted_evidence(self) -> None:
        records = self.supplemental["records"]
        self.assertEqual(2, self.supplemental["record_count"])
        self.assertEqual(2, len({row["episode_id"] for row in records}))
        fixture_by_id = {row["binding_id"]: row for row in FIXTURE["bindings"]}
        self.assertEqual(records, [fixture_by_id[row["binding_id"]] for row in records])

    def test_111_exclusions_are_deterministic_and_schema_valid(self) -> None:
        records = self.exclusions["records"]
        self.assertEqual(111, self.exclusions["record_count"])
        self.assertEqual(111, len({row["episode_id"] for row in records}))
        self.assertEqual(111, len({row["decision_id"] for row in records}))
        self.assertEqual(
            {
                "INSUFFICIENT_EVIDENCE": 33,
                "NO_FREE_UPSTREAM_COVERAGE": 76,
                "CONFLICT_REMAINS_FAIL_CLOSED": 2,
            },
            self.exclusions["classification_counts"],
        )
        authority = [
            {
                "episode_id": row["episode_id"],
                "valid_from": "2010-01-01",
                "valid_to": "2025-01-01",
            }
            for row in records
        ]
        validated = validate_exclusion_set(records, authoritative_episodes=authority)
        self.assertEqual(111, len(validated))
        for row in records:
            Draft202012Validator(self.exclusion_schema).validate(row)
            self.assertEqual(
                row["decision_id"],
                exclusion_decision_id_for(
                    {key: value for key, value in row.items() if key != "decision_id"}
                ),
            )
            self.assertNotIn("cik", row)

    def test_binding_and_exclusion_episode_sets_are_disjoint(self) -> None:
        binding_ids = {
            row["episode_id"] for row in self.supplemental["records"]
        }
        exclusion_ids = {row["episode_id"] for row in self.exclusions["records"]}
        self.assertFalse(binding_ids & exclusion_ids)


if __name__ == "__main__":
    unittest.main()
