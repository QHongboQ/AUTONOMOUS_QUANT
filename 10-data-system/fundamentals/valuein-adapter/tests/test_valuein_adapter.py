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

from aq_valuein_adapter import project_valuein_native_binding


def episode(ticker: str, start: str, end: str, marker: str) -> dict[str, object]:
    return {
        "episode_id": "P1EP-" + marker * 64,
        "index_id": "SP500",
        "normalized_ticker": ticker,
        "valid_from": start,
        "valid_to": end,
        "provenance_hash": marker * 64,
        "resolution_state": "RESOLVED",
    }


def security(
    ticker: str,
    cik: str,
    start: str,
    end: str | None,
    marker: str = "1",
) -> dict[str, object]:
    return {
        "id": f"security-{marker}",
        "entity_id": cik,
        "symbol": ticker,
        "valid_from": start,
        "valid_to": end,
        "exchange": "NYSE",
    }


def membership(
    cik: str,
    start: str,
    end: str | None,
    *,
    index_name: str = "SP500",
    source: str = "historical_seed",
    marker: str = "1",
) -> dict[str, object]:
    return {
        "id": f"membership-{marker}",
        "cik": cik,
        "index_name": index_name,
        "effective_date": start,
        "removal_date": end,
        "source": source,
    }


def reference(cik: str, marker: str = "1") -> dict[str, object]:
    return {
        "security_id": f"security-{marker}",
        "cik": cik,
        "figi": f"FIGI-{marker}",
        "composite_figi": f"COMPOSITE-{marker}",
        "share_class_figi": f"SHARE-{marker}",
    }


