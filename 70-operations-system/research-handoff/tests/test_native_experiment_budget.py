from __future__ import annotations

import hashlib
import urllib.parse
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docker-rdagent-smoke"))
import native_experiment_budget as budget  # noqa: E402


def identity(seed: str = "experiment") -> budget.P12ExperimentIdentity:
    digest = lambda value: "sha256:" + hashlib.sha256(value.encode()).hexdigest()
    return budget.P12ExperimentIdentity(
        research_budget_identity=digest(seed),
        request_id=digest("request"),
        standing_policy_id=digest("policy"),
    )


def _matches_strptime(value: str, fmt: str) -> bool:
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


class FakeNativeAPI:
    def __init__(self):
        self.users = {}
        self.keys = {}
        self.calls = []
        self.key_index = 0
        self.key_user_id_override = None

    def user_info(self, user_id):
        value = self.users.get(user_id)
        return None if value is None else dict(value)

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        body = body or {}
        if method == "POST" and path == "/user/new":
            if body["user_id"] in self.users:
                return 409, {}
            user = {
                "user_id": body["user_id"],
                "max_budget": body["max_budget"],
                "budget_duration": body["budget_duration"],
                "models": body["models"],
                "max_parallel_requests": body["max_parallel_requests"],
                "spend": 0.0,
            }
            self.users[body["user_id"]] = user
            return 200, {"user_id": body["user_id"]}
        if method == "POST" and path == "/key/generate":
            self.key_index += 1
            token = f"sk-key-{self.key_index}"
            info = {
                "user_id": self.key_user_id_override or body["user_id"],
                "models": body["models"],
                "max_budget": body["max_budget"],
                "budget_duration": body["budget_duration"],
                "max_parallel_requests": body["max_parallel_requests"],
                "expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            }
            self.keys[token] = info
            return 200, {"key": token}
        if method == "GET" and path.startswith("/key/info?"):
            token = path.split("key=", 1)[1]
            return 200, {"info": self.keys[token]}
        if method == "POST" and path == "/key/block":
            return 200, {"blocked": True}
        return 404, {}

    def key_info(self, token):
        return dict(self.keys[token])


class NativeExperimentBudgetTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeNativeAPI()
        self.controller = budget.NativeExperimentBudgetController(self.api)
        self.identity = identity()

    def create_user(self):
        return self.controller.ensure_test_user(
            self.identity,
            budget_usd=0.00012,
            synthetic_fixture_verified=True,
            p12_replay=False,
        )

    def test_user_id_is_deterministic_for_budget_identity_across_requests(self):
        another_request = budget.P12ExperimentIdentity(
            self.identity.research_budget_identity,
            "sha256:" + "a" * 64,
            "sha256:" + "b" * 64,
        )
        self.assertEqual(self.identity.user_id, another_request.user_id)
        self.assertNotEqual(self.identity.user_id, identity("different-experiment").user_id)

    def test_spend_logs_v2_uses_bounded_native_filters_and_pagination(self):
        seen = []
        class QueryAPI(budget.LiteLLMNativeAPI):
            def __init__(self):
                pass
            def request(self, method, path, body=None):
                seen.append((method, path, body))
                return 200, {"data": [], "page": 2, "page_size": 25, "total": 0, "total_pages": 0}
        result = QueryAPI().spend_logs_v2(
            user_id="p12-user", api_key_hash="native-hash", start_date="2026-10-19 00:00:00",
            end_date="2026-10-20 00:00:00", page=2, page_size=25,
        )
        self.assertEqual(result["total_pages"], 0)
        method, path, _ = seen[0]
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)
        self.assertEqual(method, "GET")
        self.assertEqual(urllib.parse.urlsplit(path).path, "/spend/logs/v2")
        self.assertEqual(query["user_id"], ["p12-user"])
        self.assertEqual(query["api_key"], ["native-hash"])
        self.assertEqual(query["page"], ["2"])
        self.assertEqual(query["page_size"], ["25"])
        self.assertEqual(query["start_date"], ["2026-10-19 00:00:00"])
        self.assertEqual(query["end_date"], ["2026-10-20 00:00:00"])

    def test_pinned_spend_logs_date_parser_accepts_only_supported_shapes(self):
        accepted = ("2026-10-19", "2026-10-19 23:59:59")
        rejected = (
            "2026-10-19T23:59:59Z",
            "2026-10-19 23:59:59.123456",
            "2026-10-19 23:59:59+00:00",
        )
        formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d")
        for value in accepted:
            self.assertTrue(any(_matches_strptime(value, fmt) for fmt in formats), value)
        for value in rejected:
            self.assertFalse(any(_matches_strptime(value, fmt) for fmt in formats), value)

    def test_p12_request_policy_budget_identity_must_match(self):
        with self.assertRaisesRegex(budget.BudgetBoundaryDenied, "IDENTITY_MISMATCH"):
            budget.P12ExperimentIdentity.from_p12(
                {"request_id": self.identity.request_id, "research_budget_identity": self.identity.research_budget_identity},
                {"policy_id": self.identity.standing_policy_id, "research_budget_identity": "sha256:" + "f" * 64},
            )

    def test_unknown_owner_authorization_fails_closed_without_api_call(self):
        with self.assertRaisesRegex(budget.BudgetBoundaryDenied, "OWNER_AUTHORIZATION_UNVERIFIED"):
            self.controller.issue_real_key(owner_authorization={"authorization_status": "APPROVED"})
        self.assertEqual(self.api.calls, [])

    def test_native_user_is_created_once_and_replay_reuses_same_budget(self):
        self.create_user()
        creates_before = [call for call in self.api.calls if call[:2] == ("POST", "/user/new")]
        observed = self.controller.ensure_test_user(
            self.identity,
            budget_usd=0.00012,
            synthetic_fixture_verified=True,
            p12_replay=True,
        )
        creates_after = [call for call in self.api.calls if call[:2] == ("POST", "/user/new")]
        self.assertEqual(observed["user_id"], self.identity.user_id)
        self.assertEqual(creates_before, creates_after)
        self.assertEqual(observed["spend"], 0.0)

    def test_missing_native_user_on_replay_never_allocates_a_new_budget(self):
        with self.assertRaisesRegex(budget.BudgetBoundaryDenied, "MISSING_ON_REPLAY"):
            self.controller.ensure_test_user(
                self.identity,
                budget_usd=0.00012,
                synthetic_fixture_verified=True,
                p12_replay=True,
            )
        self.assertFalse(any(path == "/user/new" for _, path, _ in self.api.calls))

    def test_changed_experiment_identity_on_replay_cannot_create_second_user(self):
        self.create_user()
        changed = identity("changed-experiment")
        self.assertNotEqual(changed.user_id, self.identity.user_id)
        with self.assertRaisesRegex(budget.BudgetBoundaryDenied, "MISSING_ON_REPLAY"):
            self.controller.ensure_test_user(
                changed,
                budget_usd=0.00012,
                synthetic_fixture_verified=True,
                p12_replay=True,
            )
        self.assertEqual(len([c for c in self.api.calls if c[1] == "/user/new"]), 1)

    def test_changed_or_higher_native_user_budget_fails_closed(self):
        self.create_user()
        self.api.users[self.identity.user_id]["max_budget"] = 0.00013
        with self.assertRaisesRegex(budget.BudgetBoundaryDenied, "BUDGET_MISMATCH"):
            self.controller.ensure_test_user(
                self.identity,
                budget_usd=0.00012,
                synthetic_fixture_verified=True,
                p12_replay=True,
            )
        self.assertEqual(len([c for c in self.api.calls if c[1] == "/user/new"]), 1)

    def test_user_budget_cannot_be_reset_or_model_scope_changed(self):
        self.create_user()
        for key, value in (("budget_duration", "1h"), ("models", ["deepseek-chat"])):
            self.api.users[self.identity.user_id][key] = value
            with self.subTest(key=key), self.assertRaises(budget.BudgetBoundaryDenied):
                self.controller.ensure_test_user(
                    self.identity,
                    budget_usd=0.00012,
                    synthetic_fixture_verified=True,
                    p12_replay=True,
                )
            self.api.users[self.identity.user_id][key] = None if key == "budget_duration" else list(budget.ALLOWED_MODELS)

    def test_key_is_bound_to_user_and_has_nonresetting_bounded_scope(self):
        self.create_user()
        token = self.controller.issue_test_key(
            self.identity,
            key_alias="aq-p12-exp-test-key-a",
            budget_usd=0.00012,
            user_budget_usd=0.00012,
            synthetic_fixture_verified=True,
            p12_replay=False,
        )
        key = self.api.keys[token]
        self.assertEqual(key["user_id"], self.identity.user_id)
        self.assertIsNone(key["budget_duration"])
        self.assertEqual(key["models"], list(budget.ALLOWED_MODELS))
        self.assertEqual(key["max_parallel_requests"], 1)

    def test_key_not_attached_to_canonical_user_is_blocked(self):
        self.create_user()
        self.api.key_user_id_override = "aq-p12-exp-wrong"
        with self.assertRaisesRegex(budget.BudgetBoundaryDenied, "KEY_SCOPE_MISMATCH"):
            self.controller.issue_test_key(
                self.identity,
                key_alias="aq-p12-exp-test-key-wrong",
                budget_usd=0.00012,
                user_budget_usd=0.00012,
                synthetic_fixture_verified=True,
                p12_replay=False,
            )
        self.assertIn(("POST", "/key/block", {"key": "sk-key-1"}), self.api.calls)

    def test_replay_cannot_issue_another_key(self):
        self.create_user()
        with self.assertRaisesRegex(budget.BudgetBoundaryDenied, "KEY_ISSUANCE_ON_P12_REPLAY"):
            self.controller.issue_test_key(
                self.identity,
                key_alias="aq-p12-exp-test-key-replay",
                budget_usd=0.00012,
                user_budget_usd=0.00012,
                synthetic_fixture_verified=True,
                p12_replay=True,
            )
        self.assertFalse(any(path == "/key/generate" for _, path, _ in self.api.calls))

    def test_key_budget_and_expiration_are_bounded(self):
        for duration in ("25h", "-1", "0h"):
            with self.subTest(duration=duration), self.assertRaises(budget.BudgetBoundaryDenied):
                budget._duration_seconds(duration)
        self.create_user()
        with self.assertRaisesRegex(budget.BudgetBoundaryDenied, "EXCEEDS_USER_BUDGET"):
            self.controller.issue_test_key(
                self.identity,
                key_alias="aq-p12-exp-test-too-large",
                budget_usd=0.00013,
                user_budget_usd=0.00012,
                synthetic_fixture_verified=True,
                p12_replay=False,
            )


if __name__ == "__main__":
    unittest.main()
