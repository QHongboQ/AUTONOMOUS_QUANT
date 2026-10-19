"""No-paid tests for the explicit local one-shot boundary and native budgets."""

from __future__ import annotations

import hashlib
import json
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
import standing_policy  # noqa: E402
from native_experiment_budget import (  # noqa: E402
    OWNER_ONESHOT_MODELS,
    NativeExperimentBudgetController,
    P12ExperimentIdentity,
    experiment_user_id,
)


def identity(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


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
            oneshot._ensure_experiment_binding(state_dir, request, policy)
            changed_request = request.model_copy(update={"request_id": identity("different-request")})
            with self.assertRaisesRegex(ValueError, "already bound"):
                oneshot._ensure_experiment_binding(state_dir, changed_request, policy)

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
        digest = hashlib.sha256(oneshot.rfc8785.dumps(envelope)).hexdigest()
        user_id = experiment_user_id(request.research_budget_identity)
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            attempt = "90dba3ad-a291-4fb7-9df4-cd84e3556396"
            common = {
                "request_id": request.request_id, "request_digest": digest,
                "research_budget_identity": request.research_budget_identity,
                "native_experiment_user_id": user_id, "standing_policy_id": policy.policy_id,
                "attempt_id": attempt, "target_identity": oneshot.REAL_TARGET,
            }
            claim = {**common, "state": "CLAIMED_OWNER_ONESHOT", "dispatch_mode": "OWNER_ONESHOT"}
            dispatch = {**common, "state": "DISPATCHING_OWNER_ONESHOT", "dispatch_mode": "OWNER_ONESHOT"}
            status = {
                **common, "state": "SUCCEEDED_OWNER_ONESHOT", "dispatch_mode": "OWNER_ONESHOT",
                "target_return_code": 0, "key_blocked_after_attempt": True,
                "real_dispatch_permission": "LOCAL_INTERACTIVE_OWNER_CONFIRMED",
                "candidate_count": 0, "broker_actions": 0, "sealed_oos_accessed": False,
            }
            for path, value in ((oneshot.p12._claim_file(state, request.request_id), claim), (oneshot.p12._dispatch_file(state, request.request_id), dispatch), (oneshot.p12._status_file(state, request.request_id), status)):
                path.write_text(json.dumps(value))
            result, code = oneshot._owner_replay(state, request.request_id, digest, request.research_budget_identity, user_id, policy.policy_id)
        self.assertEqual(code, 0)
        self.assertEqual(result["dispatch_count_added"], 0)

    def test_compose_worker_uses_full_loop_pinned_proxy_and_static_token_cap(self):
        compose = (SMOKE / "compose.deepseek-staging.yaml").read_text()
        worker = compose.split("  rdagent-owner-oneshot-worker:", 1)[1].split("secrets:", 1)[0]
        self.assertIn('command: ["fin_quant", "--loop-n", "1"]', worker)
        self.assertNotIn("--step-n", worker)
        self.assertIn('LITELLM_CHAT_MAX_TOKENS: "8192"', worker)
        self.assertIn('LITELLM_CHAT_MODEL_MAP: "{}"', worker)
        self.assertIn("http://litellm-deepseek-staging:4000/v1", worker)
        self.assertIn("networks: [worker_proxy]", worker)
        for forbidden in ("DEEPSEEK_API_KEY", "LITELLM_DEEPSEEK_STAGING_MASTER_KEY", "POSTGRES_PASSWORD", "/var/run/docker.sock"):
            self.assertNotIn(forbidden, worker)
        self.assertEqual(len(oneshot.FINQUANT_DATA_MOUNTS), 3)


if __name__ == "__main__":
    unittest.main()
