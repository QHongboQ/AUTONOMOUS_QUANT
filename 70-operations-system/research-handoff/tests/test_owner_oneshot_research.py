"""No-paid tests for the explicit local one-shot boundary and native budgets."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
HANDOFF = ROOT / "70-operations-system/research-handoff"
SMOKE = HANDOFF / "docker-rdagent-smoke"
P4_DIR = ROOT / "40-certification-system/champion-challenger/p4-residual-thin-policy"
for directory in (str(P4_DIR), str(HANDOFF), str(SMOKE)):
    if directory not in sys.path:
        sys.path.insert(0, directory)

import aq_p4_policy as p4  # noqa: E402
import owner_oneshot_research as oneshot  # noqa: E402
import owner_bootstrap_request as bootstrap  # noqa: E402
import owner_oneshot_proxy_control as proxy_control  # noqa: E402
import docker_rdagent_target  # noqa: E402
import standing_policy  # noqa: E402
from native_experiment_budget import (  # noqa: E402
    OWNER_ONESHOT_MODELS,
    NativeExperimentBudgetController,
    P12ExperimentIdentity,
    experiment_user_id,
)
from docker_rdagent_target import (  # noqa: E402
    FINQUANT_DATA_MOUNTS,
    PINNED_FINQUANT_IMAGE,
    PINNED_FINQUANT_IMAGE_ID,
    PERSISTENT_LITELLM_NETWORK,
    validate_owner_worker_inspection,
    _owner_artifact_volume_name,
    _owner_artifact_container_command,
)
from p12_mlflow_evidence import inspect_research_evidence  # noqa: E402


def identity(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def completed_owner_evidence(return_code: int = 0):
    return {
        "target_return_code": return_code,
        "key_blocked_after_attempt": True,
        "research_evidence_status": (
            "RESEARCH_EVIDENCE_COMPLETE" if return_code == 0 else "RESEARCH_EVIDENCE_INCOMPLETE"
        ),
    }


def owner_fixture(now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    sources = (identity("real-source-a"),)
    decision = p4.challenger_needed(
        candidate_id=identity("candidate"),
        reason=p4.ChallengerReason.NO_CHAMPION,
        current_champion_state=None,
        source_evidence_identities=sources,
    )
    request = p4.build_research_request(
        challenger_decision=decision,
        asset_universe_scope_identity=identity("frozen-us-pit-scope"),
        allowed_research_families=("RD_AGENT",),
        research_budget_identity=identity("one-approved-experiment"),
        target_protocol_context="frozen-US-PIT-research-only",
        evidence_cutoff=(now.date() - timedelta(days=1)),
        request_provenance=identity("owner-approved-p4-request"),
    )
    base_policy = standing_policy.create_synthetic_test_policy(request)
    approved_policy = base_policy.model_copy(update={
        "authorization_status": "APPROVED",
        "evidence_classification": "HUMAN_APPROVED",
        "approval_source_identity": identity("owner-source"),
        "approval_record_identity": identity("owner-record"),
        "effective_at": now - timedelta(minutes=1),
        "expires_at": now + timedelta(hours=23, minutes=59),
        "revoked_at": None,
        "allowed_universe_scope_identities": (request.asset_universe_scope_identity,),
        "allowed_request_provenance_identities": (request.request_provenance,),
        "allowed_research_families": tuple(request.allowed_research_families),
        "allowed_llm_routes": (
            standing_policy.LLMRouteV1(provider="deepseek", model="deepseek/deepseek-flash", billing_class="PAID"),
            standing_policy.LLMRouteV1(provider="ollama", model="ollama/qwen3-embedding:0.6b", billing_class="LOCAL"),
        ),
        "research_budget_identity": request.research_budget_identity,
        "maximum_period_spend_usd": Decimal("5.00"),
        "maximum_run_spend_usd": Decimal("5.00"),
        "spending_reset_window_seconds": 86400,
        "spending_limit_semantics": "TRACKED_SPEND_LIMIT_ONLY",
        "maximum_concurrent_runs": 1,
        "maximum_runtime_seconds": 3600,
        "maximum_memory_mb": 4096,
        "maximum_storage_bytes": 100_000_000_000,
    })
    fields = approved_policy.model_dump(mode="json", exclude={"policy_id"})
    fields["policy_id"] = standing_policy.policy_identity(fields)
    envelope = {"p4_decision": decision.model_dump(mode="json"), "research_request": request.model_dump(mode="json")}
    return envelope, request, standing_policy.P12StandingResearchPolicyV1.model_validate(fields)


class FakeNativeAPI:
    def __init__(self):
        self.calls = []
        self.users = {}
        self.keys = []
        self.token = "sk-test-token-not-a-real-key"

    def user_info(self, user_id):
        return self.users.get(user_id)

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if path.startswith("/key/list?"):
            if self.keys:
                return 200, {"keys": list(self.keys), "total_pages": 1}
            return 200, {"keys": [], "total_pages": 0}
        if path == "/user/new":
            self.users[body["user_id"]] = {
                "user_id": body["user_id"], "user_alias": body["user_alias"],
                "max_budget": body["max_budget"], "budget_duration": body["budget_duration"],
                "models": body["models"], "max_parallel_requests": body["max_parallel_requests"],
                "spend": 0.0,
            }
            return 200, {"user_id": body["user_id"]}
        if path == "/key/generate":
            self.keys.append({
                **body,
                "key_alias": body["key_alias"],
                "expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            })
            return 200, {"key": self.token}
        if path == "/key/block":
            self.keys[-1]["blocked"] = True
            return 200, {"blocked": True}
        return 500, {}

    def key_info(self, token):
        assert token == self.token
        return dict(self.keys[-1])


class OwnerOneShotTests(unittest.TestCase):
    def bootstrap_fixture(self):
        inputs = tuple(
            bootstrap.InputIdentityV1(name=name, sha256=identity(name))
            for name in ("p2_pit_inventory", "p3_materialization_report", "rdagent_qlib_pinned_image")
        )
        request = bootstrap.build_owner_bootstrap_request(inputs)
        return {"bootstrap_request": request.model_dump(mode="json")}, request

    def test_bootstrap_contract_is_content_addressed_without_p4_claim(self):
        envelope, request = self.bootstrap_fixture()
        with patch.object(bootstrap, "verify_current_frozen_inputs"):
            origin, decision, parsed = oneshot._parse_request_envelope(envelope)
        self.assertEqual(origin, p12_origin := "OWNER_INITIAL_BOOTSTRAP")
        self.assertIsNone(decision)
        self.assertEqual(parsed.request_id, request.request_id)
        self.assertEqual(request.scope, "US/PIT")
        self.assertEqual(request.allowed_research_families, ("RD_AGENT",))
        self.assertEqual(request.trading_authority, "NONE")
        changed = dict(envelope["bootstrap_request"])
        changed["asset_universe_scope_identity"] = identity("changed-scope")
        with self.assertRaisesRegex(ValueError, "scope, budget, or provenance|request_id"):
            bootstrap.OwnerInitialBootstrapRequestV1.model_validate(changed)
        self.assertEqual(p12_origin, "OWNER_INITIAL_BOOTSTRAP")

    def test_bootstrap_request_rejects_any_fabricated_p4_payload(self):
        envelope, _ = self.bootstrap_fixture()
        envelope["p4_decision"] = {"evidence_classification": "REAL_EXTERNAL_EVIDENCE"}
        with self.assertRaisesRegex(ValueError, "must not contain P4"):
            bootstrap.validate_owner_bootstrap_envelope(envelope)

    def test_bootstrap_p12_claim_records_origin_and_replay_does_not_dispatch(self):
        envelope, request = self.bootstrap_fixture()
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "canonical"
            with patch.object(oneshot.p12, "OWNER_BOOTSTRAP_STATE_DIR", state), patch.object(
                bootstrap, "verify_current_frozen_inputs"
            ):
                result, code = oneshot.p12.process_owner_oneshot(
                    envelope, state_dir=state, policy_id=identity("approved-bootstrap-policy"),
                    owner_confirmed=True,
                    target=lambda _: calls.append("dispatch") or {
                        **completed_owner_evidence(), "worker_identity_verified": True,
                    },
                )
                replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                    envelope, state_dir=state, policy_id=identity("approved-bootstrap-policy"),
                )
            self.assertEqual(code, 0)
            self.assertEqual(result["dispatch_count_added"], 1)
            self.assertEqual(replay[1], 0)
            self.assertEqual(replay[0]["dispatch_count_added"], 0)
            for marker in (oneshot.p12._claim_file(state, request.request_id),
                           oneshot.p12._dispatch_file(state, request.request_id),
                           oneshot.p12._status_file(state, request.request_id)):
                self.assertEqual(oneshot.p12._read_json_nofollow(marker)["request_origin"], "OWNER_INITIAL_BOOTSTRAP")
        self.assertEqual(calls, ["dispatch"])

    def test_legacy_p4_owner_success_and_failure_replay_without_redispatch(self):
        for return_code, expected_code, expected_state in (
            (0, 0, "SUCCEEDED_OWNER_ONESHOT"),
            (1, oneshot.p12._EXIT_FAILED, "FAILED_OWNER_ONESHOT"),
        ):
            with self.subTest(return_code=return_code):
                envelope, request, policy = owner_fixture()
                calls = []
                with tempfile.TemporaryDirectory() as tmp:
                    state = Path(tmp)
                    first, first_code = oneshot.p12.process_owner_oneshot(
                        envelope, state_dir=state, policy_id=policy.policy_id, owner_confirmed=True,
                        target=lambda _: calls.append("dispatch") or completed_owner_evidence(return_code),
                    )
                    self.assertEqual(first_code, expected_code)
                    self.assertEqual(first["classification"], expected_state)
                    for marker in (
                        oneshot.p12._claim_file(state, request.request_id),
                        oneshot.p12._dispatch_file(state, request.request_id),
                        oneshot.p12._status_file(state, request.request_id),
                    ):
                        record = json.loads(marker.read_text())
                        record.pop("request_origin")
                        marker.write_text(json.dumps(record))
                    replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                        envelope, state_dir=state, policy_id=policy.policy_id,
                    )
                self.assertEqual(replay[1], expected_code)
                self.assertEqual(replay[0]["classification"], expected_state)
                self.assertEqual(replay[0]["dispatch_count_added"], 0)
                self.assertEqual(calls, ["dispatch"])

    def test_mixed_owner_origin_markers_fail_closed(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            calls = []
            oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id, owner_confirmed=True,
                target=lambda _: calls.append("dispatch") or completed_owner_evidence(),
            )
            claim_path = oneshot.p12._claim_file(state, request.request_id)
            claim = json.loads(claim_path.read_text())
            claim.pop("request_origin")
            claim_path.write_text(json.dumps(claim))
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertNotEqual(replay[1], 0)
        self.assertIn("IDENTITY_COLLISION", replay[0]["classification"])
        self.assertEqual(calls, ["dispatch"])

    def test_bootstrap_legacy_origin_is_never_accepted(self):
        envelope, request = self.bootstrap_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "canonical"
            with patch.object(oneshot.p12, "OWNER_BOOTSTRAP_STATE_DIR", state), patch.object(
                bootstrap, "verify_current_frozen_inputs"
            ):
                oneshot.p12.process_owner_oneshot(
                    envelope, state_dir=state, policy_id=identity("approved-bootstrap-policy"),
                    owner_confirmed=True,
                    target=lambda _: completed_owner_evidence(),
                )
                for marker in (
                    oneshot.p12._claim_file(state, request.request_id),
                    oneshot.p12._dispatch_file(state, request.request_id),
                    oneshot.p12._status_file(state, request.request_id),
                ):
                    record = json.loads(marker.read_text())
                    record.pop("request_origin")
                    marker.write_text(json.dumps(record))
                replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                    envelope, state_dir=state, policy_id=identity("approved-bootstrap-policy"),
                )
        self.assertNotEqual(replay[1], 0)
        self.assertIn("IDENTITY_COLLISION", replay[0]["classification"])
        self.assertEqual(replay[0]["dispatch_count_added"], 0)

    def test_interrupted_bootstrap_claim_blocks_restart_without_second_dispatch(self):
        envelope, request = self.bootstrap_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "canonical"
            with patch.object(oneshot.p12, "OWNER_BOOTSTRAP_STATE_DIR", state), patch.object(
                bootstrap, "verify_current_frozen_inputs"
            ):
                state.mkdir()
                oneshot.p12._durable_json_create(
                    oneshot.p12._claim_file(state, request.request_id),
                    {"request_id": request.request_id, "request_origin": "OWNER_INITIAL_BOOTSTRAP", "state": "CLAIMED_OWNER_ONESHOT"},
                )
                replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                    envelope, state_dir=state, policy_id=identity("approved-bootstrap-policy"),
                )
                restarted, code = oneshot.p12.process_owner_oneshot(
                    envelope, state_dir=state, policy_id=identity("approved-bootstrap-policy"), owner_confirmed=True,
                    target=lambda _: self.fail("interrupted bootstrap must never be retried"),
                )
        self.assertNotEqual(replay[1], 0)
        self.assertNotEqual(code, 0)
        self.assertIn("BLOCKED_OWNER_ONESHOT", replay[0]["classification"])
        self.assertIn("BLOCKED_OWNER_ONESHOT", restarted["classification"])

    def test_bootstrap_cannot_use_arbitrary_state_or_allocate_second_experiment(self):
        envelope, _ = self.bootstrap_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            canonical = Path(tmp) / "canonical"
            arbitrary = Path(tmp) / "alternate"
            with patch.object(oneshot.p12, "OWNER_BOOTSTRAP_STATE_DIR", canonical), patch.object(
                bootstrap, "verify_current_frozen_inputs"
            ):
                denied, code = oneshot.p12.process_owner_oneshot(
                    envelope, state_dir=arbitrary, policy_id=identity("policy-a"), owner_confirmed=True,
                    target=lambda _: self.fail("noncanonical bootstrap must not dispatch"),
                )
                self.assertNotEqual(code, 0)
                self.assertEqual(denied["classification"], "DENIED_OWNER_BOOTSTRAP_REQUEST_IDENTITY")
                accepted, code = oneshot.p12.process_owner_oneshot(
                    envelope, state_dir=canonical, policy_id=identity("policy-a"), owner_confirmed=True,
                    target=lambda _: completed_owner_evidence(),
                )
                other, _ = self.bootstrap_fixture_with_suffix("other")
                denied_again, code_again = oneshot.p12.process_owner_oneshot(
                    other, state_dir=canonical, policy_id=identity("policy-b"), owner_confirmed=True,
                    target=lambda _: self.fail("second bootstrap allocation must not dispatch"),
                )
        self.assertEqual(code, 0)
        self.assertNotEqual(code_again, 0)
        self.assertEqual(denied_again["classification"], "BLOCKED_OWNER_BOOTSTRAP_ALREADY_ALLOCATED")

    def bootstrap_fixture_with_suffix(self, suffix: str):
        inputs = tuple(
            bootstrap.InputIdentityV1(name=name, sha256=identity(name + suffix))
            for name in ("p2_pit_inventory", "p3_materialization_report", "rdagent_qlib_pinned_image")
        )
        request = bootstrap.build_owner_bootstrap_request(inputs)
        return {"bootstrap_request": request.model_dump(mode="json")}, request

    def test_no_tty_confirmation_creates_no_bootstrap_policy_or_claim(self):
        envelope, request = self.bootstrap_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "canonical"
            request_path = Path(tmp) / "request.json"
            request_path.write_text(json.dumps(envelope))
            with patch.object(oneshot.p12, "OWNER_BOOTSTRAP_STATE_DIR", state), patch.object(
                bootstrap, "verify_current_frozen_inputs"
            ), patch.object(oneshot, "_preflight", return_value={"classification": "PASS"}), patch.object(
                oneshot, "_new_provider_secret_path", return_value=Path(tmp) / "provider.secret"
            ), patch.object(oneshot.sys.stdin, "isatty", return_value=False):
                result, code = oneshot.run_one_shot(
                    request_path, None, state, Path(tmp) / "runtime", Path(tmp) / "compose.env",
                    Path(tmp) / "provider.secret",
                )
            self.assertNotEqual(code, 0)
            self.assertEqual(result["classification"], "DENIED_INTERACTIVE_OWNER_TTY_REQUIRED")
            self.assertFalse(state.exists())
            self.assertFalse((state / oneshot.BOOTSTRAP_POLICY_NAME).exists())
            self.assertFalse((state / "owner-initial-bootstrap-allocation.json").exists())

    def test_bootstrap_policy_materializes_only_after_exact_request_confirmation(self):
        _, request = self.bootstrap_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "canonical"
            state.mkdir()
            with patch.object(oneshot.p12, "OWNER_BOOTSTRAP_STATE_DIR", state):
                with self.assertRaisesRegex(ValueError, "CONFIRMATION_MISMATCH"):
                    oneshot._materialize_bootstrap_policy_after_confirmation(
                        request, state_dir=state, confirmation="yes",
                    )
                self.assertFalse((state / oneshot.BOOTSTRAP_POLICY_NAME).exists())
                phrase = f"AUTHORIZE INITIAL $5 RUN {request.request_id}"
                policy = oneshot._materialize_bootstrap_policy_after_confirmation(
                    request, state_dir=state, confirmation=phrase,
                    now=datetime(2026, 10, 18, tzinfo=timezone.utc),
                )
            self.assertEqual(policy.evidence_classification, "HUMAN_APPROVED")
            self.assertEqual(policy.research_budget_identity, request.research_budget_identity)
            self.assertEqual(policy.maximum_period_spend_usd, Decimal("5.00"))
            self.assertEqual(policy.expires_at - policy.effective_at, timedelta(hours=24))

    def test_p4_terminal_claim_cannot_replay_as_bootstrap_origin(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id, owner_confirmed=True,
                target=lambda _: completed_owner_evidence(),
            )
            claim_path = oneshot.p12._claim_file(state, request.request_id)
            claim = json.loads(claim_path.read_text())
            claim["request_origin"] = "OWNER_INITIAL_BOOTSTRAP"
            claim_path.write_text(json.dumps(claim))
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertNotEqual(replay[1], 0)
        self.assertIn("IDENTITY_COLLISION", replay[0]["classification"])

    def test_real_p4_request_and_exact_expiring_policy_validate(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "request.json"
            policy_path = Path(tmp) / "policy.json"
            request_path.write_text(json.dumps(envelope))
            policy_path.write_text(policy.model_dump_json())
            checked = oneshot._validate_inputs(request_path, policy_path)
        self.assertEqual(checked[2].request_id, request.request_id)
        self.assertEqual(checked[3].maximum_period_spend_usd, 5)

    def test_synthetic_p4_fixtures_are_rejected(self):
        envelope, request, policy = owner_fixture()
        envelope["p4_decision"]["evidence_classification"] = "TEST_FIXTURE_NOT_REAL_EVIDENCE"
        with tempfile.TemporaryDirectory() as tmp:
            request_path, policy_path = Path(tmp) / "request.json", Path(tmp) / "policy.json"
            request_path.write_text(json.dumps(envelope))
            policy_path.write_text(policy.model_dump_json())
            with self.assertRaisesRegex(ValueError, "synthetic"):
                oneshot._validate_inputs(request_path, policy_path)

    def test_changed_provider_budget_expiry_or_revocation_is_denied(self):
        for change in (
            {"maximum_period_spend_usd": "5.01"},
            {"maximum_run_spend_usd": "4.99"},
            {"revoked_at": datetime.now(timezone.utc).isoformat()},
            {"expires_at": (datetime.now(timezone.utc) + timedelta(hours=25)).isoformat()},
        ):
            envelope, _, policy = owner_fixture()
            values = policy.model_dump(mode="json")
            values.update(change)
            values["policy_id"] = standing_policy.policy_identity({k: v for k, v in values.items() if k != "policy_id"})
            with tempfile.TemporaryDirectory() as tmp:
                request_path, policy_path = Path(tmp) / "request.json", Path(tmp) / "policy.json"
                request_path.write_text(json.dumps(envelope))
                policy_path.write_text(json.dumps(values))
                with self.assertRaises(ValueError):
                    oneshot._validate_inputs(request_path, policy_path)

    def test_native_user_and_key_are_same_stable_experiment_with_no_reset(self):
        _, request, policy = owner_fixture()
        identity_value = P12ExperimentIdentity.from_p12(request, policy)
        api = FakeNativeAPI()
        token, user, key = NativeExperimentBudgetController(api).prepare_owner_oneshot(
            identity_value, owner_activation_confirmed=True
        )
        self.assertEqual(token, api.token)
        self.assertEqual(user["user_id"], experiment_user_id(request.research_budget_identity))
        self.assertEqual(key["user_id"], user["user_id"])
        self.assertEqual(user["max_budget"], 5.0)
        self.assertIsNone(user["budget_duration"])
        self.assertEqual(key["max_budget"], 5.0)
        self.assertIsNone(key["budget_duration"])
        self.assertEqual(key["max_parallel_requests"], 1)
        self.assertEqual(key["models"], list(OWNER_ONESHOT_MODELS))
        self.assertEqual(sum(call[1] == "/user/new" for call in api.calls), 1)
        self.assertEqual(sum(call[1] == "/key/generate" for call in api.calls), 1)

    def test_no_activation_spend_history_alias_change_or_prior_key_denies(self):
        _, request, policy = owner_fixture()
        identity_value = P12ExperimentIdentity.from_p12(request, policy)
        no_activation = FakeNativeAPI()
        with self.assertRaisesRegex(Exception, "DENIED_INTERACTIVE_OWNER_ACTIVATION_REQUIRED"):
            NativeExperimentBudgetController(no_activation).prepare_owner_oneshot(
                identity_value, owner_activation_confirmed=False
            )
        self.assertEqual(no_activation.calls, [])

        spent = FakeNativeAPI()
        NativeExperimentBudgetController(spent).prepare_owner_oneshot(identity_value, owner_activation_confirmed=True)
        spent.users[identity_value.user_id]["spend"] = 0.01
        with self.assertRaisesRegex(Exception, "SCOPE_OR_SPEND_MISMATCH"):
            NativeExperimentBudgetController(spent).prepare_owner_oneshot(identity_value, owner_activation_confirmed=True)
        self.assertEqual(sum(call[1] == "/key/generate" for call in spent.calls), 1)

        prior_key = FakeNativeAPI()
        NativeExperimentBudgetController(prior_key).prepare_owner_oneshot(identity_value, owner_activation_confirmed=True)
        with self.assertRaisesRegex(Exception, "KEY_ALREADY_ISSUED"):
            NativeExperimentBudgetController(prior_key).prepare_owner_oneshot(identity_value, owner_activation_confirmed=True)
        self.assertEqual(sum(call[1] == "/key/generate" for call in prior_key.calls), 1)

    def test_native_key_that_fails_scope_verification_is_blocked(self):
        _, request, policy = owner_fixture()
        identity_value = P12ExperimentIdentity.from_p12(request, policy)
        api = FakeNativeAPI()
        original_key_info = api.key_info

        def wrong_scope(token):
            value = original_key_info(token)
            value["models"] = ["another-model"]
            return value

        api.key_info = wrong_scope
        with self.assertRaisesRegex(Exception, "DENIED_OWNER_NATIVE_KEY_SCOPE_MISMATCH"):
            NativeExperimentBudgetController(api).prepare_owner_oneshot(
                identity_value, owner_activation_confirmed=True
            )
        self.assertTrue(api.keys[-1]["blocked"])
        self.assertEqual(sum(call[1] == "/key/generate" for call in api.calls), 1)
        self.assertEqual(sum(call[1] == "/key/block" for call in api.calls), 1)

    def test_experiment_identity_cannot_be_rebound_to_another_request(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            result, code = oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state_dir, policy_id=policy.policy_id,
                owner_confirmed=True,
                target=lambda _: completed_owner_evidence(),
            )
            self.assertEqual(code, 0)
            sources = (identity("different-real-source"),)
            changed_decision = p4.challenger_needed(
                candidate_id=identity("different-candidate"),
                reason=p4.ChallengerReason.NO_CHAMPION,
                current_champion_state=None,
                source_evidence_identities=sources,
            )
            changed_request = p4.build_research_request(
                challenger_decision=changed_decision,
                asset_universe_scope_identity=request.asset_universe_scope_identity,
                allowed_research_families=tuple(request.allowed_research_families),
                research_budget_identity=request.research_budget_identity,
                target_protocol_context="same-US-PIT-scope",
                evidence_cutoff=request.evidence_cutoff,
                request_provenance=identity("different-provenance"),
            )
            changed_envelope = {
                "p4_decision": changed_decision.model_dump(mode="json"),
                "research_request": changed_request.model_dump(mode="json"),
            }
            result, code = oneshot.p12.process_owner_oneshot(
                changed_envelope, state_dir=state_dir, policy_id=policy.policy_id,
                owner_confirmed=True,
                target=lambda _: self.fail("rebound experiment must not dispatch"),
            )
        self.assertNotEqual(code, 0)
        self.assertIn("EXPERIMENT_REBOUND", result["classification"])

    def test_cli_requires_tty_and_exact_interactive_owner_phrase(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            request_path, policy_path = Path(tmp) / "request.json", Path(tmp) / "policy.json"
            request_path.write_text(json.dumps(envelope))
            policy_path.write_text(policy.model_dump_json())
            with patch.object(oneshot, "_preflight", return_value={"classification": "PASS"}):
                with patch.object(oneshot, "_new_provider_secret_path", return_value=Path(tmp) / "new-secret"):
                    with patch.object(oneshot.sys.stdin, "isatty", return_value=False):
                        result, code = oneshot.run_one_shot(
                            request_path, policy_path, Path(tmp) / "state", Path(tmp) / "runtime",
                            Path(tmp) / "compose.env", Path(tmp) / "new-secret",
                        )
        self.assertNotEqual(code, 0)
        self.assertEqual(result["classification"], "DENIED_INTERACTIVE_OWNER_TTY_REQUIRED")

    def test_owner_terminal_replay_never_dispatches_again(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            result, code = oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id,
                owner_confirmed=True,
                target=lambda _: {**completed_owner_evidence(), "worker_identity_verified": True},
            )
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["dispatch_count_added"], 1)
        self.assertEqual(replay[1], 0)
        self.assertEqual(replay[0]["dispatch_count_added"], 0)

    def test_owner_artifact_inspection_command_binds_request_and_attempt(self):
        request_id, attempt_id = identity("artifact-command-request"), "d1feb58c-7b86-41f1-8eef-7bd54b1bffd1"
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with patch.object(docker_rdagent_target.subprocess, "run", return_value=completed) as run:
            observed = _owner_artifact_container_command(
                output=Path("/tmp/attempt-output"), volume="aq-p12-owner-artifacts-0123456789abcdef",
                tracking_uri="sqlite:////workspace/runs/run/mlflow.db", helper="p12_mlflow_evidence.py",
                prepare=False, request_id=request_id, attempt_id=attempt_id,
            )
        self.assertIs(observed, completed)
        argv = run.call_args.args[0]
        self.assertIn("--request-id", argv)
        self.assertEqual(argv[argv.index("--request-id") + 1], request_id)
        self.assertEqual(argv[argv.index("--attempt-id") + 1], attempt_id)

    def test_new_terminal_binds_immutable_litellm_evidence_and_replay_verifies_hash(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "output"
            state = Path(tmp) / "state"

            def target(attempt_id):
                output = root / request.request_id.removeprefix("sha256:") / attempt_id
                output.mkdir(parents=True)
                payload = {
                    "format_version": "P12_LITELLM_CALL_EVIDENCE_V1",
                    "request_id": request.request_id,
                    "attempt_id": attempt_id,
                    "evidence_status": "PARTIAL",
                    "calls": [],
                    "missing_fields": ["synthetic_fixture"],
                }
                (output / "p12-litellm-call-evidence.json").write_text(json.dumps(payload))
                return completed_owner_evidence()

            with patch.object(oneshot.p12, "OWNER_FINQUANT_OUTPUT_ROOT", root):
                result, code = oneshot.p12.process_owner_oneshot(
                    envelope, state_dir=state, policy_id=policy.policy_id,
                    owner_confirmed=True, target=target,
                )
                terminal = oneshot.p12._read_json_nofollow(oneshot.p12._status_file(state, request.request_id))
                replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                    envelope, state_dir=state, policy_id=policy.policy_id,
                )
                self.assertEqual(terminal["llm_provenance_evidence_status"], "PARTIAL")
                self.assertEqual(len(terminal["llm_provenance_evidence_sha256"]), 64)
                self.assertEqual(replay[0]["dispatch_count_added"], 0)
                evidence_path = root / terminal["llm_provenance_evidence_path"]
                evidence_path.write_text("tampered")
                tampered_replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                    envelope, state_dir=state, policy_id=policy.policy_id,
                )
        self.assertEqual(code, 0)
        self.assertEqual(result["dispatch_count_added"], 1)
        self.assertEqual(tampered_replay[0]["classification"], "BLOCKED_OWNER_ONESHOT_LITELLM_EVIDENCE_MISMATCH")
        self.assertEqual(tampered_replay[0]["dispatch_count_added"], 0)

    def test_terminal_without_evidence_is_explicit_partial_and_old_terminal_replay_stays_safe(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            oneshot.p12, "OWNER_FINQUANT_OUTPUT_ROOT", Path(tmp) / "output"
        ):
            state = Path(tmp) / "state"
            result, _ = oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id,
                owner_confirmed=True, target=lambda _: completed_owner_evidence(),
            )
            self.assertEqual(result["status"]["llm_provenance_evidence_status"], "PARTIAL")
            self.assertIsNone(result["status"]["llm_provenance_evidence_path"])
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertEqual(replay[0]["dispatch_count_added"], 0)

    def test_complete_native_evidence_is_bound_only_to_matching_p12_user_and_attempt(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "output"
            state = Path(tmp) / "state"
            def target(attempt_id):
                output = root / request.request_id.removeprefix("sha256:") / attempt_id
                output.mkdir(parents=True)
                payload = {
                    "format_version": "P12_LITELLM_CALL_EVIDENCE_V1",
                    "request_id": request.request_id,
                    "attempt_id": attempt_id,
                    "native_experiment_user_id": oneshot.p12.experiment_user_id(request.research_budget_identity),
                    "scoped_key_identity": identity("scoped-key"),
                    "proxy_config_sha256": hashlib.sha256(
                        (oneshot.p12.REPO_ROOT / "70-operations-system/research-handoff/docker-rdagent-smoke/config.deepseek-staging.yaml").read_bytes()
                    ).hexdigest(),
                    "litellm_proxy_version": "1.105.1",
                    "litellm_proxy_image": oneshot.p12.OWNER_LITELLM_PROXY_IMAGE,
                    "configured_allowed_models": list(proxy_control.OWNER_ONESHOT_MODELS),
                    "calls": [{
                        "spend_log_request_id": "native-row-1", "litellm_call_id": "native-call-1",
                        "attempted_fallbacks": 0, "attempted_retries": 0,
                        "status": "success", "call_type": "completion",
                        "routed_model_group": "deepseek/deepseek-flash",
                        "provider_model_identity_kind": "UNAVAILABLE",
                        "prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5,
                        "spend_usd": "0.25",
                    }], "call_count": 1,
                    "total_spend_usd": "0.25", "spend_logs_total_usd": "0.25",
                    "missing_fields": [], "evidence_status": "COMPLETE",
                }
                (output / "p12-litellm-call-evidence.json").write_text(json.dumps(payload))
                return completed_owner_evidence()
            with patch.object(oneshot.p12, "OWNER_FINQUANT_OUTPUT_ROOT", root):
                result, _ = oneshot.p12.process_owner_oneshot(
                    envelope, state_dir=state, policy_id=policy.policy_id,
                    owner_confirmed=True, target=target,
                )
            self.assertEqual(result["status"]["llm_provenance_evidence_status"], "COMPLETE")
            payload_path = root / result["status"]["llm_provenance_evidence_path"]
            value = json.loads(payload_path.read_text())
            value["native_experiment_user_id"] = "foreign-user"
            payload_path.write_text(json.dumps(value))
            with patch.object(oneshot.p12, "OWNER_FINQUANT_OUTPUT_ROOT", root):
                replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                    envelope, state_dir=state, policy_id=policy.policy_id,
                )
        self.assertEqual(replay[0]["classification"], "BLOCKED_OWNER_ONESHOT_LITELLM_EVIDENCE_MISMATCH")
        self.assertEqual(replay[0]["dispatch_count_added"], 0)

    def test_spendlog_projection_redacts_payload_and_preserves_fallback_unknown(self):
        now = datetime.now(timezone.utc)
        request_id = identity("litellm-request")
        attempt_id = "d1feb58c-7b86-41f1-8eef-7bd54b1bffd1"
        budget_id = identity("litellm-budget")
        user_id = oneshot.p12.experiment_user_id(budget_id)
        key_hash = "native-hash-only-for-fixture"
        class SpendAPI:
            def __init__(self, row):
                self.row = row
                self.key = {"user_id": user_id, "key_alias": "aq-p12-owner-once-" + hashlib.sha256((request_id + ":key").encode()).hexdigest()[:20], "blocked": True, "spend": 0.25, "models": list(proxy_control.OWNER_ONESHOT_MODELS)}
                self.pages = 0
            def key_info(self, token):
                return dict(self.key)
            def user_info(self, value):
                return {"user_id": value}
            def spend_logs_v2(self, **kwargs):
                self.pages += 1
                return {"data": [self.row], "total": 1, "total_pages": 1}
        row = {
            "request_id": "native-row-1", "litellm_call_id": "call-1", "user": user_id,
            "api_key": key_hash, "startTime": now.isoformat(), "status": "success",
            "model_group": "deepseek/deepseek-flash", "model": "deepseek/deepseek-flash",
            "call_type": "completion", "spend": 0.25, "prompt_tokens": 10,
            "completion_tokens": 4, "total_tokens": 14,
            "metadata": {"attempted_fallbacks": None, "attempted_retries": 0,
                         "messages": "DO_NOT_PERSIST", "response": "DO_NOT_PERSIST"},
        }
        api = SpendAPI(row)
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.yaml"
            config.write_text("synthetic config")
            with patch.object(proxy_control, "_native_key_hash", return_value=key_hash), patch.object(
                proxy_control, "PROXY_CONFIG_PATH", config
            ):
                evidence = proxy_control.collect_call_evidence(
                    api, token="sk-fixture", request_id=request_id, attempt_id=attempt_id,
                    research_budget_identity=budget_id, attempt_started_at_utc=(now - timedelta(seconds=1)).isoformat(),
                    now=lambda: now + timedelta(seconds=1), sleep=lambda _: None,
                )
        self.assertEqual(evidence["evidence_status"], "PARTIAL")
        self.assertEqual(evidence["calls"][0]["attempted_fallbacks"], "UNKNOWN")
        self.assertNotIn("DO_NOT_PERSIST", json.dumps(evidence))
        self.assertNotIn(key_hash, json.dumps(evidence))

    def test_spendlog_rejects_foreign_key_user_duplicate_ids_and_spend_mismatch(self):
        now = datetime.now(timezone.utc)
        user = identity("expected-user")
        base = {
            "request_id": "row", "litellm_call_id": "call", "user": user, "api_key": "hash",
            "startTime": now.isoformat(), "status": "success", "model_group": "routed",
            "spend": 1, "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2,
            "metadata": {"attempted_fallbacks": 0, "attempted_retries": 0},
        }
        args = {"expected_user": user, "expected_key_hash": "hash", "started_at": now - timedelta(seconds=1), "ended_at": now + timedelta(seconds=1)}
        self.assertEqual(proxy_control._safe_row(base, **args)["attempted_fallbacks"], 0)
        for changed in ({**base, "user": "foreign"}, {**base, "api_key": "foreign"},
                        {**base, "litellm_call_id": None}):
            with self.subTest(changed=changed.get("user", changed.get("api_key", "missing"))):
                with self.assertRaises(ValueError):
                    proxy_control._safe_row(changed, **args)
        class DuplicateAPI:
            def spend_logs_v2(self, **kwargs):
                return {"data": [base, {**base, "request_id": "row-2"}], "total": 2, "total_pages": 1}
        with self.assertRaisesRegex(ValueError, "duplicate native call identity"):
            proxy_control._spend_snapshot(
                DuplicateAPI(), user_id=user, key_hash="hash",
                started_at=now - timedelta(seconds=1), ended_at=now + timedelta(seconds=1),
            )
        with self.assertRaisesRegex(ValueError, "metadata ownership"):
            proxy_control._safe_row({**base, "metadata": {
                "attempted_fallbacks": 0, "attempted_retries": 0,
                "user_api_key_user_id": "attacker-controlled-user",
            }}, **args)

    def test_native_fallback_positive_is_preserved_and_spend_total_mismatch_is_partial(self):
        now = datetime.now(timezone.utc)
        request_id, attempt_id, budget_id = identity("fallback-request"), "d1feb58c-7b86-41f1-8eef-7bd54b1bffd1", identity("fallback-budget")
        user_id = oneshot.p12.experiment_user_id(budget_id)
        key_hash = "fixture-native-hash"
        row = {
            "request_id": "row", "litellm_call_id": "call", "user": user_id, "api_key": key_hash,
            "startTime": now.isoformat(), "status": "failure", "model_group": "deepseek/deepseek-flash",
            "model": "proxy-routed-model", "call_type": "completion", "spend": 0.25,
            "prompt_tokens": 2, "completion_tokens": 0, "total_tokens": 2,
            "metadata": {"attempted_fallbacks": 1, "original_model_group": "deepseek/deepseek-flash", "attempted_retries": 0},
        }
        class SpendAPI:
            def __init__(self, key_spend): self.key_spend = key_spend
            def key_info(self, token):
                return {"user_id": user_id, "key_alias": "aq-p12-owner-once-" + hashlib.sha256((request_id + ":key").encode()).hexdigest()[:20], "blocked": True, "spend": self.key_spend, "models": list(proxy_control.OWNER_ONESHOT_MODELS)}
            def user_info(self, value): return {"user_id": value}
            def spend_logs_v2(self, **kwargs): return {"data": [row], "total": 1, "total_pages": 1}
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.yaml"
            config.write_text("synthetic")
            with patch.object(proxy_control, "_native_key_hash", return_value=key_hash), patch.object(proxy_control, "PROXY_CONFIG_PATH", config):
                complete = proxy_control.collect_call_evidence(
                    SpendAPI(0.25), token="sk-fixture", request_id=request_id, attempt_id=attempt_id,
                    research_budget_identity=budget_id, attempt_started_at_utc=(now - timedelta(seconds=1)).isoformat(),
                    now=lambda: now + timedelta(seconds=1), sleep=lambda _: None,
                )
                mismatch = proxy_control.collect_call_evidence(
                    SpendAPI(0.26), token="sk-fixture", request_id=request_id, attempt_id=attempt_id,
                    research_budget_identity=budget_id, attempt_started_at_utc=(now - timedelta(seconds=1)).isoformat(),
                    now=lambda: now + timedelta(seconds=1), sleep=lambda _: None,
                )
        self.assertEqual(complete["evidence_status"], "COMPLETE")
        self.assertEqual(complete["calls"][0]["attempted_fallbacks"], 1)
        self.assertEqual(complete["calls"][0]["provider_model_identity_kind"], "UNAVAILABLE")
        self.assertEqual(complete["calls"][0]["proxy_model_field"], "proxy-routed-model")
        self.assertEqual(mismatch["evidence_status"], "PARTIAL")
        self.assertIn("spend_logs_not_settled_or_totals_mismatch", mismatch["missing_fields"])

    def test_delayed_spendlog_settlement_is_bounded_and_waits_for_stable_rows(self):
        now = datetime.now(timezone.utc)
        request_id, attempt_id, budget_id = identity("delayed-request"), "d1feb58c-7b86-41f1-8eef-7bd54b1bffd1", identity("delayed-budget")
        user_id = oneshot.p12.experiment_user_id(budget_id)
        key_hash = "delayed-native-hash"
        row = {
            "request_id": "delayed-row", "litellm_call_id": "delayed-call", "user": user_id,
            "api_key": key_hash, "startTime": now.isoformat(), "status": "success",
            "model_group": "deepseek/deepseek-flash", "call_type": "completion", "spend": 0.125,
            "prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5,
            "metadata": {"attempted_fallbacks": 0, "attempted_retries": 0},
        }
        class DelayedAPI:
            def __init__(self): self.polls = 0
            def key_info(self, token):
                return {"user_id": user_id, "key_alias": "aq-p12-owner-once-" + hashlib.sha256((request_id + ":key").encode()).hexdigest()[:20], "blocked": True, "spend": 0.125, "models": list(proxy_control.OWNER_ONESHOT_MODELS)}
            def user_info(self, value): return {"user_id": value}
            def spend_logs_v2(self, **kwargs):
                self.polls += 1
                rows = [] if self.polls == 1 else [row]
                return {"data": rows, "total": len(rows), "total_pages": 1 if rows else 0}
        api = DelayedAPI()
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.yaml"
            config.write_text("synthetic")
            with patch.object(proxy_control, "_native_key_hash", return_value=key_hash), patch.object(proxy_control, "PROXY_CONFIG_PATH", config):
                result = proxy_control.collect_call_evidence(
                    api, token="sk-fixture", request_id=request_id, attempt_id=attempt_id,
                    research_budget_identity=budget_id, attempt_started_at_utc=(now - timedelta(seconds=1)).isoformat(),
                    now=lambda: now + timedelta(seconds=1), sleep=lambda _: None,
                )
        self.assertEqual(result["evidence_status"], "COMPLETE")
        self.assertEqual(result["call_count"], 1)
        self.assertGreaterEqual(api.polls, 3)
        self.assertLessEqual(api.polls, proxy_control.MAX_SETTLEMENT_POLLS)

    def test_empty_zero_spend_ledger_is_partial_not_false_complete(self):
        request_id, budget_id = identity("empty-ledger-request"), identity("empty-ledger-budget")
        user_id = oneshot.p12.experiment_user_id(budget_id)
        class EmptyAPI:
            timeout = 10
            def __init__(self): self.polls = 0
            def key_info(self, token):
                return {"user_id": user_id, "key_alias": "aq-p12-owner-once-" + hashlib.sha256((request_id + ":key").encode()).hexdigest()[:20], "blocked": True, "spend": 0, "models": list(proxy_control.OWNER_ONESHOT_MODELS)}
            def user_info(self, value): return {"user_id": value}
            def spend_logs_v2(self, **kwargs):
                self.polls += 1
                return {"data": [], "total": 0, "total_pages": 0}
        api = EmptyAPI()
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.yaml"
            config.write_text("synthetic")
            with patch.object(proxy_control, "_native_key_hash", return_value="empty-fixture-hash"), patch.object(
                proxy_control, "PROXY_CONFIG_PATH", config
            ):
                result = proxy_control.collect_call_evidence(
                    api, token="sk-fixture", request_id=request_id, attempt_id="d1feb58c-7b86-41f1-8eef-7bd54b1bffd1",
                    research_budget_identity=budget_id, attempt_started_at_utc=datetime.now(timezone.utc).isoformat(),
                    now=lambda: datetime.now(timezone.utc), sleep=lambda _: None,
                )
        self.assertEqual(result["evidence_status"], "PARTIAL")
        self.assertIn("no_native_call_rows_to_seal", result["missing_fields"])

    def test_legacy_owner_terminal_replay_is_not_verified_and_never_redispatches(self):
        envelope, request, policy = owner_fixture()
        dispatches = []
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id,
                owner_confirmed=True,
                target=lambda _: (dispatches.append("dispatch") or completed_owner_evidence()),
            )
            status_path = oneshot.p12._status_file(state, request.request_id)
            legacy_terminal = oneshot.p12._read_json_nofollow(status_path)
            legacy_terminal.pop("process_exit_status")
            legacy_terminal.pop("research_evidence_status")
            status_path.write_text(json.dumps(legacy_terminal))
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertEqual(replay[0]["classification"], "LEGACY_OWNER_ONESHOT_NOT_VERIFIED")
        self.assertEqual(replay[0]["research_evidence_status"], "NOT_VERIFIED")
        self.assertEqual(replay[0]["dispatch_count_added"], 0)
        self.assertFalse(replay[0]["new_key_created"])
        self.assertNotEqual(replay[1], 0)
        self.assertEqual(dispatches, ["dispatch"])

    def test_mixed_legacy_terminal_evidence_is_blocked(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id,
                owner_confirmed=True, target=lambda _: completed_owner_evidence(),
            )
            status_path = oneshot.p12._status_file(state, request.request_id)
            terminal = oneshot.p12._read_json_nofollow(status_path)
            terminal.pop("research_evidence_status")
            status_path.write_text(json.dumps(terminal))
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertEqual(replay[0]["classification"], "BLOCKED_OWNER_ONESHOT_TERMINAL_INCONSISTENT")
        self.assertNotEqual(replay[1], 0)
        self.assertEqual(replay[0]["dispatch_count_added"], 0)

    def test_zero_exit_without_finished_qlib_evidence_is_incomplete_and_replay_fails(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            result, code = oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id,
                owner_confirmed=True,
                target=lambda _: {"target_return_code": 0, "key_blocked_after_attempt": True},
            )
            terminal = oneshot.p12._read_json_nofollow(oneshot.p12._status_file(state, request.request_id))
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertNotEqual(code, 0)
        self.assertEqual(result["classification"], "INCOMPLETE_OWNER_ONESHOT")
        self.assertEqual(terminal["process_exit_status"], "PROCESS_EXIT_SUCCESS")
        self.assertEqual(terminal["research_evidence_status"], "RESEARCH_EVIDENCE_INCOMPLETE")
        self.assertNotEqual(replay[1], 0)
        self.assertEqual(replay[0]["dispatch_count_added"], 0)

    def test_mlflow_evidence_gate_requires_finished_recorder_and_native_outputs(self):
        request_id = identity("evidence-request")
        attempt_id = "d1feb58c-7b86-41f1-8eef-7bd54b1bffd1"
        volume = "aq-p12-owner-artifacts-0123456789abcdef"
        artifacts = {
            "task": False, "dataset": False, "params.pkl": False, "pred.pkl": False,
            "sig_analysis": True, "sig_analysis/ic.pkl": False, "sig_analysis/ric.pkl": False,
            "portfolio_analysis": True,
            "portfolio_analysis/report_normal_1day.pkl": False,
            "portfolio_analysis/port_analysis_1day.pkl": False,
        }
        metrics = {
            "IC": 0.05, "ICIR": 0.3, "Rank IC": 0.04, "Rank ICIR": 0.2,
            **{
                f"1day.{kind}.{metric}": 0.1
                for kind in ("excess_return_without_cost", "excess_return_with_cost")
                for metric in ("annualized_return", "information_ratio", "max_drawdown")
            },
        }

        class Info:
            experiment_id = "1"
            run_id = "recorder-1"
            status = "FINISHED"
            artifact_uri = "file:///qlib-artifacts/recorder-1/artifacts"

        class Run:
            def __init__(self, status):
                self.info = Info()
                self.info.status = status
                self.data = type("Data", (), {"metrics": metrics})()

        class Artifact:
            def __init__(self, path, is_dir=False):
                self.path, self.is_dir = path, is_dir
                self.file_size = 0 if is_dir else 128

        class Client:
            def __init__(self, status="FINISHED", files=None):
                self.run = Run(status)
                self.files = files or artifacts
            def get_experiment_by_name(self, name):
                return type("Experiment", (), {
                    "experiment_id": "1", "artifact_location": "file:///qlib-artifacts",
                    "tags": {"aq.p12.request_id": request_id, "aq.p12.attempt_id": attempt_id,
                             "aq.p12.artifact_volume": volume},
                })()
            def search_runs(self, experiment_ids, max_results):
                return [self.run]
            def list_artifacts(self, run_id, path=None):
                prefix = f"{path}/" if path else ""
                direct = {}
                for name, is_dir in self.files.items():
                    if not name.startswith(prefix):
                        continue
                    remainder = name[len(prefix):]
                    head, separator, _ = remainder.partition("/")
                    direct[f"{prefix}{head}"] = True if separator else is_dir
                return [Artifact(name, is_dir) for name, is_dir in direct.items()]

        args = {"request_id": request_id, "attempt_id": attempt_id, "artifact_volume": volume}
        complete = inspect_research_evidence(Client(), **args)
        failed = inspect_research_evidence(Client(status="FAILED"), **args)
        missing_params = dict(artifacts)
        missing_params.pop("params.pkl")
        missing_model = inspect_research_evidence(Client(files=missing_params), **args)
        empty_folder = inspect_research_evidence(
            Client(files={"sig_analysis": True, "portfolio_analysis": True}), **args
        )
        self.assertEqual(complete["classification"], "RESEARCH_EVIDENCE_COMPLETE")
        self.assertEqual(failed["reason"], "NO_FINISHED_RECORDER")
        self.assertEqual(missing_model["classification"], "RESEARCH_EVIDENCE_INCOMPLETE")
        self.assertIn("model_parameters", missing_model["missing"])
        self.assertEqual(empty_folder["classification"], "RESEARCH_EVIDENCE_INCOMPLETE")

        mismatched = Client()
        mismatched.get_experiment_by_name = lambda name: type("Experiment", (), {
            "experiment_id": "1", "artifact_location": "file:///qlib-artifacts",
            "tags": {"aq.p12.request_id": request_id, "aq.p12.attempt_id": attempt_id,
                     "aq.p12.artifact_volume": "wrong-volume"},
        })()
        self.assertEqual(
            inspect_research_evidence(mismatched, **args)["reason"],
            "ATTEMPT_OR_ARTIFACT_VOLUME_MISMATCH",
        )

    def test_failed_terminal_is_persisted_and_replayed_nonzero(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            result, code = oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id,
                owner_confirmed=True,
                target=lambda _: completed_owner_evidence(1),
            )
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertNotEqual(code, 0)
        self.assertEqual(result["classification"], "FAILED_OWNER_ONESHOT")
        self.assertNotEqual(replay[1], 0)

    def test_ambiguous_target_preserves_blocked_semantics_without_retry(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            result, code = oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id,
                owner_confirmed=True,
                target=lambda _: (_ for _ in ()).throw(TimeoutError("ambiguous")),
            )
            replay = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
        self.assertNotEqual(code, 0)
        self.assertEqual(result["classification"], "BLOCKED_OWNER_ONESHOT_UNKNOWN_DISPATCH")
        self.assertNotEqual(replay[1], 0)
        self.assertIn("BLOCKED_OWNER_ONESHOT", replay[0]["classification"])

    def test_interrupted_claim_and_concurrent_owner_attempt_fail_closed(self):
        envelope, request, policy = owner_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            oneshot.p12._durable_json_create(
                oneshot.p12._claim_file(state, request.request_id),
                {"request_id": request.request_id, "state": "CLAIMED_OWNER_ONESHOT"},
            )
            result, code = oneshot.p12.owner_oneshot_replay_if_claimed(
                envelope, state_dir=state, policy_id=policy.policy_id,
            )
            self.assertNotEqual(code, 0)
            self.assertTrue(result["classification"].startswith("BLOCKED_OWNER_ONESHOT"))
            (state / "owner-oneshot-active.lock").write_text("active")
            concurrent, concurrent_code = oneshot.p12.process_owner_oneshot(
                envelope, state_dir=state, policy_id=policy.policy_id,
                owner_confirmed=True, target=lambda _: self.fail("concurrent attempt must not dispatch"),
            )
        self.assertNotEqual(concurrent_code, 0)
        self.assertEqual(concurrent["classification"], "BLOCKED_OWNER_ONESHOT_CONCURRENT_RUN")

    def test_actual_shell_entrypoint_identity_is_accepted_and_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            script = (SMOKE / "compose.deepseek-staging.yaml").read_text().split("      - |\n", 1)[1].split("\n      - --", 1)[0]
            entrypoint = ["/bin/sh", "-ec", script, "--"]
            environment = [
                "OPENAI_API_BASE=http://litellm-deepseek-staging:4000/v1",
                "OPENAI_API_KEY=sk-dummy-owner-key-0123456789",
                "P12_OWNER_SCOPED_PROXY_KEY=sk-dummy-owner-key-0123456789",
                "LITELLM_CHAT_MAX_TOKENS=8192", "LITELLM_CHAT_MODEL_MAP={}",
                "WORKSPACE_PATH=/workspace/runs/aq-p12-owner-123456789abc/workspaces",
            ]
            inspection = {
                "Image": PINNED_FINQUANT_IMAGE_ID,
                "Config": {"Image": PINNED_FINQUANT_IMAGE, "Entrypoint": entrypoint,
                           "Cmd": ["fin_quant", "--loop-n", "1"], "User": "10001:10001",
                           "Env": environment},
                "State": {"Status": "exited", "ExitCode": 0},
                "HostConfig": {"ReadonlyRootfs": True},
                "Mounts": [
                    {"Destination": target, "Source": source, "RW": False, "Type": "bind"}
                    for target, source in FINQUANT_DATA_MOUNTS.items()
                ] + [
                    {"Destination": "/workspace", "Source": str(output.resolve()), "RW": True, "Type": "bind"},
                    {"Destination": "/qlib-artifacts", "Name": "aq-p12-owner-artifacts-0123456789abcdef", "Source": "/var/lib/docker/volumes/aq-p12-owner-artifacts-0123456789abcdef/_data", "RW": True, "Type": "volume"},
                ],
                "NetworkSettings": {"Networks": {PERSISTENT_LITELLM_NETWORK: {}}},
            }
            observed = validate_owner_worker_inspection(
                inspection, expected_key="sk-dummy-owner-key-0123456789",
                expected_output=output, run_namespace="aq-p12-owner-123456789abc",
                expected_artifact_volume="aq-p12-owner-artifacts-0123456789abcdef",
            )
            self.assertEqual(observed["return_code"], 0)
            bad_name = json.loads(json.dumps(inspection))
            bad_name["Mounts"][-1]["Name"] = "wrong-volume"
            with self.assertRaises(Exception):
                validate_owner_worker_inspection(
                    bad_name, expected_key="sk-dummy-owner-key-0123456789",
                    expected_output=output, run_namespace="aq-p12-owner-123456789abc",
                    expected_artifact_volume="aq-p12-owner-artifacts-0123456789abcdef",
                )
            extra_mount = json.loads(json.dumps(inspection))
            extra_mount["Mounts"].append({
                "Destination": "/unexpected", "Source": "/tmp", "RW": True, "Type": "bind",
            })
            with self.assertRaises(Exception):
                validate_owner_worker_inspection(
                    extra_mount, expected_key="sk-dummy-owner-key-0123456789",
                    expected_output=output, run_namespace="aq-p12-owner-123456789abc",
                    expected_artifact_volume="aq-p12-owner-artifacts-0123456789abcdef",
                )
            inspection["Config"]["Entrypoint"] = ["rdagent"]
            with self.assertRaises(Exception):
                validate_owner_worker_inspection(
                    inspection, expected_key="sk-dummy-owner-key-0123456789",
                    expected_output=output, run_namespace="aq-p12-owner-123456789abc",
                    expected_artifact_volume="aq-p12-owner-artifacts-0123456789abcdef",
                )

    def test_compose_worker_uses_full_loop_pinned_proxy_and_static_token_cap(self):
        compose = (SMOKE / "compose.deepseek-staging.yaml").read_text()
        worker = compose.split("  rdagent-owner-oneshot-worker:", 1)[1].split("secrets:", 1)[0]
        self.assertIn('command: ["fin_quant", "--loop-n", "1"]', worker)
        self.assertNotIn("--step-n", worker)
        self.assertIn('LITELLM_CHAT_MAX_TOKENS: "8192"', worker)
        self.assertIn('LITELLM_CHAT_MODEL_MAP: "{}"', worker)
        self.assertIn("http://litellm-deepseek-staging:4000/v1", worker)
        self.assertIn("networks: [worker_proxy]", worker)
        self.assertIn("target: /qlib-artifacts", worker)
        self.assertIn("P12_MLFLOW_ARTIFACT_VOLUME", worker)
        self.assertEqual(
            _owner_artifact_volume_name(identity("request"), "d1feb58c-7b86-41f1-8eef-7bd54b1bffd1"),
            "aq-p12-owner-artifacts-" + hashlib.sha256(
                f"{identity('request')}:d1feb58c-7b86-41f1-8eef-7bd54b1bffd1".encode()
            ).hexdigest()[:16],
        )
        for forbidden in ("DEEPSEEK_API_KEY", "LITELLM_DEEPSEEK_STAGING_MASTER_KEY", "POSTGRES_PASSWORD", "/var/run/docker.sock"):
            self.assertNotIn(forbidden, worker)
        self.assertEqual(len(oneshot.FINQUANT_DATA_MOUNTS), 3)


if __name__ == "__main__":
    unittest.main()
