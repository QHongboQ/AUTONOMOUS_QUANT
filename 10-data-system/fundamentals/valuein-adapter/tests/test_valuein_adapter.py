from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ADAPTER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
CIK_ROOT = REPO_ROOT / "10-data-system" / "fundamentals" / "identity-binding"
for path in (ADAPTER_ROOT, CIK_ROOT):
    sys.path.insert(0, str(path))

from aq_valuein_adapter import (  # noqa: E402
    admit_exact_valuein_binding,
    classify_valuein_identity,
)


def episode(ticker: str, start: str, end: str, marker: str) -> dict[str, object]:
    return {
        "episode_id": "P1EP-" + marker * 64,
        "normalized_ticker": ticker,
        "valid_from": start,
        "valid_to": end,
        "provenance_hash": marker * 64,
    }


def security(
    ticker: str,
    cik: str,
    start: str,
    end: str | None,
    marker: str = "1",
) -> dict[str, object]:
    return {
        "security_id": f"security-{marker}",
        "entity_id": cik,
        "cik": cik,
        "symbol": ticker,
        "valid_from": start,
        "valid_to": end,
    }


def membership(cik: str, start: str, end: str | None) -> dict[str, object]:
    return {
        "cik": cik,
        "effective_date": start,
        "removal_date": end,
        "source": "historical_seed",
    }


CONTROL_CASES = (
    (
        "AAPL",
        episode("AAPL", "2010-01-04", "2025-01-01", "1"),
        [security("AAPL", "0000320193", "1994-01-26", None)],
        "COMPATIBLE_CANDIDATE",
    ),
    (
        "CTL_TO_LUMN",
        episode("CTL", "2010-01-04", "2020-09-18", "2"),
        [],
        "NO_MATCH",
    ),
    (
        "HISTORICAL_BBBY",
        episode("BBBY", "2010-01-04", "2017-07-26", "3"),
        [],
        "NO_MATCH",
    ),
    (
        "DRE",
        episode("DRE", "2017-07-26", "2022-10-03", "4"),
        [security("DRE", "0000783280", "1994-05-12", "2022-10-04")],
        "COMPATIBLE_CANDIDATE",
    ),
    (
        "OLD_DD",
        episode("DD", "2010-01-04", "2017-09-01", "5"),
        [security("DD", "0001666700", "2016-03-01", None)],
        "PARTIAL",
    ),
    (
        "NEW_DD",
        episode("DD", "2019-06-03", "2025-01-01", "6"),
        [security("DD", "0001666700", "2016-03-01", None)],
        "COMPATIBLE_CANDIDATE",
    ),
    (
        "FB_TO_META",
        episode("FB", "2013-12-23", "2022-06-09", "7"),
        [],
        "NO_MATCH",
    ),
    (
        "OLD_CEG",
        episode("CEG", "2010-01-04", "2012-03-13", "8"),
        [],
        "NO_MATCH",
    ),
)


class ValueinIdentityAdapterTests(unittest.TestCase):
    def test_eight_authoritative_control_boundaries(self) -> None:
        for name, item, rows, expected in CONTROL_CASES:
            with self.subTest(name=name):
                decision = classify_valuein_identity(item, rows, [])
                self.assertEqual(expected, decision.classification)

    def test_exact_interval_admits_deterministically(self) -> None:
        item = episode("FRC", "2019-01-02", "2023-05-04", "a")
        rows = [security("FRC", "0001132979", "2019-01-02", "2023-05-04")]
        memberships = [membership("0001132979", "2019-01-02", "2023-05-04")]
        decision = classify_valuein_identity(item, rows, memberships)
        self.assertEqual("EXACT", decision.classification)
        first = admit_exact_valuein_binding(
            decision,
            authoritative_episodes=[item],
            episode=item,
            snapshot_identity="a" * 64,
        )
        second = admit_exact_valuein_binding(
            decision,
            authoritative_episodes=[item],
            episode=item,
            snapshot_identity="a" * 64,
        )
        self.assertEqual(first.binding_id, second.binding_id)
        self.assertEqual("0001132979", first.cik)

    def test_compatible_partial_ambiguous_and_no_match_never_admit(self) -> None:
        item = episode("TEST", "2020-01-01", "2021-01-01", "b")
        cases = (
            [security("TEST", "0000000001", "2019-01-01", "2022-01-01")],
            [security("TEST", "0000000001", "2020-06-01", "2022-01-01")],
            [
                security("TEST", "0000000001", "2019-01-01", "2022-01-01", "1"),
                security("TEST", "0000000002", "2019-01-01", "2022-01-01", "2"),
            ],
            [],
        )
        for rows in cases:
            decision = classify_valuein_identity(item, rows, [])
            with self.subTest(classification=decision.classification), self.assertRaises(
                ValueError
            ):
                admit_exact_valuein_binding(
                    decision,
                    authoritative_episodes=[item],
                    episode=item,
                    snapshot_identity="a" * 64,
                )

    def test_conflicting_accepted_cik_fails_closed(self) -> None:
        item = episode("REUSE", "2020-01-01", "2021-01-01", "c")
        decision = classify_valuein_identity(
            item,
            [security("REUSE", "0000000002", "2020-01-01", "2021-01-01")],
            [],
            accepted_cik="0000000001",
        )
        self.assertEqual("CONFLICT", decision.classification)

    def test_exact_identity_requires_membership_containment(self) -> None:
        item = episode("FRC", "2019-01-02", "2023-05-04", "d")
        decision = classify_valuein_identity(
            item,
            [security("FRC", "0001132979", "2019-01-02", "2023-05-04")],
            [membership("0001132979", "2020-01-01", "2023-05-04")],
        )
        with self.assertRaisesRegex(ValueError, "membership"):
            admit_exact_valuein_binding(
                decision,
                authoritative_episodes=[item],
                episode=item,
                snapshot_identity="a" * 64,
            )


class ValueinArchitectureTests(unittest.TestCase):
    def test_module_contains_no_framework_or_network_client(self) -> None:
        source = (ADAPTER_ROOT / "aq_valuein_adapter" / "__init__.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        forbidden_classes = {
            "ProviderRegistry",
            "ProviderBase",
            "ProviderProtocol",
            "AdapterRegistry",
            "AdapterFactory",
            "GenericAdapter",
            "SecurityMaster",
            "IdentityResolverEngine",
            "FundamentalEngine",
        }
        self.assertFalse(
            forbidden_classes.intersection(
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            )
        )
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse(imported.intersection({"requests", "httpx", "valuein_sdk"}))


if __name__ == "__main__":
    unittest.main()
