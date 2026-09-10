"""Runtime-foundation matrix for the standard-library Trial Ledger."""

from __future__ import annotations

import copy
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from aq_trial_ledger.auth import DeterministicFakeAuthenticator
from aq_trial_ledger.backup import backup, load_anchor_artifact, verify_restored_backup, write_anchor_artifact
from aq_trial_ledger.canonical import CanonicalizationError, canonical_json_bytes, canonicalize_anchor_payload, canonicalize_research_spec, event_hash, hash_research_spec, parse_json_strict
from aq_trial_ledger.contract import Capability, P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1
from aq_trial_ledger.storage import Ledger, LedgerError


def spec(**changes):
    default_family_inputs = {"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"}
    value = {
        "generator": "unit-generator", "generator_version": "1", "hypothesis_id": "h-1",
        "factor_spec_hash": "factor-a", "model_spec_hash": "model-a", "hyperparameter_hash": "hyper-a",
        "dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a",
        "feature_set_hash": "features-a", "train_window": "2020-01-01/2020-12-31",
        "validation_window": "2021-01-01/2021-06-30", "exchange_calendar": "XNYS",
        "calendar_version": "1", "portfolio_rule_hash": "portfolio-a", "cost_assumption_hash": "cost-a",
        "benchmark_policy_hash": "benchmark-a", "git_commit_sha": "abc123",
        "environment_fingerprint": "env-v1", "random_seed": "7",
        "family_policy_inputs_hash": Ledger.family_input_hash(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", default_family_inputs),
        "parameters": {"learning_rate": {"type": "decimal", "value": "0.10"}},
    }
    value.update(changes)
    return value


class CanonicalTests(unittest.TestCase):
    def test_key_order_and_decimal_vectors(self):
        first, first_hash = hash_research_spec(spec())
        second, second_hash = hash_research_spec(dict(reversed(list(spec().items()))))
        self.assertEqual(first, second)
        self.assertEqual(first_hash, second_hash)
        self.assertEqual(
            first,
            b'{"canonicalization_version":"AQ_RESEARCH_SPEC_CANONICAL_V1","research_spec":{"benchmark_policy_hash":"benchmark-a","calendar_version":"1","cost_assumption_hash":"cost-a","dataset_snapshot_id":"dataset-1","environment_fingerprint":"env-v1","exchange_calendar":"XNYS","factor_spec_hash":"factor-a","family_policy_inputs_hash":"746327959046b6c8aa542189832af8928bac24c271f5ca8e90ff13d847961d51","feature_set_hash":"features-a","generator":"unit-generator","generator_version":"1","git_commit_sha":"abc123","hyperparameter_hash":"hyper-a","hypothesis_id":"h-1","label_spec_hash":"label-a","model_spec_hash":"model-a","parameters":{"learning_rate":{"type":"decimal","value":"0.1"}},"portfolio_rule_hash":"portfolio-a","random_seed":"7","train_window":"2020-01-01/2020-12-31","universe_id":"us-large","validation_window":"2021-01-01/2021-06-30"}}',
        )
        self.assertIn(b'"value":"0.1"', first)

    def test_material_parameter_and_metadata_exclusion_rules(self):
        _, original = hash_research_spec(spec())
        _, changed = hash_research_spec(spec(parameters={"learning_rate": {"type": "decimal", "value": "0.11"}}))
        self.assertNotEqual(original, changed)
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(trial_id="not-permitted"))

    def test_unicode_and_escape_vectors(self):
        canonical = canonicalize_research_spec(spec(hypothesis_text="é / \" \\ \n"))
        self.assertIn("é".encode("utf-8"), canonical)
        self.assertIn(b"/", canonical)
        self.assertIn(b"\\u000a", canonical)
        self.assertNotIn(b"\\n", canonical)

    def test_actual_newline_vs_literal_backslash_n_distinct(self):
        # ACTUAL_NEWLINE_VS_LITERAL_BACKSLASH_N_DISTINCT
        actual = canonical_json_bytes({"value": "\n"})
        literal = canonical_json_bytes({"value": "\\n"})
        self.assertEqual(actual, b'{"value":"\\u000a"}')
        self.assertEqual(literal, b'{"value":"\\\\n"}')
        self.assertNotEqual(actual, literal)

    def test_actual_tab_vs_literal_backslash_t_distinct(self):
        # ACTUAL_TAB_VS_LITERAL_BACKSLASH_T_DISTINCT
        actual = canonical_json_bytes({"value": "\t"})
        literal = canonical_json_bytes({"value": "\\t"})
        self.assertEqual(actual, b'{"value":"\\u0009"}')
        self.assertEqual(literal, b'{"value":"\\\\t"}')
        self.assertNotEqual(actual, literal)

    def test_literal_backslash_u_escape_distinct(self):
        # LITERAL_BACKSLASH_U_ESCAPE_DISTINCT
        self.assertNotEqual(
            canonical_json_bytes({"value": "\n"}),
            canonical_json_bytes({"value": "\\u000a"}),
        )

    def test_canonical_string_roundtrip(self):
        # CANONICAL_STRING_ROUNDTRIP
        for value in ("\n", "\\n", "\t", "\\t", "\r", "\\r", "\b", "\\b", "\f", "\\f", "\\u000a", '"', "\\", "/", "é"):
            with self.subTest(value=repr(value)):
                encoded = canonical_json_bytes({"value": value})
                self.assertEqual(parse_json_strict(encoded.decode("utf-8")), {"value": value})

    def test_schema_aware_opaque_string_and_decimal_rejections(self):
        opaque_one = canonicalize_research_spec(spec(hypothesis_id="e\u0301"))
        opaque_two = canonicalize_research_spec(spec(hypothesis_id="é"))
        self.assertNotEqual(opaque_one, opaque_two)
        self.assertEqual(
            canonicalize_research_spec(spec(hypothesis_text="e\u0301")),
            canonicalize_research_spec(spec(hypothesis_text="é")),
        )
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(parameters={"learning_rate": {"type": "decimal", "value": 0.1}}))
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(extensions={"sealed_oos_data": "no"}))

    def test_semantic_normalization_is_schema_path_scoped(self):
        # TOP_LEVEL_SEMANTIC_TEXT_NFC_NORMALIZED
        self.assertEqual(
            canonicalize_research_spec(spec(hypothesis_text="e\u0301")),
            canonicalize_research_spec(spec(hypothesis_text="é")),
        )
        # NESTED_EXTENSION_SAME_NAME_REMAINS_OPAQUE / OPAQUE_EXTENSION_UNICODE_DISTINCT
        self.assertNotEqual(
            canonicalize_research_spec(spec(extensions={"hypothesis_text": "e\u0301"})),
            canonicalize_research_spec(spec(extensions={"hypothesis_text": "é"})),
        )
        self.assertNotEqual(
            canonicalize_research_spec(spec(extensions={"opaque": "e\u0301"})),
            canonicalize_research_spec(spec(extensions={"opaque": "é"})),
        )

    def test_negative_canonical_inputs(self):
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(unknown="no"))
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(extensions={1: "no"}))
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(hypothesis_id="\ud800"))
        with self.assertRaises(CanonicalizationError):
            parse_json_strict('{"x":1,"x":2}')

    def test_finite_float_in_extension_rejected(self):
        # FINITE_FLOAT_IN_EXTENSION_REJECTED
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(extensions={"ratio": 0.1}))

    def test_finite_float_in_nested_research_field_rejected(self):
        # FINITE_FLOAT_IN_NESTED_RESEARCH_FIELD_REJECTED
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(family_inputs={"nested": {"ratio": 0.1}}))

    def test_required_identity_axes_and_typed_parameters(self):
        for field in ("model_spec_hash", "hyperparameter_hash", "train_window", "validation_window",
                      "cost_assumption_hash", "benchmark_policy_hash", "factor_spec_hash"):
            with self.subTest(field=field):
                invalid = spec()
                del invalid[field]
                with self.assertRaises(CanonicalizationError):
                    canonicalize_research_spec(invalid)
        self.assertEqual(
            hash_research_spec(spec())[1],
            hash_research_spec(spec(parameters={"learning_rate": {"type": "decimal", "value": "1e-1"}}))[1],
        )
        opaque = spec(parameters={"source_label": {"type": "string", "value": "001"}})
        self.assertIn(b'"001"', canonicalize_research_spec(opaque))

    def test_frozen_canonical_vectors(self):
        self.assertEqual(hash_research_spec(spec())[1], "a200675434f562226d4caf596cedfb41f31a2d3deaf1b8e57f0d2c6ff91f5948")
        self.assertEqual(hash_research_spec(spec(hypothesis_text="é"))[1], "57342b113c1a1ddbb94063e9d3c85e485e869034145357dfeea67a0d0935af47")
        self.assertEqual(hash_research_spec(spec(hypothesis_text="line\n"))[1], "9f30f55aecd179f746caa50001a0e78ab0b833702f73d503fc5205851afdae91")
        plus_eight = spec(extensions={"instant": datetime(2026, 9, 10, 8, tzinfo=timezone(timedelta(hours=8)))})
        utc = spec(extensions={"instant": datetime(2026, 9, 10, 0, tzinfo=timezone.utc)})
        self.assertEqual(hash_research_spec(plus_eight)[1], "fdc5bc0e439e624ee1b17cae211de109a980bcab0ebc32d534395f651e3ce174")
        self.assertEqual(hash_research_spec(plus_eight)[1], hash_research_spec(utc)[1])