class ValueinNativeProjectionTests(unittest.TestCase):
    def project(
        self,
        item: dict[str, object],
        securities: list[dict[str, object]],
        memberships: list[dict[str, object]],
        *,
        entities: list[dict[str, object]] | None = None,
        references: list[dict[str, object]] | None = None,
    ):
        ciks = sorted({str(row["entity_id"]) for row in securities})
        return project_valuein_native_binding(
            item,
            authoritative_episodes=[item],
            security_rows=securities,
            entity_rows=entities if entities is not None else [{"cik": cik} for cik in ciks],
            membership_rows=memberships,
            reference_rows=(
                references
                if references is not None
                else [reference(str(row["entity_id"]), str(row["id"]).split("-")[-1]) for row in securities]
            ),
            snapshot_identity="a" * 64,
        )

    def test_native_exact_case_is_pass_exact_and_deterministic(self) -> None:
        item = episode("FRC", "2019-01-02", "2023-05-04", "a")
        securities = [security("FRC", "0001132979", "2019-01-02", "2023-05-04")]
        memberships = [membership("0001132979", "2019-01-02", "2023-05-04")]
        first = self.project(item, securities, memberships)
        second = self.project(item, securities, memberships)
        self.assertEqual("PASS_EXACT", first.binding_classification)
        self.assertEqual(first.binding_id, second.binding_id)

    def test_native_containing_case_is_pass_corroborated(self) -> None:
        item = episode("AAPL", "2010-01-04", "2025-01-01", "b")
        binding = self.project(
            item,
            [security("AAPL", "0000320193", "1994-01-26", None)],
            [membership("0000320193", "1996-01-02", None)],
        )
        self.assertEqual("PASS_CORROBORATED", binding.binding_classification)
        self.assertEqual("2010-01-04", binding.valid_from.isoformat())
        self.assertEqual("2025-01-01", binding.valid_to.isoformat())

    def test_security_may_start_before_and_end_after_episode(self) -> None:
        item = episode("TEST", "2020-01-01", "2021-01-01", "c")
        binding = self.project(
            item,
            [security("TEST", "0000000001", "2010-01-01", "2030-01-01")],
            [membership("0000000001", "2019-01-01", "2022-01-01")],
        )
        self.assertEqual("PASS_CORROBORATED", binding.binding_classification)

    def test_sp500_membership_exact_or_containing_is_accepted(self) -> None:
        item = episode("TEST", "2020-01-01", "2021-01-01", "d")
        securities = [security("TEST", "0000000001", "2019-01-01", "2022-01-01")]
        for membership_interval in (
            membership("0000000001", "2020-01-01", "2021-01-01"),
            membership("0000000001", "2019-01-01", "2022-01-01"),
        ):
            with self.subTest(membership=membership_interval):
                binding = self.project(item, securities, [membership_interval])
                self.assertEqual("PASS_CORROBORATED", binding.binding_classification)

    def test_russell_membership_cannot_satisfy_sp500_gate(self) -> None:
        item = episode("KMI", "2012-05-25", "2025-01-01", "e")
        with self.assertRaisesRegex(ValueError, "SP500 membership"):
            self.project(
                item,
                [security("KMI", "0001506307", "2010-11-23", None)],
                [
                    membership(
                        "0001506307",
                        "2011-06-30",
                        None,
                        index_name="RUSSELL3000",
                        source="fund_holdings",
                    )
                ],
            )

    def test_fund_holdings_cannot_satisfy_sp500_gate(self) -> None:
        item = episode("TEST", "2020-01-01", "2021-01-01", "f")
        with self.assertRaisesRegex(ValueError, "SP500 membership"):
            self.project(
                item,
                [security("TEST", "0000000001", "2019-01-01", "2022-01-01")],
                [
                    membership(
                        "0000000001",
                        "2019-01-01",
                        "2022-01-01",
                        source="fund_holdings",
                    )
                ],
            )

    def test_multiple_security_identities_and_ciks_fail_closed(self) -> None:
        item = episode("REUSE", "2020-01-01", "2021-01-01", "1")
        securities = [
            security("REUSE", "0000000001", "2019-01-01", "2022-01-01", "1"),
            security("REUSE", "0000000002", "2019-01-01", "2022-01-01", "2"),
        ]
        with self.assertRaisesRegex(ValueError, "unambiguous"):
            self.project(
                item,
                securities,
                [
                    membership("0000000001", "2019-01-01", "2022-01-01"),
                    membership("0000000002", "2019-01-01", "2022-01-01"),
                ],
            )

    def test_partial_and_ticker_boundary_difference_fail_closed(self) -> None:
        item = episode("DD", "2010-01-04", "2017-09-01", "2")
        with self.assertRaisesRegex(ValueError, "does not contain"):
            self.project(
                item,
                [security("DD", "0001666700", "2016-03-01", None)],
                [membership("0001666700", "2010-01-04", "2017-09-01")],
            )

    def test_conflicting_entity_and_reference_relations_fail_closed(self) -> None:
        item = episode("TEST", "2020-01-01", "2021-01-01", "3")
        securities = [security("TEST", "0000000001", "2019-01-01", "2022-01-01")]
        memberships = [membership("0000000001", "2019-01-01", "2022-01-01")]
        with self.assertRaisesRegex(ValueError, "references CIK"):
            self.project(
                item,
                securities,
                memberships,
                references=[reference("0000000002")],
            )

    def test_no_coverage_and_current_ticker_backfill_fail_closed(self) -> None:
        item = episode("FB", "2013-12-23", "2022-06-09", "4")
        with self.assertRaisesRegex(ValueError, "unambiguous"):
            self.project(
                item,
                [security("META", "0001326801", "2005-05-06", None)],
                [membership("0001326801", "2013-12-23", None)],
            )

    def test_unresolved_episode_fails_closed(self) -> None:
        item = episode("TEST", "2020-01-01", "2021-01-01", "5")
        item["resolution_state"] = "AMBIGUOUS"
        with self.assertRaisesRegex(ValueError, "RESOLVED"):
            self.project(
                item,
                [security("TEST", "0000000001", "2019-01-01", "2022-01-01")],
                [membership("0000000001", "2019-01-01", "2022-01-01")],
            )

    def test_evidence_identity_is_stable_under_input_order(self) -> None:
        item = episode("TEST", "2020-01-01", "2021-01-01", "6")
        securities = [security("TEST", "0000000001", "2019-01-01", "2022-01-01")]
        memberships = [
            membership("0000000001", "2019-01-01", "2022-01-01", marker="1"),
            membership("0000000001", "2018-01-01", "2023-01-01", marker="2"),
        ]
        first = self.project(item, securities, memberships)
        second = self.project(item, securities, list(reversed(memberships)))
        self.assertEqual(first.binding_id, second.binding_id)


class ValueinArchitectureTests(unittest.TestCase):
    def test_legacy_exact_only_path_is_absent(self) -> None:
        module = __import__("aq_valuein_adapter")
        for name in (
            "IdentityClassification",
            "ValueinIdentityDecision",
            "admit_exact_valuein_binding",
            "classify_valuein_identity",
        ):
            self.assertFalse(hasattr(module, name))

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
