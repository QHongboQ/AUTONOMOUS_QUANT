"""SQLite repository and single-process writer for the Trial Ledger."""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .canonical import (
    EVENT_HASH_DOMAIN_V1,
    canonical_json_bytes,
    canonicalize_anchor_payload,
    event_hash,
    hash_research_spec,
    parse_json_strict,
)
from .contract import (
    Capability,
    LedgerAnchorManifest,
    LedgerAnchorManifestPayload,
    P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1,
    TrialHistorySnapshot,
)

SCHEMA_VERSION = "1"
GENESIS_PREVIOUS_HASH = "0" * 64


class LedgerError(ValueError):
    """Raised when an operation would violate the immutable ledger contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Ledger:
    """A serialized local SQLite writer; callers never receive mutable rows."""

    _IMMUTABLE_TABLES = (
        "schema_metadata", "actor_identities", "actor_status_events", "capability_events",
        "family_policy_specs", "family_policy_events", "research_specs",
        "trial_registrations", "registration_idempotency", "execution_records",
        "trial_events", "result_references", "artifact_references", "protocol_violations",
        "anchor_evidence",
    )

    def __init__(
        self, path: str | Path, *, clock: Any = utc_now, id_factory: Any = lambda: str(uuid.uuid4()),
        ledger_id_factory: Any | None = None,
    ):
        self.path = str(path)
        self._clock = clock
        self._id_factory = id_factory
        self._ledger_id_factory = ledger_id_factory or id_factory
        self.db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA busy_timeout = 5000")

    def close(self) -> None:
        self.db.close()

    def _transaction(self) -> None:
        self.db.execute("BEGIN IMMEDIATE")

    def _commit(self) -> None:
        self.db.execute("COMMIT")

    def _rollback(self) -> None:
        self.db.execute("ROLLBACK")

    def _run_write(self, operation: Any) -> Any:
        with self.lock:
            self._transaction()
            try:
                result = operation()
            except Exception:
                self._rollback()
                raise
            self._commit()
            return result

    def _metadata(self, key: str) -> str:
        row = self.db.execute(
            "SELECT value FROM schema_metadata WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            raise LedgerError("ledger is not initialized")
        return str(row["value"])

    def _create_schema(self) -> None:
        self.db.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE actor_identities (
                actor_id TEXT PRIMARY KEY, actor_type TEXT NOT NULL, actor_version TEXT NOT NULL,
                display_name TEXT NOT NULL, credential_binding TEXT NOT NULL,
                authentication_method TEXT NOT NULL, created_at TEXT NOT NULL,
                metadata_schema_version TEXT NOT NULL, global_event_id TEXT NOT NULL UNIQUE
            );
            CREATE TABLE actor_status_events (
                status_event_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL, actor_id_by TEXT NOT NULL, reason TEXT NOT NULL,
                global_event_id TEXT NOT NULL UNIQUE,
                FOREIGN KEY(actor_id) REFERENCES actor_identities(actor_id),
                FOREIGN KEY(actor_id_by) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE capability_events (
                capability_event_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, capability TEXT NOT NULL,
                event_type TEXT NOT NULL, policy_version TEXT NOT NULL, occurred_at TEXT NOT NULL,
                actor_id_by TEXT NOT NULL, reason TEXT NOT NULL, global_event_id TEXT NOT NULL UNIQUE,
                FOREIGN KEY(actor_id) REFERENCES actor_identities(actor_id),
                FOREIGN KEY(actor_id_by) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE family_policy_specs (
                family_policy_id TEXT NOT NULL, family_policy_version TEXT NOT NULL,
                policy_schema_version TEXT NOT NULL, policy_rules_hash TEXT NOT NULL,
                policy_rules_blob BLOB NOT NULL, effective_from TEXT NOT NULL,
                registered_at TEXT NOT NULL, registered_by TEXT NOT NULL,
                canonical_policy_hash TEXT NOT NULL, global_event_id TEXT NOT NULL UNIQUE,
                PRIMARY KEY(family_policy_id, family_policy_version),
                FOREIGN KEY(registered_by) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE family_policy_events (
                policy_event_id TEXT PRIMARY KEY, family_policy_id TEXT NOT NULL,
                family_policy_version TEXT NOT NULL, event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL, actor_id TEXT NOT NULL, reason TEXT NOT NULL,
                global_event_id TEXT NOT NULL UNIQUE,
                FOREIGN KEY(family_policy_id, family_policy_version)
                    REFERENCES family_policy_specs(family_policy_id, family_policy_version),
                FOREIGN KEY(actor_id) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE research_specs (
                canonical_research_spec_sha256 TEXT PRIMARY KEY, canonical_blob BLOB NOT NULL,
                created_ledger_sequence INTEGER NOT NULL
            );
            CREATE TABLE trial_registrations (
                trial_id TEXT PRIMARY KEY, canonical_research_spec_sha256 TEXT NOT NULL,
                trial_family_id TEXT NOT NULL, parent_trial_id TEXT, trial_kind TEXT NOT NULL,
                registration_actor TEXT NOT NULL, registered_at TEXT NOT NULL, schema_version TEXT NOT NULL,
                family_policy_id TEXT NOT NULL, family_policy_version TEXT NOT NULL,
                frozen_replay_identity_hash TEXT NOT NULL, created_ledger_sequence INTEGER NOT NULL,
                FOREIGN KEY(canonical_research_spec_sha256) REFERENCES research_specs(canonical_research_spec_sha256),
                FOREIGN KEY(parent_trial_id) REFERENCES trial_registrations(trial_id),
                FOREIGN KEY(registration_actor) REFERENCES actor_identities(actor_id),
                FOREIGN KEY(family_policy_id, family_policy_version)
                    REFERENCES family_policy_specs(family_policy_id, family_policy_version)
            );
            CREATE TABLE registration_idempotency (
                registration_actor TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                request_hash TEXT NOT NULL, trial_id TEXT NOT NULL,
                PRIMARY KEY(registration_actor, idempotency_key),
                FOREIGN KEY(registration_actor) REFERENCES actor_identities(actor_id),
                FOREIGN KEY(trial_id) REFERENCES trial_registrations(trial_id)
            );
            CREATE TABLE execution_records (
                execution_id TEXT PRIMARY KEY, trial_id TEXT NOT NULL, execution_kind TEXT NOT NULL,
                original_execution_id TEXT, created_at TEXT NOT NULL, actor_id TEXT NOT NULL,
                created_ledger_sequence INTEGER NOT NULL,
                FOREIGN KEY(trial_id) REFERENCES trial_registrations(trial_id),
                FOREIGN KEY(original_execution_id) REFERENCES execution_records(execution_id),
                FOREIGN KEY(actor_id) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE trial_events (
                event_id TEXT PRIMARY KEY, ledger_sequence INTEGER NOT NULL UNIQUE,
                trial_id TEXT, execution_id TEXT, event_type TEXT NOT NULL, actor_id TEXT NOT NULL,
                occurred_at TEXT NOT NULL, payload_json TEXT NOT NULL,
                previous_global_event_hash TEXT NOT NULL, global_event_hash TEXT NOT NULL,
                FOREIGN KEY(trial_id) REFERENCES trial_registrations(trial_id),
                FOREIGN KEY(execution_id) REFERENCES execution_records(execution_id),
                FOREIGN KEY(actor_id) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE result_references (
                reference_id TEXT PRIMARY KEY, trial_id TEXT NOT NULL, execution_id TEXT NOT NULL,
                reference_type TEXT NOT NULL, locator TEXT NOT NULL, content_hash TEXT,
                created_at TEXT NOT NULL, actor_id TEXT NOT NULL, created_ledger_sequence INTEGER NOT NULL,
                FOREIGN KEY(trial_id) REFERENCES trial_registrations(trial_id),
                FOREIGN KEY(execution_id) REFERENCES execution_records(execution_id),
                FOREIGN KEY(actor_id) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE artifact_references (
                reference_id TEXT PRIMARY KEY, trial_id TEXT NOT NULL, execution_id TEXT NOT NULL,
                reference_type TEXT NOT NULL, locator TEXT NOT NULL, content_hash TEXT,
                created_at TEXT NOT NULL, actor_id TEXT NOT NULL, created_ledger_sequence INTEGER NOT NULL,
                FOREIGN KEY(trial_id) REFERENCES trial_registrations(trial_id),
                FOREIGN KEY(execution_id) REFERENCES execution_records(execution_id),
                FOREIGN KEY(actor_id) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE protocol_violations (
                violation_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, occurred_at TEXT NOT NULL,
                reason TEXT NOT NULL, external_reference TEXT, content_hash TEXT,
                created_ledger_sequence INTEGER NOT NULL,
                FOREIGN KEY(actor_id) REFERENCES actor_identities(actor_id)
            );
            CREATE TABLE anchor_evidence (
                manifest_sha256 TEXT PRIMARY KEY, payload_json TEXT NOT NULL, created_at TEXT NOT NULL,
                created_by TEXT NOT NULL, FOREIGN KEY(created_by) REFERENCES actor_identities(actor_id)
            );
        """)
        for table in self._IMMUTABLE_TABLES:
            self.db.execute(
                f"CREATE TRIGGER immutable_{table}_update BEFORE UPDATE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'immutable ledger row'); END"
            )
            self.db.execute(
                f"CREATE TRIGGER immutable_{table}_delete BEFORE DELETE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'immutable ledger row'); END"
            )

    def init(self, owner: str = "human:owner") -> str:
        """Atomically initialize only a completely empty database target."""
        with self.lock:
            tables = self.db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            if tables:
                raise LedgerError("ALREADY_INITIALIZED_OR_UNRELATED_DATABASE")
            self._create_schema()
            ledger_id = str(self._ledger_id_factory())
            try:
                self.db.executemany(
                    "INSERT INTO schema_metadata(key, value) VALUES (?, ?)",
                    (("ledger_id", ledger_id), ("schema_version", SCHEMA_VERSION),
                     ("event_hash_domain_version", EVENT_HASH_DOMAIN_V1)),
                )
                owner_created_at = self._clock()
                genesis_event_id = str(self._id_factory())
                owner_identity = {
                    "actor_id": owner, "actor_type": "HUMAN_OWNER", "actor_version": "V1",
                    "display_name": "Initial human owner", "credential_binding": "LOCAL_BOOTSTRAP",
                    "authentication_method": "LOCAL_OWNER", "created_at": owner_created_at,
                    "metadata_schema_version": "V1",
                }
                self.db.execute(
                    "INSERT INTO actor_identities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (*owner_identity.values(), genesis_event_id),
                )
                self._append_event(None, None, "GENESIS", owner, {
                    "ledger_id": ledger_id, "owner_identity": owner_identity,
                }, occurred_at=owner_created_at, event_id=genesis_event_id)
                self._append_actor_status(owner, "ACTOR_REGISTERED", owner, "genesis")
                self._append_actor_status(owner, "ACTOR_ACTIVATED", owner, "genesis")
                for capability in Capability:
                    if capability is not Capability.MAINTENANCE_ENTER:
                        self._append_capability(owner, capability.value, "CAPABILITY_GRANTED", owner, "V1", "genesis")
                self._commit()
                return ledger_id
            except Exception:
                self._rollback()
                raise

    def _next_sequence(self) -> int:
        row = self.db.execute("SELECT MAX(ledger_sequence) AS value FROM trial_events").fetchone()
        return 1 if row["value"] is None else int(row["value"]) + 1

    def _append_event(
        self, trial_id: str | None, execution_id: str | None, event_type: str,
        actor_id: str, payload: Mapping[str, Any], *, occurred_at: str | None = None,
        event_id: str | None = None,
    ) -> tuple[str, int, str]:
        last = self.db.execute(
            "SELECT ledger_sequence, global_event_hash FROM trial_events ORDER BY ledger_sequence DESC LIMIT 1"
        ).fetchone()
        sequence = 1 if last is None else int(last["ledger_sequence"]) + 1
        previous = GENESIS_PREVIOUS_HASH if last is None else str(last["global_event_hash"])
        event_id = event_id or str(self._id_factory())
        occurred_at = occurred_at or self._clock()
        envelope = {
            "hash_domain_version": EVENT_HASH_DOMAIN_V1,
            "ledger_id": self._metadata("ledger_id"), "schema_version": SCHEMA_VERSION,
            "ledger_sequence": sequence, "previous_global_event_hash": previous,
            "event_id": event_id, "execution_id": execution_id, "occurred_at": occurred_at,
            "event_type": event_type, "actor_id": actor_id, "trial_id": trial_id,
            "payload": payload,
        }
        digest = event_hash(envelope)
        self.db.execute(
            "INSERT INTO trial_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, sequence, trial_id, execution_id, event_type, actor_id, occurred_at,
             canonical_json_bytes(payload).decode("utf-8"), previous, digest),
        )
        return event_id, sequence, digest

    def _actor_is_active(self, actor_id: str) -> bool:
        row = self.db.execute(
            "SELECT event_type FROM actor_status_events WHERE actor_id = ? ORDER BY rowid DESC LIMIT 1",
            (actor_id,),
        ).fetchone()
        return row is not None and row["event_type"] == "ACTOR_ACTIVATED"

    def _capability_is_active(self, actor_id: str, capability: str) -> bool:
        row = self.db.execute(
            "SELECT event_type FROM capability_events WHERE actor_id = ? AND capability = ? "
            "ORDER BY rowid DESC LIMIT 1", (actor_id, capability),
        ).fetchone()
        return row is not None and row["event_type"] == "CAPABILITY_GRANTED"

    def _require(self, actor_id: str, capability: Capability) -> None:
        if (not self.verify_global_chain() or not self._actor_is_active(actor_id)
                or not self._capability_is_active(actor_id, capability.value)):
            raise LedgerError(f"UNAUTHORIZED:{capability.value}")

    def _append_actor_status(self, actor_id: str, event_type: str, by: str, reason: str) -> None:
        status_event_id = str(self._id_factory())
        occurred_at = self._clock()
        global_event_id, _, _ = self._append_event(None, None, event_type, by, {
            "status_event_id": status_event_id, "actor_id": actor_id, "event_type": event_type,
            "occurred_at": occurred_at, "actor_id_by": by, "reason": reason,
        }, occurred_at=occurred_at)
        self.db.execute(
            "INSERT INTO actor_status_events VALUES (?, ?, ?, ?, ?, ?, ?)",
            (status_event_id, actor_id, event_type, occurred_at, by, reason, global_event_id),
        )

    def _append_capability(
        self, actor_id: str, capability: str, event_type: str, by: str,
        policy_version: str, reason: str,
    ) -> None:
        capability_event_id = str(self._id_factory())
        occurred_at = self._clock()
        global_event_id, _, _ = self._append_event(None, None, event_type, by, {
            "capability_event_id": capability_event_id, "actor_id": actor_id, "capability": capability,
            "event_type": event_type, "policy_version": policy_version, "occurred_at": occurred_at,
            "actor_id_by": by, "reason": reason,
        }, occurred_at=occurred_at)
        self.db.execute(
            "INSERT INTO capability_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (capability_event_id, actor_id, capability, event_type, policy_version, occurred_at, by, reason, global_event_id),
        )

    def register_actor(self, by: str, actor_id: str, actor_type: str = "RESEARCH_GENERATOR") -> None:
        def operation() -> None:
            self._require(by, Capability.ACTOR_ADMIN)
            occurred_at = self._clock()
            status_event_id = str(self._id_factory())
            identity = {
                "actor_id": actor_id, "actor_type": actor_type, "actor_version": "V1",
                "display_name": actor_id, "credential_binding": "LOCAL",
                "authentication_method": "LOCAL", "created_at": occurred_at,
                "metadata_schema_version": "V1",
            }
            global_event_id, _, _ = self._append_event(None, None, "ACTOR_REGISTERED", by, {
                "status_event_id": status_event_id, "actor_id": actor_id,
                "event_type": "ACTOR_REGISTERED", "occurred_at": occurred_at,
                "actor_id_by": by, "reason": "registered", "actor_identity": identity,
            }, occurred_at=occurred_at)
            self.db.execute(
                "INSERT INTO actor_identities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (*identity.values(), global_event_id),
            )
            self.db.execute(
                "INSERT INTO actor_status_events VALUES (?, ?, ?, ?, ?, ?, ?)",
                (status_event_id, actor_id, "ACTOR_REGISTERED", occurred_at, by, "registered", global_event_id),
            )

        self._run_write(operation)

    def set_actor_status(self, by: str, actor_id: str, status: str, reason: str = "") -> None:
        if status not in {"ACTOR_ACTIVATED", "ACTOR_SUSPENDED", "ACTOR_RETIRED"}:
            raise LedgerError("invalid actor status")
        def operation() -> None:
            self._require(by, Capability.ACTOR_ADMIN)
            current = self.db.execute("SELECT event_type FROM actor_status_events WHERE actor_id = ? ORDER BY rowid DESC LIMIT 1", (actor_id,)).fetchone()
            transition = (None if current is None else current["event_type"], status)
            allowed = {("ACTOR_REGISTERED", "ACTOR_ACTIVATED"), ("ACTOR_ACTIVATED", "ACTOR_SUSPENDED"),
                       ("ACTOR_SUSPENDED", "ACTOR_ACTIVATED"), ("ACTOR_ACTIVATED", "ACTOR_RETIRED"),
                       ("ACTOR_SUSPENDED", "ACTOR_RETIRED")}
            if transition not in allowed:
                raise LedgerError("illegal or terminal actor lifecycle transition")
            self._append_actor_status(actor_id, status, by, reason)
        self._run_write(operation)

    def grant_capability(self, by: str, actor_id: str, capability: Capability, reason: str = "") -> None:
        self._run_write(lambda: (self._require(by, Capability.CAPABILITY_ADMIN),
                                 self._append_capability(actor_id, capability.value, "CAPABILITY_GRANTED", by, "V1", reason)))

    def revoke_capability(self, by: str, actor_id: str, capability: Capability, reason: str = "") -> None:
        self._run_write(lambda: (self._require(by, Capability.CAPABILITY_ADMIN),
                                 self._append_capability(actor_id, capability.value, "CAPABILITY_REVOKED", by, "V1", reason)))

    def _policy_is_active(self, policy_id: str, version: str) -> bool:
        row = self.db.execute(
            "SELECT event_type FROM family_policy_events WHERE family_policy_id = ? "
            "AND family_policy_version = ? ORDER BY rowid DESC LIMIT 1", (policy_id, version),
        ).fetchone()
        return row is not None and row["event_type"] == "FAMILY_POLICY_ACTIVATED"

    def register_family_policy(self, actor: str, policy_id: str, version: str, rules: Mapping[str, Any]) -> None:
        def operation() -> None:
            self._require(actor, Capability.FAMILY_POLICY_ADMIN)
            rules_blob = canonical_json_bytes(rules)
            rules_hash = hashlib.sha256(rules_blob).hexdigest()
            occurred_at = self._clock()
            effective_from = occurred_at
            policy_identity = {
                "family_policy_id": policy_id, "family_policy_version": version,
                "policy_schema_version": "V1", "policy_rules_hash": rules_hash,
                "effective_from": effective_from,
            }
            policy_hash = hashlib.sha256(canonical_json_bytes(policy_identity)).hexdigest()
            policy_event_id = str(self._id_factory())
            global_event_id, _, _ = self._append_event(None, None, "FAMILY_POLICY_REGISTERED", actor, {
                "policy_event_id": policy_event_id, "family_policy_id": policy_id,
                "family_policy_version": version, "event_type": "FAMILY_POLICY_REGISTERED",
                "occurred_at": occurred_at, "actor_id": actor, "reason": "registered",
                "policy_rules_hash": rules_hash, "canonical_policy_hash": policy_hash,
                "effective_from": effective_from,
            }, occurred_at=occurred_at)
            self.db.execute(
                "INSERT INTO family_policy_specs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (policy_id, version, "V1", rules_hash, rules_blob, effective_from, occurred_at, actor,
                 policy_hash, global_event_id),
            )
            self.db.execute(
                "INSERT INTO family_policy_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (policy_event_id, policy_id, version, "FAMILY_POLICY_REGISTERED", occurred_at, actor, "registered", global_event_id),
            )

        self._run_write(operation)

    def _change_policy_state(self, actor: str, policy_id: str, version: str, event_type: str) -> None:
        def operation() -> None:
            self._require(actor, Capability.FAMILY_POLICY_ADMIN)
            if not self.db.execute("SELECT 1 FROM family_policy_specs WHERE family_policy_id = ? AND family_policy_version = ?", (policy_id, version)).fetchone():
                raise LedgerError("unknown family policy")
            current = self.db.execute("SELECT event_type FROM family_policy_events WHERE family_policy_id = ? AND family_policy_version = ? ORDER BY rowid DESC LIMIT 1", (policy_id, version)).fetchone()
            allowed = {("FAMILY_POLICY_REGISTERED", "FAMILY_POLICY_ACTIVATED"),
                       ("FAMILY_POLICY_ACTIVATED", "FAMILY_POLICY_RETIRED")}
            if current is None or (current["event_type"], event_type) not in allowed:
                raise LedgerError("illegal or terminal family-policy lifecycle transition")
            policy_event_id = str(self._id_factory())
            occurred_at = self._clock()
            global_event_id, _, _ = self._append_event(None, None, event_type, actor, {
                "policy_event_id": policy_event_id, "family_policy_id": policy_id,
                "family_policy_version": version, "event_type": event_type,
                "occurred_at": occurred_at, "actor_id": actor, "reason": event_type,
            }, occurred_at=occurred_at)
            self.db.execute("INSERT INTO family_policy_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (policy_event_id, policy_id, version, event_type, occurred_at, actor, event_type, global_event_id))

        self._run_write(operation)

    def activate_family_policy(self, actor: str, policy_id: str, version: str) -> None:
        self._change_policy_state(actor, policy_id, version, "FAMILY_POLICY_ACTIVATED")

    def retire_family_policy(self, actor: str, policy_id: str, version: str) -> None:
        self._change_policy_state(actor, policy_id, version, "FAMILY_POLICY_RETIRED")

    @staticmethod
    def canonical_family_inputs(policy_id: str, version: str, inputs: Mapping[str, Any]) -> bytes:
        if policy_id == P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1:
            # The P1 fixture groups model and hyperparameter variants under one
            # predeclared broad family.  Only its declared non-performance axes
            # participate in identity.
            selected = {
                key: inputs.get(key)
                for key in (
                    "dataset_snapshot_id", "universe_id", "universe_hash", "label_spec_hash",
                    "feature_set_hash", "research_objective", "evaluation_window_policy",
                )
                if key in inputs
            }
            required = {"dataset_snapshot_id", "label_spec_hash", "feature_set_hash",
                        "research_objective", "evaluation_window_policy"}
            if not ({"universe_id", "universe_hash"} & set(selected)):
                raise LedgerError("P1 family requires universe identity")
            missing = required - set(selected)
            if missing or any(selected.get(key) in (None, "") for key in required):
                raise LedgerError(f"P1 family missing required axes: {sorted(missing)!r}")
        else:
            selected = dict(inputs)
        return canonical_json_bytes({
            "family_policy_id": policy_id, "family_policy_version": version, "declared_inputs": selected,
        })

    @classmethod
    def family_input_hash(cls, policy_id: str, version: str, inputs: Mapping[str, Any]) -> str:
        return hashlib.sha256(cls.canonical_family_inputs(policy_id, version, inputs)).hexdigest()

    @classmethod
    def family_id(cls, policy_id: str, version: str, inputs: Mapping[str, Any]) -> str:
        return hashlib.sha256(cls.canonical_family_inputs(policy_id, version, inputs)).hexdigest()

    @staticmethod
    def _replay_identity(spec: Mapping[str, Any], spec_hash: str) -> Mapping[str, Any]:
        return {
            "research_spec_sha256": spec_hash, "dataset_snapshot_id": spec["dataset_snapshot_id"],
            "git_commit_sha": spec["git_commit_sha"], "environment_fingerprint": spec["environment_fingerprint"],
            "random_seed": spec["random_seed"],
        }

    def register(
        self, actor: str, idempotency_key: str, spec: Mapping[str, Any], *,
        family_policy_id: str, family_policy_version: str, family_inputs: Mapping[str, Any],
        trial_kind: str = "INDEPENDENT_EVALUATION", parent_trial_id: str | None = None,
        request_id: str | None = None,
    ) -> str:
        def operation() -> str:
            self._require(actor, Capability.TRIAL_REGISTER)
            if not self._policy_is_active(family_policy_id, family_policy_version):
                raise LedgerError("inactive or retired family policy")
            if parent_trial_id is not None and not self.db.execute("SELECT 1 FROM trial_registrations WHERE trial_id = ?", (parent_trial_id,)).fetchone():
                raise LedgerError("unknown parent trial")
            canonical, spec_hash = hash_research_spec(spec)
            family = self.family_id(family_policy_id, family_policy_version, family_inputs)
            if spec["family_policy_inputs_hash"] != self.family_input_hash(family_policy_id, family_policy_version, family_inputs):
                raise LedgerError("family inputs do not match frozen ResearchSpec hash")
            intent = {
                "research_spec_sha256": spec_hash, "trial_family_id": family,
                "parent_trial_id": parent_trial_id, "trial_kind": trial_kind,
                "family_policy_id": family_policy_id, "family_policy_version": family_policy_version,
            }
            request_hash = hashlib.sha256(canonical_json_bytes(intent)).hexdigest()
            existing = self.db.execute(
                "SELECT trial_id, request_hash FROM registration_idempotency WHERE registration_actor = ? AND idempotency_key = ?",
                (actor, idempotency_key),
            ).fetchone()
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise LedgerError("idempotency key has different registration intent")
                return str(existing["trial_id"])
            created_sequence = self._next_sequence()
            self.db.execute("INSERT OR IGNORE INTO research_specs VALUES (?, ?, ?)", (spec_hash, canonical, created_sequence))
            trial_id = str(self._id_factory())
            registered_at = self._clock()
            replay_hash = hashlib.sha256(canonical_json_bytes(self._replay_identity(spec, spec_hash))).hexdigest()
            self.db.execute(
                "INSERT INTO trial_registrations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (trial_id, spec_hash, family, parent_trial_id, trial_kind, actor, registered_at, SCHEMA_VERSION,
                 family_policy_id, family_policy_version, replay_hash, created_sequence),
            )
            self.db.execute("INSERT INTO registration_idempotency VALUES (?, ?, ?, ?)",
                            (actor, idempotency_key, request_hash, trial_id))
            _, sequence, _ = self._append_event(trial_id, None, "TRIAL_REGISTERED", actor, {
                **intent, "trial_id": trial_id, "request_id": request_id, "idempotency_key": idempotency_key,
                "registration_request_hash": request_hash, "registered_at": registered_at,
                "registration_actor": actor, "schema_version": SCHEMA_VERSION,
                "frozen_replay_identity_hash": replay_hash,
                "created_ledger_sequence": created_sequence,
            }, occurred_at=registered_at)
            if sequence != created_sequence:
                raise LedgerError("registration sequence assignment changed during transaction")
            return trial_id

        return self._run_write(operation)

    def _execution_status(self, execution_id: str) -> str | None:
        row = self.db.execute(
            "SELECT event_type FROM trial_events WHERE execution_id = ? "
            "AND event_type IN ('TRIAL_STARTED', 'TRIAL_COMPLETED', 'TRIAL_FAILED', 'TRIAL_CANCELLED') "
            "ORDER BY ledger_sequence DESC LIMIT 1", (execution_id,),
        ).fetchone()
        return None if row is None else str(row["event_type"])

    def start_execution(
        self, actor: str, trial_id: str, *, execution_kind: str = "NORMAL",
        original_execution_id: str | None = None, replay_identity: Mapping[str, Any] | None = None,
    ) -> str:
        def operation() -> str:
            self._require(actor, Capability.EXECUTION_APPEND)
            registration = self.db.execute("SELECT * FROM trial_registrations WHERE trial_id = ?", (trial_id,)).fetchone()
            if registration is None:
                raise LedgerError("unknown trial")
            if execution_kind == "REPRODUCIBILITY_REPLAY":
                original = self.db.execute("SELECT trial_id FROM execution_records WHERE execution_id = ?", (original_execution_id,)).fetchone()
                expected = str(registration["frozen_replay_identity_hash"])
                actual = hashlib.sha256(canonical_json_bytes(replay_identity or {})).hexdigest()
                if original is None or original["trial_id"] != trial_id or actual != expected:
                    raise LedgerError("replay identity differs from frozen registration")
            elif original_execution_id is not None:
                raise LedgerError("only reproducibility replay may link original execution")
            execution_id = str(self._id_factory())
            created_sequence = self._next_sequence() + (1 if execution_kind == "REPRODUCIBILITY_REPLAY" else 0)
            created_at = self._clock()
            self.db.execute("INSERT INTO execution_records VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (execution_id, trial_id, execution_kind, original_execution_id, created_at, actor, created_sequence))
            if execution_kind == "REPRODUCIBILITY_REPLAY":
                self._append_event(
                    trial_id, execution_id, "REPLAY_LINKED", actor,
                    {"original_execution_id": original_execution_id}, occurred_at=created_at,
                )
            self._append_event(trial_id, execution_id, "TRIAL_STARTED", actor, {
                "execution_id": execution_id, "trial_id": trial_id, "execution_kind": execution_kind,
                "original_execution_id": original_execution_id, "created_at": created_at,
                "actor_id": actor, "created_ledger_sequence": created_sequence,
            }, occurred_at=created_at)
            return execution_id

        return self._run_write(operation)

    def _terminal_execution(self, actor: str, execution_id: str, event_type: str, reason: str = "") -> None:
        if event_type not in {"TRIAL_COMPLETED", "TRIAL_FAILED", "TRIAL_CANCELLED"}:
            raise LedgerError("invalid terminal transition")
        def operation() -> None:
            self._require(actor, Capability.EXECUTION_APPEND)
            execution = self.db.execute("SELECT trial_id FROM execution_records WHERE execution_id = ?", (execution_id,)).fetchone()
            if execution is None or self._execution_status(execution_id) != "TRIAL_STARTED":
                raise LedgerError("execution must be started and non-terminal")
            self._append_event(execution["trial_id"], execution_id, event_type, actor, {"reason": reason})
        self._run_write(operation)

    def complete_execution(self, actor: str, execution_id: str) -> None:
        self._terminal_execution(actor, execution_id, "TRIAL_COMPLETED")

    def fail_execution(self, actor: str, execution_id: str, reason: str) -> None:
        self._terminal_execution(actor, execution_id, "TRIAL_FAILED", reason)

    def cancel_execution(self, actor: str, execution_id: str, reason: str) -> None:
        self._terminal_execution(actor, execution_id, "TRIAL_CANCELLED", reason)

    def _attach_reference(
        self, actor: str, trial_id: str, execution_id: str, reference_type: str, locator: str,
        content_hash: str | None, table: str, event_type: str, required_capability: Capability,
    ) -> str:
        def operation() -> str:
            self._require(actor, required_capability)
            execution = self.db.execute("SELECT trial_id FROM execution_records WHERE execution_id = ?", (execution_id,)).fetchone()
            if execution is None or execution["trial_id"] != trial_id:
                raise LedgerError("reference has unknown or mismatched execution")
            if event_type == "RESULT_ATTACHED" and self._execution_status(execution_id) != "TRIAL_COMPLETED":
                raise LedgerError("performance result requires completed execution")
            reference_id = str(self._id_factory())
            created_sequence = self._next_sequence()
            created_at = self._clock()
            self.db.execute(f"INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (reference_id, trial_id, execution_id, reference_type, locator,
                             content_hash, created_at, actor, created_sequence))
            _, sequence, _ = self._append_event(trial_id, execution_id, event_type, actor, {
                "reference_id": reference_id, "reference_type": reference_type,
                "locator": locator, "content_hash": content_hash, "trial_id": trial_id,
                "execution_id": execution_id, "created_at": created_at, "actor_id": actor,
                "created_ledger_sequence": created_sequence,
            }, occurred_at=created_at)
            if sequence != created_sequence:
                raise LedgerError("reference sequence assignment changed during transaction")
            return reference_id
        return self._run_write(operation)

    def attach_result(self, actor: str, trial_id: str, execution_id: str, reference_type: str, locator: str, content_hash: str | None = None) -> str:
        return self._attach_reference(actor, trial_id, execution_id, reference_type, locator, content_hash,
                                      "result_references", "RESULT_ATTACHED", Capability.RESULT_ATTACH)

    def attach_artifact(self, actor: str, trial_id: str, execution_id: str, reference_type: str, locator: str, content_hash: str | None = None) -> str:
        return self._attach_reference(actor, trial_id, execution_id, reference_type, locator, content_hash,
                                      "artifact_references", "ARTIFACT_ATTACHED", Capability.ARTIFACT_ATTACH)

    def record_protocol_violation(self, actor: str, reason: str, external_reference: str | None = None, content_hash: str | None = None) -> str:
        def operation() -> str:
            self._require(actor, Capability.PROTOCOL_VIOLATION_RECORD)
            violation_id = str(self._id_factory())
            created_sequence = self._next_sequence()
            occurred_at = self._clock()
            self.db.execute("INSERT INTO protocol_violations VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (violation_id, actor, occurred_at, reason, external_reference, content_hash, created_sequence))
            _, sequence, _ = self._append_event(None, None, "PROTOCOL_VIOLATION_RECORDED", actor, {
                "violation_id": violation_id, "reason": reason,
                "external_reference": external_reference, "content_hash": content_hash,
                "actor_id": actor, "occurred_at": occurred_at, "created_ledger_sequence": created_sequence,
            }, occurred_at=occurred_at)
            if sequence != created_sequence:
                raise LedgerError("violation sequence assignment changed during transaction")
            return violation_id
        return self._run_write(operation)

    def verify_global_chain(self, anchor: LedgerAnchorManifest | Mapping[str, Any] | None = None) -> bool:
        try:
            ledger_id = self._metadata("ledger_id")
            previous = GENESIS_PREVIOUS_HASH
            expected = 1
            for row in self.db.execute("SELECT * FROM trial_events ORDER BY ledger_sequence"):
                payload = parse_json_strict(row["payload_json"])
                envelope = {
                    "hash_domain_version": EVENT_HASH_DOMAIN_V1, "ledger_id": ledger_id,
                    "schema_version": SCHEMA_VERSION, "ledger_sequence": row["ledger_sequence"],
                    "previous_global_event_hash": previous, "event_type": row["event_type"],
                    "event_id": row["event_id"], "execution_id": row["execution_id"],
                    "occurred_at": row["occurred_at"], "actor_id": row["actor_id"],
                    "trial_id": row["trial_id"], "payload": payload,
                }
                if row["ledger_sequence"] != expected or row["previous_global_event_hash"] != previous or row["global_event_hash"] != event_hash(envelope):
                    return False
                expected += 1
                previous = row["global_event_hash"]
            if expected == 1 or not self._verify_lifecycle_linkage() or not self._verify_authoritative_projections():
                return False
            return anchor is None or self.verify_anchor(anchor, check_chain=False)
        except (LedgerError, sqlite3.DatabaseError, ValueError):
            return False

    def _verify_lifecycle_linkage(self) -> bool:
        """Ensure lifecycle projections cannot change without a chained event."""
        projections = (
            ("actor_status_events", "status_event_id", {"status_event_id": "status_event_id", "actor_id": "actor_id", "event_type": "event_type", "occurred_at": "occurred_at", "actor_id_by": "actor_id_by", "reason": "reason"}),
            ("capability_events", "capability_event_id", {"capability_event_id": "capability_event_id", "actor_id": "actor_id", "capability": "capability", "event_type": "event_type", "policy_version": "policy_version", "occurred_at": "occurred_at", "actor_id_by": "actor_id_by", "reason": "reason"}),
            ("family_policy_events", "policy_event_id", {"policy_event_id": "policy_event_id", "family_policy_id": "family_policy_id", "family_policy_version": "family_policy_version", "event_type": "event_type", "occurred_at": "occurred_at", "actor_id": "actor_id", "reason": "reason"}),
        )
        for table, identifier, bindings in projections:
            for row in self.db.execute(f"SELECT * FROM {table}"):
                event = self.db.execute("SELECT * FROM trial_events WHERE event_id = ?", (row["global_event_id"],)).fetchone()
                if event is None or event["event_type"] != row["event_type"]:
                    return False
                payload = parse_json_strict(event["payload_json"])
                if any(payload.get(payload_key) != row[row_key] for payload_key, row_key in bindings.items()):
                    return False
        return True

    def _verify_authoritative_projections(self) -> bool:
        """Bind every registration/execution/reference projection to its event facts."""
        events = {
            row["ledger_sequence"]: (row, parse_json_strict(row["payload_json"]))
            for row in self.db.execute("SELECT * FROM trial_events")
        }
        for row in self.db.execute("SELECT * FROM actor_identities"):
            event = self.db.execute(
                "SELECT * FROM trial_events WHERE event_id = ?", (row["global_event_id"],)
            ).fetchone()
            if event is None or event["event_type"] not in {"GENESIS", "ACTOR_REGISTERED"}:
                return False
            payload = parse_json_strict(event["payload_json"])
            identity_payload = payload.get(
                "owner_identity" if event["event_type"] == "GENESIS" else "actor_identity"
            )
            bindings = {
                "actor_id": "actor_id", "actor_type": "actor_type", "actor_version": "actor_version",
                "display_name": "display_name", "credential_binding": "credential_binding",
                "authentication_method": "authentication_method", "created_at": "created_at",
                "metadata_schema_version": "metadata_schema_version",
            }
            if (identity_payload is None or event["occurred_at"] != row["created_at"]
                    or any(identity_payload.get(key) != row[value] for key, value in bindings.items())):
                return False
        for row in self.db.execute("SELECT * FROM research_specs"):
            if hashlib.sha256(row["canonical_blob"]).hexdigest() != row["canonical_research_spec_sha256"]:
                return False
            event, payload = events.get(row["created_ledger_sequence"], (None, None))
            if event is None or event["event_type"] != "TRIAL_REGISTERED" or payload.get("research_spec_sha256") != row["canonical_research_spec_sha256"]:
                return False
        for row in self.db.execute("SELECT * FROM family_policy_specs"):
            if hashlib.sha256(row["policy_rules_blob"]).hexdigest() != row["policy_rules_hash"]:
                return False
            policy_identity = {
                "family_policy_id": row["family_policy_id"],
                "family_policy_version": row["family_policy_version"],
                "policy_schema_version": row["policy_schema_version"],
                "policy_rules_hash": row["policy_rules_hash"],
                "effective_from": row["effective_from"],
            }
            if hashlib.sha256(canonical_json_bytes(policy_identity)).hexdigest() != row["canonical_policy_hash"]:
                return False
            event = self.db.execute(
                "SELECT * FROM trial_events WHERE event_id = ?", (row["global_event_id"],)
            ).fetchone()
            if (event is None or event["event_type"] != "FAMILY_POLICY_REGISTERED"
                    or event["actor_id"] != row["registered_by"]
                    or event["occurred_at"] != row["registered_at"]):
                return False
            payload = parse_json_strict(event["payload_json"])
            if not (payload.get("family_policy_id") == row["family_policy_id"]
                    and payload.get("family_policy_version") == row["family_policy_version"]
                    and payload.get("policy_rules_hash") == row["policy_rules_hash"]
                    and payload.get("canonical_policy_hash") == row["canonical_policy_hash"]
                    and payload.get("effective_from") == row["effective_from"]):
                return False
        for row in self.db.execute("SELECT * FROM trial_registrations"):
            event, payload = events.get(row["created_ledger_sequence"], (None, None))
            bindings = {"trial_id": "trial_id", "research_spec_sha256": "canonical_research_spec_sha256", "trial_family_id": "trial_family_id", "parent_trial_id": "parent_trial_id", "trial_kind": "trial_kind", "registration_actor": "registration_actor", "registered_at": "registered_at", "schema_version": "schema_version", "family_policy_id": "family_policy_id", "family_policy_version": "family_policy_version", "frozen_replay_identity_hash": "frozen_replay_identity_hash", "created_ledger_sequence": "created_ledger_sequence"}
            if event is None or event["event_type"] != "TRIAL_REGISTERED" or any(payload.get(key) != row[value] for key, value in bindings.items()):
                return False
        for row in self.db.execute("SELECT * FROM registration_idempotency"):
            trial = self.db.execute("SELECT created_ledger_sequence FROM trial_registrations WHERE trial_id = ?", (row["trial_id"],)).fetchone()
            if trial is None:
                return False
            _, payload = events.get(trial["created_ledger_sequence"], (None, None))
            if (payload is None or payload.get("registration_actor") != row["registration_actor"]
                    or payload.get("idempotency_key") != row["idempotency_key"]
                    or payload.get("registration_request_hash") != row["request_hash"]
                    or payload.get("trial_id") != row["trial_id"]):
                return False
        checks = (
            ("execution_records", "TRIAL_STARTED", {"execution_id": "execution_id", "trial_id": "trial_id", "execution_kind": "execution_kind", "original_execution_id": "original_execution_id", "created_at": "created_at", "actor_id": "actor_id", "created_ledger_sequence": "created_ledger_sequence"}),
            ("result_references", "RESULT_ATTACHED", {"reference_id": "reference_id", "trial_id": "trial_id", "execution_id": "execution_id", "reference_type": "reference_type", "locator": "locator", "content_hash": "content_hash", "created_at": "created_at", "actor_id": "actor_id", "created_ledger_sequence": "created_ledger_sequence"}),
            ("artifact_references", "ARTIFACT_ATTACHED", {"reference_id": "reference_id", "trial_id": "trial_id", "execution_id": "execution_id", "reference_type": "reference_type", "locator": "locator", "content_hash": "content_hash", "created_at": "created_at", "actor_id": "actor_id", "created_ledger_sequence": "created_ledger_sequence"}),
            ("protocol_violations", "PROTOCOL_VIOLATION_RECORDED", {"violation_id": "violation_id", "actor_id": "actor_id", "occurred_at": "occurred_at", "reason": "reason", "external_reference": "external_reference", "content_hash": "content_hash", "created_ledger_sequence": "created_ledger_sequence"}),
        )
        for table, event_type, bindings in checks:
            for row in self.db.execute(f"SELECT * FROM {table}"):
                event, payload = events.get(row["created_ledger_sequence"], (None, None))
                if event is None or event["event_type"] != event_type or any(payload.get(key) != row[value] for key, value in bindings.items()):
                    return False
        return True

    @staticmethod
    def _anchor_parts(anchor: LedgerAnchorManifest | Mapping[str, Any]) -> tuple[dict[str, Any], str]:
        if is_dataclass(anchor):
            raw = asdict(anchor)
        else:
            raw = dict(anchor)
        return dict(raw["payload"]), str(raw["manifest_sha256"])

    def verify_anchor(self, anchor: LedgerAnchorManifest | Mapping[str, Any], *, check_chain: bool = True) -> bool:
        try:
            payload, digest = self._anchor_parts(anchor)
            if hashlib.sha256(canonicalize_anchor_payload(payload)).hexdigest() != digest:
                return False
            if payload["ledger_id"] != self._metadata("ledger_id") or payload["schema_version"] != SCHEMA_VERSION:
                return False
            anchor_sequence = int(payload["as_of_ledger_sequence"])
            current = self.db.execute("SELECT MAX(ledger_sequence) AS value FROM trial_events").fetchone()["value"]
            if current is None or int(current) < anchor_sequence:
                return False
            row = self.db.execute("SELECT global_event_hash FROM trial_events WHERE ledger_sequence = ?", (anchor_sequence,)).fetchone()
            return row is not None and row["global_event_hash"] == payload["global_event_hash"] and (not check_chain or self.verify_global_chain())
        except (KeyError, TypeError, ValueError, LedgerError, sqlite3.DatabaseError):
            return False

    def snapshot(self, *, as_of_ledger_sequence: int | None = None, anchor: LedgerAnchorManifest | Mapping[str, Any] | None = None) -> TrialHistorySnapshot:
        integrity = self.db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok" or not self.verify_global_chain(anchor):
            raise LedgerError("snapshot issuance blocked by integrity, chain, or anchor failure")
        last = self.db.execute("SELECT ledger_sequence, global_event_hash FROM trial_events ORDER BY ledger_sequence DESC LIMIT 1").fetchone()
        if last is None:
            raise LedgerError("genesis event missing")
        sequence = int(last["ledger_sequence"]) if as_of_ledger_sequence is None else as_of_ledger_sequence
        boundary = self.db.execute("SELECT global_event_hash FROM trial_events WHERE ledger_sequence = ?", (sequence,)).fetchone()
        if boundary is None:
            raise LedgerError("unknown snapshot boundary")
        events = []
        for row in self.db.execute("SELECT ledger_sequence, trial_id, execution_id, event_type, actor_id, payload_json, global_event_hash FROM trial_events WHERE ledger_sequence <= ? ORDER BY ledger_sequence", (sequence,)):
            events.append({key: (parse_json_strict(row[key]) if key == "payload_json" else row[key]) for key in row.keys()})
        trials = [dict(row) for row in self.db.execute(
            "SELECT * FROM trial_registrations WHERE created_ledger_sequence <= ? ORDER BY trial_id", (sequence,)
        )]
        evidence = {
            "snapshot_schema_version": "1", "ledger_id": self._metadata("ledger_id"),
            "schema_version": SCHEMA_VERSION, "as_of_ledger_sequence": sequence,
            "global_event_hash": boundary["global_event_hash"], "registered_attempt_count": len(trials),
            "performance_evaluated_count": self.db.execute(
                "SELECT COUNT(DISTINCT trial_id) FROM result_references WHERE created_ledger_sequence <= ?", (sequence,)
            ).fetchone()[0],
            "pre_evaluation_failure_count": sum(event["event_type"] == "TRIAL_FAILED" for event in events),
            "replay_count": self.db.execute(
                "SELECT COUNT(*) FROM execution_records WHERE execution_kind = 'REPRODUCIBILITY_REPLAY' AND created_ledger_sequence <= ?", (sequence,)
            ).fetchone()[0],
            "trial_membership": trials,
            "research_spec_hashes": [row[0] for row in self.db.execute(
                "SELECT canonical_research_spec_sha256 FROM research_specs WHERE created_ledger_sequence <= ? ORDER BY canonical_research_spec_sha256", (sequence,)
            )],
            "protocol_violations": [dict(row) for row in self.db.execute(
                "SELECT * FROM protocol_violations WHERE created_ledger_sequence <= ? ORDER BY violation_id", (sequence,)
            )],
            "result_references": [dict(row) for row in self.db.execute(
                "SELECT * FROM result_references WHERE created_ledger_sequence <= ? ORDER BY reference_id", (sequence,)
            )],
            "artifact_references": [dict(row) for row in self.db.execute(
                "SELECT * FROM artifact_references WHERE created_ledger_sequence <= ? ORDER BY reference_id", (sequence,)
            )],
            "events": events,
        }
        evidence_bytes = canonical_json_bytes(evidence)
        return TrialHistorySnapshot(evidence["ledger_id"], SCHEMA_VERSION, sequence,
                                    boundary["global_event_hash"], hashlib.sha256(evidence_bytes).hexdigest(), evidence_bytes)

    def create_anchor(self, actor: str) -> LedgerAnchorManifest:
        def operation() -> LedgerAnchorManifest:
            self._require(actor, Capability.ANCHOR_CREATE)
            snapshot = self.snapshot()
            payload = LedgerAnchorManifestPayload(
                snapshot.ledger_id, snapshot.as_of_ledger_sequence, snapshot.global_event_hash,
                snapshot.schema_version, self._clock(), actor,
            )
            payload_dict = asdict(payload)
            digest = hashlib.sha256(canonicalize_anchor_payload(payload_dict)).hexdigest()
            self.db.execute("INSERT INTO anchor_evidence VALUES (?, ?, ?, ?)",
                            (digest, canonical_json_bytes(payload_dict).decode("utf-8"), payload.created_at, actor))
            return LedgerAnchorManifest(payload, digest)
        return self._run_write(operation)

    def backup_to(self, destination: str | Path) -> None:
        with self.lock:
            target = sqlite3.connect(str(destination))
            try:
                self.db.backup(target)
            finally:
                target.close()

    @classmethod
    def verify_restored_backup(
        cls, restored_path: str | Path, expected_snapshot: TrialHistorySnapshot,
        anchor: LedgerAnchorManifest | Mapping[str, Any] | None = None,
    ) -> bool:
        restored = cls(restored_path)
        try:
            snapshot = restored.snapshot(anchor=anchor)
            return snapshot.content_hash == expected_snapshot.content_hash
        except LedgerError:
            return False
        finally:
            restored.close()
