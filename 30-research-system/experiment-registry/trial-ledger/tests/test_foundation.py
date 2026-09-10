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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from aq_trial_ledger.backup import backup, verify_restored_backup
from aq_trial_ledger.canonical import CanonicalizationError, canonicalize_research_spec, hash_research_spec, parse_json_strict
from aq_trial_ledger.contract import Capability, P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1
from aq_trial_ledger.storage import Ledger, LedgerError


def spec(**changes):
    value = {
        "generator": "unit-generator", "generator_version": "1", "hypothesis_id": "h-1",
        "dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a",
        "feature_set_hash": "features-a", "git_commit_sha": "abc123",
        "environment_fingerprint": "env-v1", "random_seed": "7", "parameters": {"learning_rate": "0.10"},
    }
    value.update(changes)
    return value


class CanonicalTests(unittest.TestCase):
    def test_key_order_and_decimal_vectors(self):
        first, first_hash = hash_research_spec(spec(), decimal_fields={"learning_rate"})
        second, second_hash = hash_research_spec(dict(reversed(list(spec().items()))), decimal_fields={"learning_rate"})
        self.assertEqual(first, second)
        self.assertEqual(first_hash, second_hash)
        self.assertIn(b'"learning_rate":"0.1"', first)

    def test_material_parameter_and_metadata_exclusion_rules(self):
        _, original = hash_research_spec(spec(), decimal_fields={"learning_rate"})
        _, changed = hash_research_spec(spec(parameters={"learning_rate": "0.11"}), decimal_fields={"learning_rate"})
        self.assertNotEqual(original, changed)
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(trial_id="not-permitted"))

    def test_unicode_and_escape_vectors(self):
        canonical = canonicalize_research_spec(spec(hypothesis_text="é / \" \\ \n"))
        self.assertIn("é".encode("utf-8"), canonical)
        self.assertIn(b"/", canonical)
        self.assertIn(b"\\u000a", canonical)
        self.assertNotIn(b"\\n", canonical)

    def test_schema_aware_opaque_string_and_decimal_rejections(self):
        opaque_one = canonicalize_research_spec(spec(hypothesis_id="e\u0301"))
        opaque_two = canonicalize_research_spec(spec(hypothesis_id="é"))
        self.assertNotEqual(opaque_one, opaque_two)
        self.assertEqual(
            canonicalize_research_spec(spec(hypothesis_text="e\u0301")),
            canonicalize_research_spec(spec(hypothesis_text="é")),
        )
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(parameters={"learning_rate": 0.1}), decimal_fields={"learning_rate"})
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(extensions={"sealed_oos_data": "no"}))

    def test_negative_canonical_inputs(self):
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(unknown="no"))
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(extensions={1: "no"}))
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(hypothesis_id="\ud800"))
        with self.assertRaises(CanonicalizationError):
            parse_json_strict('{"x":1,"x":2}')


