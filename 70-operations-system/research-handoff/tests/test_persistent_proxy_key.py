from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SMOKE_DIR = Path(__file__).resolve().parents[1] / "docker-rdagent-smoke"
sys.path.insert(0, str(SMOKE_DIR))
import provision_test_key as proxy_key  # noqa: E402


class PersistentProxyKeyTests(unittest.TestCase):
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
