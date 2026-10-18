from __future__ import annotations

import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

SMOKE_DIR = Path(__file__).resolve().parents[1] / "docker-rdagent-smoke"
sys.path.insert(0, str(SMOKE_DIR))
import provision_test_key as proxy_key  # noqa: E402


class PersistentProxyKeyTests(unittest.TestCase):
    def test_legacy_zero_argument_mode_preserves_model_scope_and_response(self) -> None:
        output = StringIO()
        with patch.dict(os.environ, {"LITELLM_MASTER_KEY": "sk-master-test"}), patch.object(
            sys, "argv", ["provision_test_key.py"]
        ), patch.object(
            proxy_key, "request", return_value=(200, {"key": "sk-legacy-test"})
        ) as request, redirect_stdout(output):
            self.assertEqual(proxy_key.main(), 0)
        request.assert_called_once_with(
            "POST", "/key/generate", key="sk-master-test", body={"models": proxy_key.MODELS}
        )
        self.assertEqual(
            json.loads(output.getvalue()),
            {"classification": "TEST_PROXY_KEY_CREATED", "token": "sk-legacy-test"},
        )

    def test_explicit_create_command_remains_available(self) -> None:
        result = {
            "classification": "TEST_PROXY_KEY_CREATED",
            "token": "sk-scoped-test",
            "verified": True,
        }
        output = StringIO()
        with patch.object(
            sys, "argv", ["provision_test_key.py", "create", "0.1", "aq-p12-finquant-test-only-abcd"]
        ), patch.object(proxy_key, "create", return_value=result) as create, redirect_stdout(output):
            self.assertEqual(proxy_key.main(), 0)
        create.assert_called_once_with(0.1, "aq-p12-finquant-test-only-abcd")
        self.assertEqual(json.loads(output.getvalue()), result)

    def test_explicit_verify_exhaustion_command_remains_available(self) -> None:
        result = {"classification": "TEST_PROXY_BUDGET_ENFORCED", "excess_denied_before_mock": True}
        output = StringIO()
        with patch.object(sys, "argv", ["provision_test_key.py", "verify-exhaustion"]), patch.object(
            proxy_key, "verify_exhaustion", return_value=result
        ) as verify, redirect_stdout(output):
            self.assertEqual(proxy_key.main(), 0)
        verify.assert_called_once_with()
        self.assertEqual(json.loads(output.getvalue()), result)

    def test_explicit_block_command_remains_available(self) -> None:
        result = {"classification": "TEST_PROXY_KEY_BLOCKED", "blocked": True}
        output = StringIO()
        with patch.object(sys, "argv", ["provision_test_key.py", "block"]), patch.object(
            proxy_key, "block_key", return_value=result
        ) as block, redirect_stdout(output):
            self.assertEqual(proxy_key.main(), 0)
        block.assert_called_once_with()
        self.assertEqual(json.loads(output.getvalue()), result)

    def test_key_scope_requires_all_native_limits(self) -> None:
        info = {
            "models": ["deepseek-chat", "qwen3-embedding:0.6b"],
            "max_budget": 0.1,
            "budget_duration": "1h",
            "expires": "2026-10-18T00:00:00Z",
            "max_parallel_requests": 1,
        }
        self.assertTrue(proxy_key.info_is_scoped(info, 0.1))
        for key, value in (
            ("models", ["deepseek-chat"]),
            ("max_budget", float("inf")),
            ("budget_duration", None),
            ("expires", None),
            ("max_parallel_requests", 2),
        ):
            with self.subTest(key=key):
                changed = {**info, key: value}
                self.assertFalse(proxy_key.info_is_scoped(changed, 0.1))

    def test_exhaustion_waits_for_settled_native_spend(self) -> None:
        values = [
            {"spend": 0.0004},
            {"spend": 0.0005},
            {"spend": 0.0005},
            {"spend": 0.0005},
            {"spend": 0.0005},
        ]
        with patch.object(proxy_key, "key_info", side_effect=values) as key_info, patch.object(
            proxy_key.time, "sleep"
        ):
            info, spend = proxy_key.settled_spend("sk-test", timeout=10, stable_reads=3)
        self.assertEqual(info, {"spend": 0.0005})
        self.assertEqual(spend, 0.0005)
        self.assertEqual(key_info.call_count, 5)

    def test_exhaustion_rejects_nonfinite_native_spend(self) -> None:
        with patch.object(proxy_key, "key_info", return_value={"spend": float("nan")}), patch.object(
            proxy_key.time, "sleep"
        ):
            with self.assertRaisesRegex(RuntimeError, "spend was invalid"):
                proxy_key.settled_spend("sk-test", timeout=1, stable_reads=1)


if __name__ == "__main__":
    unittest.main()
