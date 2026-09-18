from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
MODULE_PATH = ROOT / "seal_formulaic_protocol_v2.py"
SPEC = importlib.util.spec_from_file_location("seal_formulaic_protocol_v2", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
seal = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = seal
SPEC.loader.exec_module(seal)


PRIVATE_P3 = Path("/mnt/d/AQ_DATA/P3")
PRIVATE_P2 = Path("/mnt/d/AQ_DATA/P2")


class FormulaicProtocolV2Tests(unittest.TestCase):
    def paths(self) -> dict[str, Path]:
        return {
            "protocol_path": ROOT / "p2-certification-protocol-v2.json",
            "cohort_path": ROOT / "p2-formulaic-alpha-v2-candidate-cohort.json",
            "activation_path": ROOT
            / "p2-certification-protocol-v2-activation-pending.json",
            "v1_protocol_path": ROOT / "p2-certification-protocol-v1.json",
            "candidate_contract_path": REPOSITORY
            / "30-research-system/candidate-handoff/p3-to-p2/candidate-contract-v3.md",
            "candidate_schema_path": REPOSITORY
            / "30-research-system/candidate-handoff/p3-to-p2/candidate-contract-v3.schema.json",
            "materialization_manifest_path": PRIVATE_P3
            / "candidate-v3-materialization-001/materialization_manifest.json",
            "validation_report_path": PRIVATE_P3
            / "candidate-v3-materialization-001/validation_report.json",
            "formulaic_dvc_identity_path": PRIVATE_P3
            / "formulaic-alpha-dvc-reproducibility-seal-001/dvc_stage_identity.json",
            "formulaic_seal_path": REPOSITORY
            / "30-research-system/alpha-mining/alphagen-us-pit/.private/formulaic-alpha-reproducibility-seal.json",
            "provider_report_path": PRIVATE_P2
            / "qlib-native-ragged-panel-001/reports/build-report.json",
            "authority_facts_path": REPOSITORY
            / "10-data-system/market-data/provider-binding-authority/accepted_provider_binding_facts.json",
            "control_model_config_path": REPOSITORY
            / "30-research-system/qlib/model-comparison/workflow_config_linear_Alpha158_US.yaml",
            "strategy_config_path": REPOSITORY
            / "30-research-system/qlib/strategy-comparison/strategy_candidates_Alpha158_US.yaml",
        }

    def test_real_identity_only_authorities_build_seal(self) -> None:
        result = seal.validate_and_build_seal(**self.paths())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["candidate_count"], 17)
        self.assertEqual(result["candidate_id_unique_count"], 17)
        self.assertEqual(
            result["sealed_oos_start_session"],
            "UNRESOLVED_PENDING_MAIN_ACTIVATION",
        )

    def test_protocol_v1_and_activation_are_not_v2_outputs(self) -> None:
        protocol = json.loads((ROOT / "p2-certification-protocol-v2.json").read_bytes())
        self.assertFalse(protocol["based_on_protocol"]["v1_activation_modified"])
        self.assertFalse(protocol["based_on_protocol"]["v1_candidate_inventory_changed"])
        self.assertFalse(protocol["based_on_protocol"]["v1_sealed_oos_clock_reset"])
        self.assertFalse(protocol["certification_state"]["protocol_activated"])

    def test_cohort_is_sorted_unique_and_contains_no_performance_fields(self) -> None:
        cohort = json.loads(
            (ROOT / "p2-formulaic-alpha-v2-candidate-cohort.json").read_bytes()
        )
        ids = cohort["candidate_ids"]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), 17)
        self.assertEqual(len(set(ids)), 17)
        self.assertFalse(seal.FORBIDDEN_COHORT_KEYS & seal.collect_keys(cohort))

    def test_tampered_materialization_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "manifest.json"
            source = json.loads(
                self.paths()["materialization_manifest_path"].read_bytes()
            )
            changed = copy.deepcopy(source)
            changed["candidates"] = changed["candidates"][:-1]
            target.write_text(json.dumps(changed), encoding="utf-8")
            paths = self.paths()
            paths["materialization_manifest_path"] = target
            with self.assertRaisesRegex(ValueError, "materialization identity"):
                seal.validate_and_build_seal(**paths)

    def test_activation_is_pending_and_has_no_fake_date(self) -> None:
        activation = json.loads(
            (ROOT / "p2-certification-protocol-v2-activation-pending.json").read_bytes()
        )
        self.assertEqual(activation["activation_status"], "PENDING_ORIGIN_MAIN_MERGE")
        self.assertEqual(activation["freeze_merge_sha"], "UNRESOLVED")
        self.assertEqual(activation["sealed_oos_start_session"], "UNRESOLVED")
        self.assertFalse(activation["pre_activation_sessions_count_toward_certification"])


if __name__ == "__main__":
    unittest.main()