class LedgerCase(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).parent / ".temporary-ledger-tests"
        temporary_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary_root)
        self.path = os.path.join(self.temp.name, "ledger.db")
        self.ledger = Ledger(self.path, authenticator=DeterministicFakeAuthenticator({
            "human:owner": "human:owner", "generator:one": "generator:one",
            "generator:retire": "generator:retire",
        }))
        self.ledger.init()
        self.ledger.register_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {"version": "1"})
        self.ledger.activate_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1")

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def register(self, key="one", **kwargs):
        trial_kind = kwargs.pop("trial_kind", "INDEPENDENT_EVALUATION")
        return self.ledger.register(
            "human:owner", key, spec(**kwargs), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1,
            family_policy_version="1", trial_kind=trial_kind,
            family_inputs={"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"},
        )

    def _drop_update_trigger(self, table):
        self.ledger._db.execute(f"DROP TRIGGER immutable_{table}_update")

    def _assert_tamper_blocks_integrity(self, table, statement, values=()):
        self._drop_update_trigger(table)
        self.ledger._db.execute(statement, values)
        self.assertFalse(self.ledger.verify_global_chain())
        with self.assertRaises(LedgerError):
            self.ledger.snapshot("human:owner")

    def _terminal_evidence(self):
        trial = self.register("evidence")
        execution = self.ledger.start_execution("human:owner", trial)
        self.ledger.complete_execution("human:owner", execution)
        result = self.ledger.attach_result("human:owner", trial, execution, "metric", "local://result")
        artifact = self.ledger.attach_artifact("human:owner", trial, execution, "manifest", "local://artifact")
        violation = self.ledger.record_protocol_violation("human:owner", "evidence violation", "local://violation")
        return trial, execution, result, artifact, violation

    def _use_strict_authenticator(self):
        self.ledger._authenticator = DeterministicFakeAuthenticator({
            "owner-token": "human:owner", "generator-token": "generator:strict",
            "reader-token": "generator:reader",
        })

    def test_authentication_boundary_rejects_untrusted_actor_strings(self):
        # UNAUTHENTICATED_WRITE_REJECTED / UNKNOWN_CREDENTIAL_REJECTED
        # GENERATOR_CANNOT_IMPERSONATE_OWNER / AUTHENTICATED_OWNER_ADMIN_ACCEPTED
        self._use_strict_authenticator()
        with self.assertRaises(LedgerError):
            self.ledger.register(None, "unauthenticated", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs={"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"})
        with self.assertRaises(LedgerError):
            self.ledger.register("unknown-token", "unknown", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs={"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"})
        self.ledger.register_actor("owner-token", "generator:strict")
        self.ledger.set_actor_status("owner-token", "generator:strict", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("owner-token", "generator:strict", Capability.TRIAL_REGISTER)
        with self.assertRaises(LedgerError):
            self.ledger.register("human:owner", "impersonation", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs={"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"})

    def test_authenticated_generator_scoped_write_records_authenticated_actor(self):
        # AUTHENTICATED_GENERATOR_SCOPED_WRITE_ACCEPTED / AUTHENTICATED_ACTOR_ID_RECORDED_IN_EVENT
        self._use_strict_authenticator()
        self.ledger.register_actor("owner-token", "generator:strict")
        self.ledger.set_actor_status("owner-token", "generator:strict", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("owner-token", "generator:strict", Capability.TRIAL_REGISTER)
        inputs = {"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"}
        trial = self.ledger.register("generator-token", "scoped", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs=inputs)
        event = self.ledger._db.execute("SELECT actor_id FROM trial_events WHERE trial_id = ? AND event_type = 'TRIAL_REGISTERED'", (trial,)).fetchone()
        self.assertEqual("generator:strict", event["actor_id"])

    def test_public_runtime_has_no_raw_sqlite_connection(self):
        self.assertFalse(hasattr(self.ledger, "db"))
        self.assertTrue(hasattr(self.ledger, "_db"))  # Explicit private test-only hook.

    def test_snapshot_read_authorization_and_suspension(self):
        # SNAPSHOT_WITHOUT_CAPABILITY_REJECTED / SNAPSHOT_WITH_READ_CAPABILITY_ACCEPTED
        # SUSPENDED_ACTOR_SNAPSHOT_REJECTED
        self._use_strict_authenticator()
        self.ledger.register_actor("owner-token", "generator:reader")
        self.ledger.set_actor_status("owner-token", "generator:reader", "ACTOR_ACTIVATED")
        with self.assertRaises(LedgerError):
            self.ledger.snapshot("reader-token")
        self.ledger.grant_capability("owner-token", "generator:reader", Capability.SNAPSHOT_READ)
        self.assertTrue(self.ledger.snapshot("reader-token"))
        self.ledger.set_actor_status("owner-token", "generator:reader", "ACTOR_SUSPENDED")
        with self.assertRaises(LedgerError):
            self.ledger.snapshot("reader-token")

    def test_trial_kind_allowlist_blocks_replay_as_new_trial(self):
        # REGISTER_REPLAY_AS_NEW_TRIAL_REJECTED / UNKNOWN_TRIAL_KIND_REJECTED
        # VALID_INDEPENDENT_TRIAL_KIND_ACCEPTED / REPLAY_EXECUTION_STILL_ACCEPTED
        with self.assertRaises(LedgerError):
            self.register("replay-kind", trial_kind="REPRODUCIBILITY_REPLAY")
        with self.assertRaises(LedgerError):
            self.register("unknown-kind", trial_kind="INVENTED_KIND")
        self.assertTrue(self.register("independent-kind", trial_kind="INDEPENDENT_EVALUATION"))

    def test_capability_grant_requires_active_target(self):
        # CAPABILITY_GRANT_TO_INACTIVE_ACTOR_REJECTED
        # CAPABILITY_GRANT_TO_SUSPENDED_ACTOR_REJECTED
        # CAPABILITY_GRANT_TO_RETIRED_ACTOR_REJECTED
        # ACTIVE_ACTOR_CAPABILITY_GRANT_ACCEPTED
        self.ledger.register_actor("human:owner", "generator:target")
        with self.assertRaises(LedgerError):
            self.ledger.grant_capability("human:owner", "generator:target", Capability.TRIAL_REGISTER)
        self.ledger.set_actor_status("human:owner", "generator:target", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("human:owner", "generator:target", Capability.TRIAL_REGISTER)
        self.ledger.set_actor_status("human:owner", "generator:target", "ACTOR_SUSPENDED")
        with self.assertRaises(LedgerError):
            self.ledger.grant_capability("human:owner", "generator:target", Capability.RESULT_ATTACH)
        self.ledger.set_actor_status("human:owner", "generator:target", "ACTOR_RETIRED")
        with self.assertRaises(LedgerError):
            self.ledger.grant_capability("human:owner", "generator:target", Capability.ARTIFACT_ATTACH)

    def test_normal_registration_uses_incremental_head_guard(self):
        # NORMAL_REGISTRATION_DOES_NOT_FULL_SCAN_HISTORY
        baseline = self.ledger._full_verify_calls
        for index in range(5):
            self.register(f"incremental-{index}", hypothesis_id=f"incremental-{index}")
        self.assertEqual(baseline, self.ledger._full_verify_calls)
        self.assertTrue(self.ledger.verify_global_chain())

    def test_scale_smoke_1000_sequential_registrations(self):
        baseline = self.ledger._full_verify_calls
        for index in range(1000):
            self.register(f"scale-{index}", hypothesis_id=f"scale-{index}")
        self.assertEqual(baseline, self.ledger._full_verify_calls)
        self.assertTrue(self.ledger.verify_global_chain())
        self.assertEqual(1000, self.ledger._db.execute("SELECT COUNT(*) FROM trial_registrations").fetchone()[0])
        self.assertEqual(1015, self.ledger._db.execute("SELECT COUNT(*) FROM trial_events").fetchone()[0])

    def test_external_writer_head_change_fails_closed(self):
        self.ledger._db.execute(
            "INSERT INTO trial_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("external-event", self.ledger._verified_head_sequence + 1, None, None, "EXTERNAL_WRITE",
             "human:owner", "2099-01-01T00:00:00.000000Z", "{}", self.ledger._verified_head_hash, "0" * 64),
        )
        with self.assertRaisesRegex(LedgerError, "EXTERNAL_OR_CONCURRENT_WRITER_DETECTED"):
            self.register("external-writer")

    def test_open_existing_ledger_performs_full_verification(self):
        self.register("reopen")
        self.ledger.close()
        self.ledger = Ledger(
            self.path, authenticator=DeterministicFakeAuthenticator({"human:owner": "human:owner"})
        )
        self.assertEqual(1, self.ledger._full_verify_calls)

    def test_schema_metadata_tampering_is_detected(self):
        # SCHEMA_VERSION_METADATA_TAMPER_DETECTED / EVENT_HASH_DOMAIN_METADATA_TAMPER_DETECTED
        # RESEARCH_CANONICAL_VERSION_METADATA_TAMPER_DETECTED / ANCHOR_CANONICAL_VERSION_METADATA_TAMPER_DETECTED
        # LEDGER_ID_METADATA_TAMPER_DETECTED
        mutations = (
            ("schema_version", "2"), ("event_hash_domain_version", "wrong-domain"),
            ("research_canonicalization_version", "wrong-research"),
            ("anchor_canonicalization_version", "wrong-anchor"), ("ledger_id", "wrong-ledger"),
        )
        for index, (key, value) in enumerate(mutations):
            if index:
                self.ledger.close()
                self.temp.cleanup()
                self.setUp()
            self.ledger._db.execute("DROP TRIGGER immutable_schema_metadata_update")
            self.ledger._db.execute("UPDATE schema_metadata SET value = ? WHERE key = ?", (value, key))
            self.assertFalse(self.ledger.verify_global_chain(), key)
            with self.assertRaises(LedgerError):
                self.ledger.snapshot("human:owner")

    def test_family_input_hash_match_accepted_and_mismatch_rejected(self):
        # FAMILY_INPUT_HASH_MATCH_ACCEPTED / FAMILY_INPUT_HASH_MISMATCH_REJECTED
        inputs = {"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"}
        matching = spec(family_policy_inputs_hash=Ledger.family_input_hash(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", inputs))
        self.assertTrue(self.ledger.register("human:owner", "matching", matching, family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs=inputs))
        with self.assertRaises(LedgerError):
            self.ledger.register("human:owner", "mismatch", spec(family_policy_inputs_hash="0" * 64), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs=inputs)

    def test_p1_model_variation_does_not_change_family_input_hash(self):
        # P1_MODEL_VARIATION_DOES_NOT_CHANGE_FAMILY_INPUT_HASH
        inputs = {"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1", "model": "ridge", "hyperparameter": "a"}
        changed = {**inputs, "model": "lightgbm", "hyperparameter": "b"}
        self.assertEqual(Ledger.family_input_hash(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", inputs), Ledger.family_input_hash(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", changed))

    def test_p1_required_axis_change_changes_family_input_hash(self):
        # P1_REQUIRED_AXIS_CHANGE_CHANGES_FAMILY_INPUT_HASH
        inputs = {"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"}
        self.assertNotEqual(Ledger.family_input_hash(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", inputs), Ledger.family_input_hash(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {**inputs, "label_spec_hash": "label-b"}))

    def test_policy_rules_hash_is_distinct_from_policy_spec_hash(self):
        # POLICY_RULES_HASH_DISTINCT_FROM_POLICY_SPEC_HASH
        initial = self.ledger._db.execute("SELECT * FROM family_policy_specs WHERE family_policy_id = ?", (P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1,)).fetchone()
        self.assertNotEqual(initial["policy_rules_hash"], initial["canonical_policy_hash"])
        self.ledger.register_family_policy("human:owner", "policy-other", "1", {"version": "1"})
        self.ledger.register_family_policy("human:owner", "policy-other", "2", {"version": "1"})
        self.ledger.register_family_policy("human:owner", "policy-rules-changed", "1", {"version": "2"})
        by_id = self.ledger._db.execute("SELECT * FROM family_policy_specs WHERE family_policy_id = 'policy-other' AND family_policy_version = '1'").fetchone()
        by_version = self.ledger._db.execute("SELECT * FROM family_policy_specs WHERE family_policy_id = 'policy-other' AND family_policy_version = '2'").fetchone()
        by_rules = self.ledger._db.execute("SELECT * FROM family_policy_specs WHERE family_policy_id = 'policy-rules-changed'").fetchone()
        self.assertNotEqual(initial["canonical_policy_hash"], by_id["canonical_policy_hash"])
        self.assertNotEqual(by_id["canonical_policy_hash"], by_version["canonical_policy_hash"])
        self.assertNotEqual(initial["policy_rules_hash"], by_rules["policy_rules_hash"])
        self.assertNotEqual(initial["canonical_policy_hash"], by_rules["canonical_policy_hash"])

    def test_family_policy_spec_mutation_detected(self):
        self._assert_tamper_blocks_integrity("family_policy_specs", "UPDATE family_policy_specs SET canonical_policy_hash = ? WHERE family_policy_id = ?", ("0" * 64, P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1))

    def test_chained_actor_target_mutation_detected(self):
        # CHAINED_ACTOR_TARGET_MUTATION_DETECTED
        self.ledger.register_actor("human:owner", "generator:one")
        self._assert_tamper_blocks_integrity("actor_status_events", "UPDATE actor_status_events SET actor_id = ? WHERE actor_id = ?", ("human:owner", "generator:one"))

    def test_actor_identity_mutation_detected(self):
        self.ledger.register_actor("human:owner", "generator:one")
        self._assert_tamper_blocks_integrity("actor_identities", "UPDATE actor_identities SET actor_type = ? WHERE actor_id = ?", ("TAMPERED", "generator:one"))

    def test_chained_actor_occurred_at_mutation_detected(self):
        # CHAINED_ACTOR_OCCURRED_AT_MUTATION_DETECTED
        self.ledger.register_actor("human:owner", "generator:one")
        self._assert_tamper_blocks_integrity("actor_status_events", "UPDATE actor_status_events SET occurred_at = ? WHERE actor_id = ?", ("2099-01-01T00:00:00.000000Z", "generator:one"))

    def test_chained_capability_target_mutation_detected(self):
        # CHAINED_CAPABILITY_TARGET_MUTATION_DETECTED
        self.ledger.register_actor("human:owner", "generator:one")
        self.ledger.set_actor_status("human:owner", "generator:one", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("human:owner", "generator:one", Capability.TRIAL_REGISTER)
        self._assert_tamper_blocks_integrity("capability_events", "UPDATE capability_events SET actor_id = ? WHERE actor_id = ?", ("human:owner", "generator:one"))

    def test_chained_capability_name_mutation_detected(self):
        # CHAINED_CAPABILITY_NAME_MUTATION_DETECTED
        self.ledger.register_actor("human:owner", "generator:one")
        self.ledger.set_actor_status("human:owner", "generator:one", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("human:owner", "generator:one", Capability.TRIAL_REGISTER)
        self._assert_tamper_blocks_integrity("capability_events", "UPDATE capability_events SET capability = ? WHERE actor_id = ?", ("TAMPERED", "generator:one"))

    def test_chained_capability_policy_version_mutation_detected(self):
        # CHAINED_CAPABILITY_POLICY_VERSION_MUTATION_DETECTED
        self.ledger.register_actor("human:owner", "generator:one")
        self.ledger.set_actor_status("human:owner", "generator:one", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("human:owner", "generator:one", Capability.TRIAL_REGISTER)
        self._assert_tamper_blocks_integrity("capability_events", "UPDATE capability_events SET policy_version = ? WHERE actor_id = ?", ("V2", "generator:one"))

    def test_chained_capability_reason_mutation_detected(self):
        # CHAINED_CAPABILITY_REASON_MUTATION_DETECTED
        self.ledger.register_actor("human:owner", "generator:one")
        self.ledger.set_actor_status("human:owner", "generator:one", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("human:owner", "generator:one", Capability.TRIAL_REGISTER, "granted")
        self._assert_tamper_blocks_integrity("capability_events", "UPDATE capability_events SET reason = ? WHERE actor_id = ?", ("tampered", "generator:one"))

    def test_chained_family_policy_id_mutation_detected(self):
        # CHAINED_FAMILY_POLICY_ID_MUTATION_DETECTED
        self.ledger.register_family_policy("human:owner", "policy-other", "1", {"version": "1"})
        self.ledger.activate_family_policy("human:owner", "policy-other", "1")
        self._assert_tamper_blocks_integrity("family_policy_events", "UPDATE family_policy_events SET family_policy_id = ? WHERE family_policy_id = ? AND event_type = ?", (P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "policy-other", "FAMILY_POLICY_ACTIVATED"))

    def test_chained_family_policy_version_mutation_detected(self):
        # CHAINED_FAMILY_POLICY_VERSION_MUTATION_DETECTED
        self.ledger.register_family_policy("human:owner", "policy-other", "1", {"version": "1"})
        self.ledger.register_family_policy("human:owner", "policy-other", "2", {"version": "1"})
        self.ledger.activate_family_policy("human:owner", "policy-other", "2")
        self._assert_tamper_blocks_integrity("family_policy_events", "UPDATE family_policy_events SET family_policy_version = ? WHERE family_policy_id = ? AND family_policy_version = ? AND event_type = ?", ("1", "policy-other", "2", "FAMILY_POLICY_ACTIVATED"))

    def test_trial_created_sequence_mutation_detected(self):
        # TRIAL_CREATED_SEQUENCE_MUTATION_DETECTED
        trial = self.register()
        self._assert_tamper_blocks_integrity("trial_registrations", "UPDATE trial_registrations SET created_ledger_sequence = ? WHERE trial_id = ?", (1, trial))

    def test_trial_family_mutation_detected(self):
        # TRIAL_FAMILY_MUTATION_DETECTED
        trial = self.register()
        self._assert_tamper_blocks_integrity("trial_registrations", "UPDATE trial_registrations SET trial_family_id = ? WHERE trial_id = ?", ("tampered-family", trial))

    def test_research_spec_blob_mutation_detected(self):
        # RESEARCH_SPEC_BLOB_MUTATION_DETECTED
        trial = self.register()
        row = self.ledger._db.execute("SELECT canonical_research_spec_sha256 FROM trial_registrations WHERE trial_id = ?", (trial,)).fetchone()
        self._assert_tamper_blocks_integrity("research_specs", "UPDATE research_specs SET canonical_blob = ? WHERE canonical_research_spec_sha256 = ?", (b"{}", row["canonical_research_spec_sha256"]))

    def test_idempotency_mapping_mutation_detected(self):
        # IDEMPOTENCY_MAPPING_MUTATION_DETECTED
        self.register("first")
        self._assert_tamper_blocks_integrity("registration_idempotency", "UPDATE registration_idempotency SET idempotency_key = ? WHERE idempotency_key = ?", ("tampered", "first"))

    def test_execution_trial_mutation_detected(self):
        # EXECUTION_TRIAL_MUTATION_DETECTED
        first = self.register("first")
        second = self.register("second", hypothesis_id="second")
        execution = self.ledger.start_execution("human:owner", first)
        self._assert_tamper_blocks_integrity("execution_records", "UPDATE execution_records SET trial_id = ? WHERE execution_id = ?", (second, execution))

    def test_result_created_sequence_mutation_detected(self):
        # RESULT_CREATED_SEQUENCE_MUTATION_DETECTED
        _, _, result, _, _ = self._terminal_evidence()
        self._assert_tamper_blocks_integrity("result_references", "UPDATE result_references SET created_ledger_sequence = ? WHERE reference_id = ?", (1, result))

    def test_result_locator_mutation_detected(self):
        # RESULT_LOCATOR_MUTATION_DETECTED
        _, _, result, _, _ = self._terminal_evidence()
        self._assert_tamper_blocks_integrity("result_references", "UPDATE result_references SET locator = ? WHERE reference_id = ?", ("local://tampered", result))

    def test_artifact_locator_mutation_detected(self):
        # ARTIFACT_LOCATOR_MUTATION_DETECTED
        _, _, _, artifact, _ = self._terminal_evidence()
        self._assert_tamper_blocks_integrity("artifact_references", "UPDATE artifact_references SET locator = ? WHERE reference_id = ?", ("local://tampered", artifact))

    def test_protocol_violation_mutation_detected(self):
        # PROTOCOL_VIOLATION_MUTATION_DETECTED
        _, _, _, _, violation = self._terminal_evidence()
        self._assert_tamper_blocks_integrity("protocol_violations", "UPDATE protocol_violations SET reason = ? WHERE violation_id = ?", ("tampered", violation))

    def test_historical_snapshot_tamper_fails_closed(self):
        # HISTORICAL_SNAPSHOT_TAMPER_FAIL_CLOSED
        trial = self.register("historic-tamper")
        boundary = self.ledger._db.execute("SELECT MAX(ledger_sequence) FROM trial_events").fetchone()[0]
        self.ledger.start_execution("human:owner", trial)
        self._assert_tamper_blocks_integrity("trial_registrations", "UPDATE trial_registrations SET trial_family_id = ? WHERE trial_id = ?", ("tampered-family", trial))
        with self.assertRaises(LedgerError):
            self.ledger.snapshot("human:owner", as_of_ledger_sequence=boundary)

    def test_initialization_is_atomic_and_rejects_second_init(self):
        self.assertTrue(self.ledger.verify_global_chain())
        with self.assertRaises(LedgerError):
            self.ledger.init()

    def test_actor_and_capability_lifecycle_is_append_only(self):
        self.ledger.register_actor("human:owner", "generator:one")
        self.ledger.set_actor_status("human:owner", "generator:one", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("human:owner", "generator:one", Capability.TRIAL_REGISTER)
        inputs = {"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"}
        trial = self.ledger.register("generator:one", "key", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs=inputs)
        self.assertTrue(trial)
        self.ledger.revoke_capability("human:owner", "generator:one", Capability.TRIAL_REGISTER)
        with self.assertRaises(LedgerError):
            self.ledger.register("generator:one", "other", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs=inputs)
        self.ledger.set_actor_status("human:owner", "generator:one", "ACTOR_SUSPENDED")
        self.assertGreater(self.ledger._db.execute("SELECT COUNT(*) FROM capability_events").fetchone()[0], 1)

    def test_family_identity_and_retired_policy(self):
        family_inputs = {"dataset_snapshot_id": "a", "universe_id": "u", "label_spec_hash": "b", "feature_set_hash": "f", "research_objective": "o", "evaluation_window_policy": "w", "model": "ridge", "hyperparameter": "1"}
        self.assertEqual(
            self.ledger.family_id(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", family_inputs),
            self.ledger.family_id(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {**family_inputs, "model": "lightgbm", "hyperparameter": "2"}),
        )
        self.assertNotEqual(
            self.ledger.family_id(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", family_inputs),
            self.ledger.family_id(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {**family_inputs, "dataset_snapshot_id": "changed"}),
        )
        self.ledger.retire_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1")
        with self.assertRaises(LedgerError):
            self.register()

    def test_p1_family_required_axes_fail_closed(self):
        complete = {"dataset_snapshot_id": "a", "universe_id": "u", "label_spec_hash": "b", "feature_set_hash": "f", "research_objective": "o", "evaluation_window_policy": "w"}
        for field in complete:
            with self.subTest(field=field):
                partial = dict(complete)
                del partial[field]
                with self.assertRaises(LedgerError):
                    self.ledger.family_id(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", partial)
        with self.assertRaises(LedgerError):
            self.ledger.family_id(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {})

    def test_registration_idempotency_and_conflicts(self):
        trial = self.register("same")
        self.assertEqual(trial, self.register("same"))
        for changed in ({"hypothesis_id": "changed"}, {"generator": "other"}):
            with self.assertRaises(LedgerError):
                self.register("same", **changed)

    def test_execution_lifecycle_references_and_replay(self):
        trial = self.register()
        execution = self.ledger.start_execution("human:owner", trial)
        with self.assertRaises(LedgerError):
            self.ledger.attach_result("human:owner", trial, execution, "metric", "local://result")
        self.ledger.complete_execution("human:owner", execution)
        self.assertTrue(self.ledger.attach_result("human:owner", trial, execution, "metric", "local://result"))
        self.assertTrue(self.ledger.attach_artifact("human:owner", trial, execution, "manifest", "local://artifact"))
        with self.assertRaises(LedgerError):
            self.ledger.fail_execution("human:owner", execution, "late")
        _, spec_hash = hash_research_spec(spec())
        replay = {"research_spec_sha256": spec_hash, "dataset_snapshot_id": "dataset-1", "git_commit_sha": "abc123", "environment_fingerprint": "env-v1", "random_seed": "7"}
        replay_execution = self.ledger.start_execution("human:owner", trial, execution_kind="REPRODUCIBILITY_REPLAY", original_execution_id=execution, replay_identity=replay)
        self.assertTrue(replay_execution)
        with self.assertRaises(LedgerError):
            self.ledger.start_execution("human:owner", trial, execution_kind="REPRODUCIBILITY_REPLAY", original_execution_id=execution, replay_identity={})

    def test_protocol_violation_does_not_create_trial(self):
        violation = self.ledger.record_protocol_violation("human:owner", "unregistered result", "external://opaque")
        self.assertTrue(violation)
        self.assertEqual(0, self.ledger._db.execute("SELECT COUNT(*) FROM trial_registrations").fetchone()[0])

    def test_all_authoritative_rows_reject_update_and_delete(self):
        self.register()
        for table in self.ledger._IMMUTABLE_TABLES:
            triggers = self.ledger._db.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'trigger' AND name IN (?, ?)",
                (f"immutable_{table}_update", f"immutable_{table}_delete"),
            ).fetchone()[0]
            self.assertEqual(2, triggers, table)
        for table in ("schema_metadata", "actor_identities", "research_specs", "trial_registrations", "registration_idempotency", "trial_events"):
            with self.assertRaises(sqlite3.DatabaseError, msg=table):
                self.ledger._db.execute(f"DELETE FROM {table}")

    def test_foreign_keys_prevent_orphans(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.ledger._db.execute("INSERT INTO execution_records VALUES ('orphan', 'missing', 'NORMAL', NULL, 't', 'human:owner', 1)")

    def test_chain_anchor_snapshot_backup_and_clean_reopen(self):
        self.register()
        snapshot = self.ledger.snapshot("human:owner")
        self.assertEqual(snapshot.as_of_ledger_sequence, self.ledger._db.execute("SELECT MAX(ledger_sequence) FROM trial_events").fetchone()[0])
        self.assertEqual(snapshot.content_hash, self.ledger.snapshot("human:owner").content_hash)
        anchor = self.ledger.create_anchor("human:owner")
        self.assertTrue(self.ledger.verify_anchor(anchor))
        backup_path = os.path.join(self.temp.name, "backup.db")
        backup(self.ledger, backup_path)
        self.assertTrue(verify_restored_backup(backup_path, snapshot, anchor))
        self.ledger.close()
        self.ledger = Ledger(self.path, authenticator=DeterministicFakeAuthenticator({"human:owner": "human:owner"}))
        self.assertTrue(self.ledger.verify_global_chain(anchor))

    def test_anchor_rejects_payload_mutation_and_tail_truncation(self):
        self.register()
        anchor = self.ledger.create_anchor("human:owner")
        altered = asdict(anchor)
        altered["payload"]["ledger_id"] = "wrong"
        self.assertFalse(self.ledger.verify_anchor(altered))
        self.ledger._db.execute("DROP TRIGGER immutable_trial_events_delete")
        self.ledger._db.execute("DELETE FROM trial_events WHERE ledger_sequence = (SELECT MAX(ledger_sequence) FROM trial_events)")
        self.assertFalse(self.ledger.verify_global_chain(anchor))

    def test_chain_detects_privileged_payload_tamper(self):
        self.register()
        self.ledger._db.execute("DROP TRIGGER immutable_trial_events_update")
        self.ledger._db.execute("UPDATE trial_events SET payload_json = '{}' WHERE ledger_sequence = 1")
        self.assertFalse(self.ledger.verify_global_chain())

    def test_real_concurrent_distinct_and_duplicate_registration(self):
        results, failures = [], []
        def distinct(index):
            try: results.append(self.register(f"distinct-{index}", hypothesis_id=f"h-{index}"))
            except Exception as error: failures.append(error)
        threads = [threading.Thread(target=distinct, args=(index,)) for index in range(12)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertFalse(failures)
        self.assertEqual(12, len(set(results)))
        duplicate = []
        threads = [threading.Thread(target=lambda: duplicate.append(self.register("duplicate"))) for _ in range(12)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(1, len(set(duplicate)))
        self.assertTrue(self.ledger.verify_global_chain())

    def test_historical_snapshot_excludes_future_facts_and_is_stable(self):
        trial = self.register("historic")
        boundary = self.ledger._db.execute("SELECT MAX(ledger_sequence) FROM trial_events").fetchone()[0]
        before = self.ledger.snapshot("human:owner", as_of_ledger_sequence=boundary)
        execution = self.ledger.start_execution("human:owner", trial)
        self.ledger.complete_execution("human:owner", execution)
        self.ledger.attach_result("human:owner", trial, execution, "metric", "external://result")
        self.ledger.attach_artifact("human:owner", trial, execution, "artifact", "external://artifact")
        _, spec_hash = hash_research_spec(spec())
        replay_identity = {"research_spec_sha256": spec_hash, "dataset_snapshot_id": "dataset-1", "git_commit_sha": "abc123", "environment_fingerprint": "env-v1", "random_seed": "7"}
        self.ledger.start_execution("human:owner", trial, execution_kind="REPRODUCIBILITY_REPLAY", original_execution_id=execution, replay_identity=replay_identity)
        self.ledger.record_protocol_violation("human:owner", "future violation")
        self.register("future", hypothesis_id="future")
        after = self.ledger.snapshot("human:owner", as_of_ledger_sequence=boundary)
        self.assertEqual(before.evidence, after.evidence)
        self.assertEqual(before.content_hash, after.content_hash)
        evidence = parse_json_strict(before.evidence.decode())
        self.assertEqual(1, evidence["registered_attempt_count"])
        self.assertEqual(0, evidence["performance_evaluated_count"])
        self.assertEqual(0, evidence["replay_count"])
        self.assertEqual([], evidence["result_references"])
        self.assertEqual([], evidence["artifact_references"])
        self.assertEqual([], evidence["protocol_violations"])

    def test_event_linkage_field_tampering_is_detected(self):
        mutations = (("execution_id", None), ("occurred_at", "2099-01-01T00:00:00.000000Z"), ("event_id", "bad-event"))
        for index, (field, value) in enumerate(mutations):
            if index:
                self.ledger.close()
                self.temp.cleanup()
                self.setUp()
            execution = self.ledger.start_execution("human:owner", self.register())
            sequence = self.ledger._db.execute("SELECT ledger_sequence FROM trial_events WHERE execution_id = ?", (execution,)).fetchone()[0]
            self.ledger._db.execute("DROP TRIGGER IF EXISTS immutable_trial_events_update")
            self.ledger._db.execute(f"UPDATE trial_events SET {field} = ? WHERE ledger_sequence = ?", (value, sequence))
            self.assertFalse(self.ledger.verify_global_chain(), field)

    def test_unchained_lifecycle_projection_is_detected(self):
        constructors = (
            ("actor_status_events", "INSERT INTO actor_status_events VALUES ('s', 'human:owner', 'ACTOR_ACTIVATED', 't', 'human:owner', 'bad', 'absent')"),
            ("capability_events", "INSERT INTO capability_events VALUES ('c', 'human:owner', 'TRIAL_REGISTER', 'CAPABILITY_GRANTED', 'V1', 't', 'human:owner', 'bad', 'absent')"),
            ("family_policy_events", "INSERT INTO family_policy_events VALUES ('p', 'P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1', '1', 'FAMILY_POLICY_ACTIVATED', 't', 'human:owner', 'bad', 'absent')"),
        )
        for table, statement in constructors:
            with self.subTest(table=table):
                self.ledger._db.execute(f"DROP TRIGGER immutable_{table}_update")
                self.ledger._db.execute(f"DROP TRIGGER immutable_{table}_delete")
                self.ledger._db.execute(statement)
                self.assertFalse(self.ledger.verify_global_chain())
                with self.assertRaises(LedgerError):
                    self.ledger.snapshot("human:owner")
                self.ledger.close()
                self.temp.cleanup()
                self.setUp()

    def test_retired_actor_and_policy_are_terminal(self):
        self.ledger.register_actor("human:owner", "generator:retire")
        self.ledger.set_actor_status("human:owner", "generator:retire", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("human:owner", "generator:retire", Capability.TRIAL_REGISTER)
        self.ledger.set_actor_status("human:owner", "generator:retire", "ACTOR_RETIRED")
        with self.assertRaises(LedgerError):
            self.ledger.set_actor_status("human:owner", "generator:retire", "ACTOR_ACTIVATED")
        with self.assertRaises(LedgerError):
            self.ledger.register("generator:retire", "x", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs={})
        self.ledger.retire_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1")
        with self.assertRaises(LedgerError):
            self.ledger.activate_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1")

    def test_external_anchor_artifact_and_truncation_detection(self):
        self.register()
        anchor = self.ledger.create_anchor("human:owner")
        with tempfile.TemporaryDirectory(dir=Path(self.temp.name).parent) as external:
            artifact = Path(external) / "anchor.json"
            self.assertNotEqual(artifact.parent.resolve(), Path(self.path).parent.resolve())
            write_anchor_artifact(artifact, anchor)
            loaded = load_anchor_artifact(artifact)
            self.assertTrue(self.ledger.verify_anchor(loaded))
            self.ledger._db.execute("DROP TRIGGER immutable_trial_events_delete")
            self.ledger._db.execute("DELETE FROM trial_events WHERE ledger_sequence = (SELECT MAX(ledger_sequence) FROM trial_events)")
            self.assertFalse(self.ledger.verify_anchor(loaded))


class FrozenVectorTests(unittest.TestCase):
    def test_string_escape_vectors_are_frozen(self):
        # Exact byte and SHA vectors prevent canonical escape regressions.
        vectors = (
            ("\n", b'{"value":"\\u000a"}', "bd3ba95c9aa5b05ad84b98e21d40803a7c78d39bf85747bfc3f2dfdded73d57e"),
            ("\\n", b'{"value":"\\\\n"}', "dd3bb0194cbd1deaecde8cdaa38a87579850ae9061ca9ca25cc44c2d7905e826"),
            ("\t", b'{"value":"\\u0009"}', "7b628ddf0b215926ccfb0795f9568cb6df7ff1d7dfa222dd2e030f09771dc1cf"),
            ("\\t", b'{"value":"\\\\t"}', "fae4f67c44f9c51bdc8eccbc9c1ef6a04ddb20654ba2caf25fd8c9f99a2d72b8"),
            ("\\u000a", b'{"value":"\\\\u000a"}', "68cb5bb8c7014c6fb20192bb08fb58ceda5c8d41662741bafd49063e192f9d6f"),
        )
        for value, expected, digest in vectors:
            with self.subTest(value=repr(value)):
                self.assertEqual(canonical_json_bytes({"value": value}), expected)
                self.assertEqual(__import__("hashlib").sha256(expected).hexdigest(), digest)
                self.assertEqual(parse_json_strict(expected.decode("utf-8")), {"value": value})

    def test_family_policy_spec_hash_vector_is_frozen(self):
        rules_hash = "aa5bc61f44d5f633935d04cbccf2654c56806fc924b0083a6cb6b7545369ad64"
        identity = {
            "family_policy_id": "policy-fixed", "family_policy_version": "1",
            "policy_schema_version": "V1", "policy_rules_hash": rules_hash,
            "effective_from": "2026-09-10T12:34:56.000000Z",
        }
        expected = b'{"effective_from":"2026-09-10T12:34:56.000000Z","family_policy_id":"policy-fixed","family_policy_version":"1","policy_rules_hash":"aa5bc61f44d5f633935d04cbccf2654c56806fc924b0083a6cb6b7545369ad64","policy_schema_version":"V1"}'
        self.assertEqual(canonical_json_bytes(identity), expected)
        self.assertEqual(__import__("hashlib").sha256(expected).hexdigest(), "06f1c6486b8fd31884c2425ad195cf2848dcfb1d20a7fb052253c33bc0da8359")
        self.assertNotEqual(rules_hash, "06f1c6486b8fd31884c2425ad195cf2848dcfb1d20a7fb052253c33bc0da8359")

    def test_event_hash_vector_is_frozen(self):
        envelope = {
            "hash_domain_version": "AQ_LEDGER_EVENT_HASH_V1", "ledger_id": "ledger-fixed",
            "schema_version": "1", "ledger_sequence": 7, "previous_global_event_hash": "0" * 64,
            "event_id": "event-fixed", "execution_id": "execution-fixed",
            "occurred_at": "2026-09-10T12:34:56.000000Z", "event_type": "TRIAL_STARTED",
            "actor_id": "human:owner", "trial_id": "trial-fixed", "payload": {"kind": "NORMAL"},
        }
        self.assertEqual(
            canonical_json_bytes(envelope),
            b'{"actor_id":"human:owner","event_id":"event-fixed","event_type":"TRIAL_STARTED","execution_id":"execution-fixed","hash_domain_version":"AQ_LEDGER_EVENT_HASH_V1","ledger_id":"ledger-fixed","ledger_sequence":7,"occurred_at":"2026-09-10T12:34:56.000000Z","payload":{"kind":"NORMAL"},"previous_global_event_hash":"0000000000000000000000000000000000000000000000000000000000000000","schema_version":"1","trial_id":"trial-fixed"}',
        )
        self.assertEqual(event_hash(envelope), "c5c326b51dfee5633c439c9bd8c9d42d35169d6e57ed13d052a083a475719728")

    def test_anchor_payload_vector_is_frozen(self):
        payload = {"ledger_id": "ledger-fixed", "as_of_ledger_sequence": 7, "global_event_hash": "a" * 64,
                   "schema_version": "1", "created_at": "2026-09-10T12:34:56.000000Z", "created_by": "human:owner",
                   "manifest_schema_version": "1", "canonicalization_version": "AQ_LEDGER_ANCHOR_CANONICAL_V1"}
        self.assertEqual(
            canonicalize_anchor_payload(payload),
            b'{"canonicalization_version":"AQ_LEDGER_ANCHOR_CANONICAL_V1","payload":{"as_of_ledger_sequence":7,"canonicalization_version":"AQ_LEDGER_ANCHOR_CANONICAL_V1","created_at":"2026-09-10T12:34:56.000000Z","created_by":"human:owner","global_event_hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","ledger_id":"ledger-fixed","manifest_schema_version":"1","schema_version":"1"}}',
        )
        self.assertEqual(__import__("hashlib").sha256(canonicalize_anchor_payload(payload)).hexdigest(), "e68a6d9793db3d52c3270ff4cfb820ab6d5af580b31881a30a3160fafd3c5f07")

    def test_deterministic_snapshot_vector_is_frozen(self):
        temporary_root = Path(__file__).parent / ".temporary-ledger-tests"
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            identifiers = iter(f"id-{number}" for number in range(100))
            ledger = Ledger(
                Path(directory) / "fixed.db", clock=lambda: "2026-09-10T12:34:56.000000Z",
                id_factory=lambda: next(identifiers), ledger_id_factory=lambda: "ledger-fixed",
                authenticator=DeterministicFakeAuthenticator({"human:owner": "human:owner"}),
            )
            try:
                ledger.init()
                ledger.register_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {"version": "1"})
                ledger.activate_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1")
                ledger.register("human:owner", "fixed-key", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1,
                                family_policy_version="1", family_inputs={"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"})
                snapshot = ledger.snapshot("human:owner")
                self.assertEqual(snapshot.content_hash, "0373ed43143468884390c492ca55de94334109fd80482a2dced5057b6f0cda9e")
            finally:
                ledger.close()


if __name__ == "__main__":
    unittest.main()
