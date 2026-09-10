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

from aq_trial_ledger.backup import backup, load_anchor_artifact, verify_restored_backup, write_anchor_artifact
from aq_trial_ledger.canonical import CanonicalizationError, canonical_json_bytes, canonicalize_anchor_payload, canonicalize_research_spec, event_hash, hash_research_spec, parse_json_strict
from aq_trial_ledger.contract import Capability, P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1
from aq_trial_ledger.storage import Ledger, LedgerError


def spec(**changes):
    value = {
        "generator": "unit-generator", "generator_version": "1", "hypothesis_id": "h-1",
        "factor_spec_hash": "factor-a", "model_spec_hash": "model-a", "hyperparameter_hash": "hyper-a",
        "dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a",
        "feature_set_hash": "features-a", "train_window": "2020-01-01/2020-12-31",
        "validation_window": "2021-01-01/2021-06-30", "exchange_calendar": "XNYS",
        "calendar_version": "1", "portfolio_rule_hash": "portfolio-a", "cost_assumption_hash": "cost-a",
        "benchmark_policy_hash": "benchmark-a", "git_commit_sha": "abc123",
        "environment_fingerprint": "env-v1", "random_seed": "7", "family_policy_inputs_hash": "family-a",
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
            b'{"canonicalization_version":"AQ_RESEARCH_SPEC_CANONICAL_V1","research_spec":{"benchmark_policy_hash":"benchmark-a","calendar_version":"1","cost_assumption_hash":"cost-a","dataset_snapshot_id":"dataset-1","environment_fingerprint":"env-v1","exchange_calendar":"XNYS","factor_spec_hash":"factor-a","family_policy_inputs_hash":"family-a","feature_set_hash":"features-a","generator":"unit-generator","generator_version":"1","git_commit_sha":"abc123","hyperparameter_hash":"hyper-a","hypothesis_id":"h-1","label_spec_hash":"label-a","model_spec_hash":"model-a","parameters":{"learning_rate":{"type":"decimal","value":"0.1"}},"portfolio_rule_hash":"portfolio-a","random_seed":"7","train_window":"2020-01-01/2020-12-31","universe_id":"us-large","validation_window":"2021-01-01/2021-06-30"}}',
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

    def test_negative_canonical_inputs(self):
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(unknown="no"))
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(extensions={1: "no"}))
        with self.assertRaises(CanonicalizationError):
            canonicalize_research_spec(spec(hypothesis_id="\ud800"))
        with self.assertRaises(CanonicalizationError):
            parse_json_strict('{"x":1,"x":2}')

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
        self.assertEqual(hash_research_spec(spec())[1], "6043aedb32b23df715f61d9f2f9ce12d9305f0a14172c6266db9ae38ceb5dd61")
        self.assertEqual(hash_research_spec(spec(hypothesis_text="é"))[1], "ec4374cd8a46ca65e50d4cb98cfcb2a2cd24ba258ccdcbe14dbbf23eec942258")
        self.assertEqual(hash_research_spec(spec(hypothesis_text="line\n"))[1], "a6e13511a3cac6ad862b7e46fffd4569ae1763f0735a890beeeb91bd5b068448")
        plus_eight = spec(extensions={"instant": datetime(2026, 9, 10, 8, tzinfo=timezone(timedelta(hours=8)))})
        utc = spec(extensions={"instant": datetime(2026, 9, 10, 0, tzinfo=timezone.utc)})
        self.assertEqual(hash_research_spec(plus_eight)[1], "27585662bb37d79a56d329a09771e64a39493533a298dd7eded7f5e150704106")
        self.assertEqual(hash_research_spec(plus_eight)[1], hash_research_spec(utc)[1])


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
        )

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
        self.assertGreater(self.ledger.db.execute("SELECT COUNT(*) FROM capability_events").fetchone()[0], 1)

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
            self.ledger.db.execute("INSERT INTO execution_records VALUES ('orphan', 'missing', 'NORMAL', NULL, 't', 'human:owner', 1)")

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

    def test_historical_snapshot_excludes_future_facts_and_is_stable(self):
        trial = self.register("historic")
        boundary = self.ledger.db.execute("SELECT MAX(ledger_sequence) FROM trial_events").fetchone()[0]
        before = self.ledger.snapshot(as_of_ledger_sequence=boundary)
        execution = self.ledger.start_execution("human:owner", trial)
        self.ledger.complete_execution("human:owner", execution)
        self.ledger.attach_result("human:owner", trial, execution, "metric", "external://result")
        self.ledger.attach_artifact("human:owner", trial, execution, "artifact", "external://artifact")
        _, spec_hash = hash_research_spec(spec())
        replay_identity = {"research_spec_sha256": spec_hash, "dataset_snapshot_id": "dataset-1", "git_commit_sha": "abc123", "environment_fingerprint": "env-v1", "random_seed": "7"}
        self.ledger.start_execution("human:owner", trial, execution_kind="REPRODUCIBILITY_REPLAY", original_execution_id=execution, replay_identity=replay_identity)
        self.ledger.record_protocol_violation("human:owner", "future violation")
        self.register("future", hypothesis_id="future")
        after = self.ledger.snapshot(as_of_ledger_sequence=boundary)
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
            sequence = self.ledger.db.execute("SELECT ledger_sequence FROM trial_events WHERE execution_id = ?", (execution,)).fetchone()[0]
            self.ledger.db.execute("DROP TRIGGER IF EXISTS immutable_trial_events_update")
            self.ledger.db.execute(f"UPDATE trial_events SET {field} = ? WHERE ledger_sequence = ?", (value, sequence))
            self.assertFalse(self.ledger.verify_global_chain(), field)

    def test_unchained_lifecycle_projection_is_detected(self):
        constructors = (
            ("actor_status_events", "INSERT INTO actor_status_events VALUES ('s', 'human:owner', 'ACTOR_ACTIVATED', 't', 'human:owner', 'bad', 'absent')"),
            ("capability_events", "INSERT INTO capability_events VALUES ('c', 'human:owner', 'TRIAL_REGISTER', 'CAPABILITY_GRANTED', 'V1', 't', 'human:owner', 'bad', 'absent')"),
            ("family_policy_events", "INSERT INTO family_policy_events VALUES ('p', 'P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1', '1', 'FAMILY_POLICY_ACTIVATED', 't', 'human:owner', 'bad', 'absent')"),
        )
        for table, statement in constructors:
            with self.subTest(table=table):
                self.ledger.db.execute(f"DROP TRIGGER immutable_{table}_update")
                self.ledger.db.execute(f"DROP TRIGGER immutable_{table}_delete")
                self.ledger.db.execute(statement)
                self.assertFalse(self.ledger.verify_global_chain())
                with self.assertRaises(LedgerError):
                    self.ledger.snapshot()
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
            self.ledger.db.execute("DROP TRIGGER immutable_trial_events_delete")
            self.ledger.db.execute("DELETE FROM trial_events WHERE ledger_sequence = (SELECT MAX(ledger_sequence) FROM trial_events)")
            self.assertFalse(self.ledger.verify_anchor(loaded))


class FrozenVectorTests(unittest.TestCase):
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
            )
            try:
                ledger.init()
                ledger.register_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1", {"version": "1"})
                ledger.activate_family_policy("human:owner", P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1, "1")
                ledger.register("human:owner", "fixed-key", spec(), family_policy_id=P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1,
                                family_policy_version="1", family_inputs={"dataset_snapshot_id": "dataset-1", "universe_id": "us-large", "label_spec_hash": "label-a", "feature_set_hash": "features-a", "research_objective": "test", "evaluation_window_policy": "v1"})
                snapshot = ledger.snapshot()
                self.assertEqual(snapshot.content_hash, "56e10ce6fd86f0719fbb360b64ab36327646c99236567eb0ea637453bcd0b88f")
            finally:
                ledger.close()


if __name__ == "__main__":
    unittest.main()