class LedgerCase(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).parent / ".temporary-ledger-tests"
        temporary_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary_root)
        self.path = os.path.join(self.temp.name, "ledger.db")
        self.ledger = Ledger(self.path)
        self.ledger.init()
        self.ledger.register_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {"version": "1"})
        self.ledger.activate_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1")

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def register(self, key="one", **kwargs):
        return self.ledger.register(
            "human:owner", key, spec(**kwargs), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1,
            family_policy_version="1", family_inputs={"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"},
            decimal_fields={"learning_rate"},
        )

    def test_initialization_is_atomic_and_rejects_second_init(self):
        self.assertTrue(self.ledger.verify_global_chain())
        with self.assertRaises(LedgerError):
            self.ledger.init()

    def test_actor_and_capability_lifecycle_is_append_only(self):
        self.ledger.register_actor("human:owner", "generator:one")
        self.ledger.set_actor_status("human:owner", "generator:one", "ACTOR_ACTIVATED")
        self.ledger.grant_capability("human:owner", "generator:one", Capability.TRIAL_REGISTER)
        trial = self.ledger.register("generator:one", "key", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs={})
        self.assertTrue(trial)
        self.ledger.revoke_capability("human:owner", "generator:one", Capability.TRIAL_REGISTER)
        with self.assertRaises(LedgerError):
            self.ledger.register("generator:one", "other", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, family_policy_version="1", family_inputs={})
        self.ledger.set_actor_status("human:owner", "generator:one", "ACTOR_SUSPENDED")
        self.assertGreater(self.ledger.db.execute("SELECT COUNT(*) FROM capability_events").fetchone()[0], 1)

    def test_family_identity_and_retired_policy(self):
        first = self.ledger.family_id(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {"dataset": "a", "label": "b"})
        self.assertEqual(first, self.ledger.family_id(P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {"label": "b", "dataset": "a"}))
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
        _, spec_hash = hash_research_spec(spec(), decimal_fields={"learning_rate"})
        replay = {"research_spec_sha256": spec_hash, "dataset_snapshot_id": "dataset-1", "git_commit_sha": "abc123", "environment_fingerprint": "env-v1", "random_seed": "7"}
        replay_execution = self.ledger.start_execution("human:owner", trial, execution_kind="REPRODUCIBILITY_REPLAY", original_execution_id=execution, replay_identity=replay)
        self.assertTrue(replay_execution)
        with self.assertRaises(LedgerError):
            self.ledger.start_execution("human:owner", trial, execution_kind="REPRODUCIBILITY_REPLAY", original_execution_id=execution, replay_identity={})

    def test_protocol_violation_does_not_create_trial(self):
        violation = self.ledger.record_protocol_violation("human:owner", "unregistered result", "external://opaque")
        self.assertTrue(violation)
        self.assertEqual(0, self.ledger.db.execute("SELECT COUNT(*) FROM trial_registrations").fetchone()[0])

    def test_all_authoritative_rows_reject_update_and_delete(self):
        self.register()
        for table in self.ledger._IMMUTABLE_TABLES:
            triggers = self.ledger.db.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'trigger' AND name IN (?, ?)",
                (f"immutable_{table}_update", f"immutable_{table}_delete"),
            ).fetchone()[0]
            self.assertEqual(2, triggers, table)
        for table in ("schema_metadata", "actor_identities", "research_specs", "trial_registrations", "registration_idempotency", "trial_events"):
            with self.assertRaises(sqlite3.DatabaseError, msg=table):
                self.ledger.db.execute(f"DELETE FROM {table}")

    def test_foreign_keys_prevent_orphans(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.ledger.db.execute("INSERT INTO execution_records VALUES ('orphan', 'missing', 'NORMAL', NULL, 't', 'human:owner')")

    def test_chain_anchor_snapshot_backup_and_clean_reopen(self):
        self.register()
        snapshot = self.ledger.snapshot()
        self.assertEqual(snapshot.as_of_ledger_sequence, self.ledger.db.execute("SELECT MAX(ledger_sequence) FROM trial_events").fetchone()[0])
        self.assertEqual(snapshot.content_hash, self.ledger.snapshot().content_hash)
        anchor = self.ledger.create_anchor("human:owner")
        self.assertTrue(self.ledger.verify_anchor(anchor))
        backup_path = os.path.join(self.temp.name, "backup.db")
        backup(self.ledger, backup_path)
        self.assertTrue(verify_restored_backup(backup_path, snapshot, anchor))
        self.ledger.close()
        self.ledger = Ledger(self.path)
        self.assertTrue(self.ledger.verify_global_chain(anchor))

    def test_anchor_rejects_payload_mutation_and_tail_truncation(self):
        self.register()
        anchor = self.ledger.create_anchor("human:owner")
        altered = asdict(anchor)
        altered["payload"]["ledger_id"] = "wrong"
        self.assertFalse(self.ledger.verify_anchor(altered))
        self.ledger.db.execute("DROP TRIGGER immutable_trial_events_delete")
        self.ledger.db.execute("DELETE FROM trial_events WHERE ledger_sequence = (SELECT MAX(ledger_sequence) FROM trial_events)")
        self.assertFalse(self.ledger.verify_global_chain(anchor))

    def test_chain_detects_privileged_payload_tamper(self):
        self.register()
        self.ledger.db.execute("DROP TRIGGER immutable_trial_events_update")
        self.ledger.db.execute("UPDATE trial_events SET payload_json = '{}' WHERE ledger_sequence = 1")
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


if __name__ == "__main__":
    unittest.main()
