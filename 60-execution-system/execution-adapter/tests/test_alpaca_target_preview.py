from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alpaca_target_preview import (  # noqa: E402
    AccountState,
    Identity,
    Position,
    PreviewRejected,
    Quote,
    RiskPolicy,
    build_offline_preview,
)
import alpaca_target_preview as preview_module  # noqa: E402


NOW = datetime(2026, 10, 13, 18, 0, tzinfo=timezone.utc)
DEFAULT_FIXTURE = object()
P2SEC_ID = "P2SEC" + "A" * 64
TARGET_ID = "sha256:" + "b" * 64
CANDIDATE_ID = "sha256:" + "c" * 64
DECISION = {"reference": "fixture://p2/decision", "sha256": "d" * 64}
RISK_REF = {
    "contract_version": "AQ_HUMAN_RISK_ENVELOPE_REFERENCE_V1",
    "status": "HUMAN_APPROVED",
    "risk_envelope_id": "sha256:" + "e" * 64,
    "effective_from": "2026-10-01T00:00:00Z",
    "effective_until": "2026-11-01T00:00:00Z",
    "human_authority_record": {"reference": "fixture://risk/authority", "sha256": "f" * 64},
    "risk_limit_set": {"reference": "fixture://risk/limits", "sha256": "1" * 64},
}


class FixtureAuthority:
    def __init__(self, *, p2=True, p4=True, risk=True, policy=None):
        self.p2 = p2
        self.p4 = p4
        self.risk = risk
        self.policy = policy or RiskPolicy(0.5, 1.0, 60, False, False)

    def p2_certified(self, candidate_id, decision_ref):
        return self.p2 and candidate_id == CANDIDATE_ID and decision_ref == DECISION

    def p4_champion(self, candidate_id, decision_ref):
        return self.p4 and candidate_id == CANDIDATE_ID and decision_ref == DECISION

    def human_risk_policy(self, reference, effective_time):
        return self.policy if self.risk and reference == RISK_REF else None


class FixtureIdentity:
    def __init__(self, identity=None):
        self.identity = identity or Identity(
            "SPY", "P1EPISODE-fixture", NOW - timedelta(days=30), None, True
        )

    def resolve_p2sec(self, instrument_id, effective_time):
        return self.identity if instrument_id == P2SEC_ID else None


def target(*, weight=0.25, cash=0.75, kind="P2_CERTIFIED_CANDIDATE", risk=RISK_REF, weights=None):
    item = {
        "input_kind": kind,
        "candidate_id": CANDIDATE_ID,
        "strategy_artifact": {"reference": "fixture://strategy", "sha256": "2" * 64},
        "p2_certification": {"status": "CERTIFIED", "decision": DECISION},
    }
    if kind == "P4_CHAMPION":
        item["p4_champion_decision"] = DECISION
    return {
        "contract_version": "AQ_TARGET_PORTFOLIO_V1",
        "target_portfolio_id": TARGET_ID,
        "effective_time": "2026-10-13T17:59:00Z",
        "provenance": {"producer": "QLIB", "producer_version": "fixture", "method_id": "fixture", "output_artifact": {"reference": "fixture://out", "sha256": "3" * 64}},
        "input_references": [item],
        "target_weights": {P2SEC_ID: weight} if weights is None else weights,
        "cash_target_weight": cash,
        "risk_envelope": risk,
    }


def preview(*, t=None, authorities=None, identities=DEFAULT_FIXTURE, account=None, positions=None, quotes=None,
            prior_intent_ids=frozenset(), order_state_known=True):
    # The local runtime has no approved rfc8785 installation. This bypass is
    # limited to unit tests for downstream preview mechanics; the public path
    # is separately tested to fail closed when JCS verification is unavailable.
    with patch.object(preview_module, "_verify_target_identity", return_value=None):
        return build_offline_preview(
            t or target(),
            authorities=authorities if authorities is not None else FixtureAuthority(),
            identities=FixtureIdentity() if identities is DEFAULT_FIXTURE else identities,
            account=account or AccountState("https://paper-api.alpaca.markets", True, 10_000, 10_000, False, 1.0, False, False, 10_000),
            positions=positions if positions is not None else {},
            quotes=quotes if quotes is not None else {"SPY": Quote(100.0, NOW - timedelta(seconds=10))},
            now=NOW,
            prior_intent_ids=prior_intent_ids,
            order_state_known=order_state_known,
        )


class AlpacaTargetPreviewTests(unittest.TestCase):
    def test_valid_p2sec_synthetic_preview_is_non_executable_and_deterministic(self):
        first = preview()
        second = preview()
        self.assertEqual(first, second)
        self.assertFalse(first.executable)
        self.assertEqual(first.lines[0].symbol, "SPY")
        self.assertEqual(first.lines[0].notional_usd, 2500.0)
        self.assertFalse(first.strategy_uses_leverage)

    def test_public_preview_fails_closed_when_rfc8785_is_unavailable(self):
        with patch.object(preview_module.importlib, "import_module", side_effect=ImportError):
            with self.assertRaisesRegex(PreviewRejected, "RFC8785_VALIDATOR_UNAVAILABLE"):
                build_offline_preview(
                    target(), authorities=FixtureAuthority(), identities=FixtureIdentity(),
                    account=AccountState("https://paper-api.alpaca.markets", True, 10_000, 10_000, False, 1.0, False, False, 10_000),
                    positions={}, quotes={"SPY": Quote(100.0, NOW - timedelta(seconds=10))}, now=NOW,
                )

    def test_jcs_identity_digest_is_checked_without_a_local_canonicalizer(self):
        from types import SimpleNamespace

        fixture_bytes = b"official-rfc8785-fixture-output"
        canonicalizer = SimpleNamespace(dumps=lambda value: fixture_bytes)
        fixture_target = target()
        fixture_target.pop("target_portfolio_id")
        correct_id = "sha256:" + hashlib.sha256(fixture_bytes).hexdigest()
        with patch.object(preview_module.importlib, "import_module", return_value=canonicalizer) as imported:
            preview_module._verify_target_identity(fixture_target, correct_id)
            imported.assert_called_once_with("rfc8785")
            with self.assertRaisesRegex(PreviewRejected, "TARGET_IDENTITY_MISMATCH"):
                preview_module._verify_target_identity(fixture_target, "sha256:" + "0" * 64)

    def test_sdk_market_request_static_compatibility_only(self):
        from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import MarketOrderRequest

        client = TradingClient(api_key="fixture-key", secret_key="fixture-secret", paper=True)
        base_url = getattr(client._base_url, "value", client._base_url)
        self.assertEqual(str(base_url).rstrip("/"), "https://paper-api.alpaca.markets")

        line = preview().lines[0]
        request = MarketOrderRequest(
            symbol=line.symbol,
            notional=line.notional_usd,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )
        fields = request.to_request_fields()
        self.assertEqual(fields["symbol"], "SPY")
        self.assertEqual(float(fields["notional"]), 2500.0)
        self.assertEqual(fields["type"].value, "market")

    def test_invalid_credential_shape_rejected_before_sdk_construction(self):
        import alpaca_paper_readonly_probe as probe

        with patch.object(probe, "TradingClient", side_effect=AssertionError("SDK must not be constructed")):
            with self.assertRaisesRegex(ValueError, "CREDENTIAL_FIELDS_EMPTY"):
                probe.validate_payload({"endpoint": "https://paper-api.alpaca.markets", "api_key": "", "api_secret": ""})

    def test_authentication_failure_is_redacted(self):
        import alpaca_paper_readonly_probe as probe

        class RejectingClient:
            def get_account(self):
                raise RuntimeError("fixture secret-bearing response body")

        with self.assertRaises(probe.ReadOnlyProbeError) as caught:
            probe.read_account(RejectingClient())
        self.assertEqual(str(caught.exception), "RuntimeError")
        self.assertNotIn("fixture secret-bearing response body", str(caught.exception))

    def test_missing_certified_decision_fails_closed(self):
        invalid = target()
        invalid["input_references"][0]["p2_certification"]["status"] = "CANDIDATE"
        with self.assertRaisesRegex(PreviewRejected, "P2_CERTIFICATION_REQUIRED"):
            preview(t=invalid)

    def test_invalid_champion_reference_fails_closed(self):
        champion = target(kind="P4_CHAMPION")
        with self.assertRaisesRegex(PreviewRejected, "P4_CHAMPION_UNVERIFIED"):
            preview(t=champion, authorities=FixtureAuthority(p4=False))

    def test_unset_human_risk_envelope_fails_closed(self):
        unset = {"contract_version": "AQ_HUMAN_RISK_ENVELOPE_REFERENCE_V1", "status": "UNSET"}
        with self.assertRaisesRegex(PreviewRejected, "HUMAN_RISK_ENVELOPE_UNSET"):
            preview(t=target(risk=unset))

    def test_unverified_p2sec_identity_fails_closed(self):
        identity_resolver = FixtureIdentity()
        identity_resolver.identity = None
        with self.assertRaisesRegex(PreviewRejected, "P2SEC_IDENTITY_UNVERIFIED"):
            preview(identities=identity_resolver)

    def test_ticker_alias_is_not_a_p2sec_identity(self):
        invalid = target()
        invalid["target_weights"] = {"SPY": 0.25}
        with self.assertRaisesRegex(PreviewRejected, "P2SEC_IDENTITY_REQUIRED"):
            preview(t=invalid)

    def test_missing_usd_price_fails_closed(self):
        with self.assertRaisesRegex(PreviewRejected, "USD_PRICE_MISSING_OR_INVALID"):
            preview(quotes={})

    def test_stale_price_fails_closed(self):
        stale = {"SPY": Quote(100.0, NOW - timedelta(seconds=61))}
        with self.assertRaisesRegex(PreviewRejected, "USD_PRICE_STALE_OR_FUTURE"):
            preview(quotes=stale)

    def test_buying_power_short_leverage_duplicate_order_and_endpoint_guards(self):
        poor = AccountState("https://paper-api.alpaca.markets", True, 10_000, 100, False, 1.0, False, False, 10_000)
        with self.assertRaisesRegex(PreviewRejected, "INSUFFICIENT_BUYING_POWER"):
            preview(account=poor)
        with self.assertRaisesRegex(PreviewRejected, "SHORTING_NOT_AUTHORIZED"):
            preview(t=target(weight=-0.1, cash=1.1))
        with self.assertRaisesRegex(PreviewRejected, "LEVERAGE_NOT_AUTHORIZED"):
            preview(
                t=target(weight=1.1, cash=-0.1),
                authorities=FixtureAuthority(policy=RiskPolicy(1.5, 1.5, 60, False, False)),
            )
        with self.assertRaisesRegex(PreviewRejected, "DUPLICATE_EXECUTION_INTENT"):
            preview(prior_intent_ids=frozenset({TARGET_ID}))
        live = AccountState("https://api.alpaca.markets", False, 10_000, 10_000, False, 1.0, False, False, 10_000)
        with self.assertRaisesRegex(PreviewRejected, "PAPER_ENDPOINT_REQUIRED"):
            preview(account=live)

    def test_unknown_order_state_fails_closed(self):
        with self.assertRaisesRegex(PreviewRejected, "ORDER_STATE_UNKNOWN"):
            preview(order_state_known=False)

    def test_unverified_authority_and_blocked_account_fail_closed(self):
        with self.assertRaisesRegex(PreviewRejected, "P2_CERTIFICATION_UNVERIFIED"):
            preview(authorities=FixtureAuthority(p2=False))
        blocked = AccountState("https://paper-api.alpaca.markets", True, 10_000, 10_000, False, 1.0, True, False, 10_000)
        with self.assertRaisesRegex(PreviewRejected, "ACCOUNT_BLOCKED"):
            preview(account=blocked)

    def test_cash_only_with_existing_position_fails_closed_for_missing_liquidation_plan(self):
        cash_only = target(cash=1.0, weights={})
        with self.assertRaisesRegex(PreviewRejected, "UNREPRESENTED_POSITION_REQUIRES_LIQUIDATION_PLAN"):
            preview(t=cash_only, positions={"SPY": Position(10.0, 1_000.0)})

    def test_cash_only_with_no_positions_is_a_valid_empty_preview(self):
        result = preview(t=target(cash=1.0, weights={}), positions={}, identities=None)
        self.assertEqual(result.lines, ())
        self.assertFalse(result.executable)
        self.assertFalse(result.strategy_uses_leverage)

    def test_explicit_zero_weight_produces_sell_preview_for_existing_holding(self):
        result = preview(t=target(weight=0.0, cash=1.0), positions={"SPY": Position(25.0, 2_500.0)})
        self.assertEqual(len(result.lines), 1)
        self.assertEqual((result.lines[0].side, result.lines[0].notional_usd), ("sell", 2_500.0))

    def test_margin_capability_does_not_mean_strategy_uses_leverage(self):
        margin_account = AccountState("https://paper-api.alpaca.markets", True, 10_000, 20_000, False, 2.0, False, False, 10_000)
        result = preview(account=margin_account)
        self.assertFalse(result.strategy_uses_leverage)

    def test_buying_power_cannot_substitute_for_cash_without_leverage_authority(self):
        margin_account = AccountState("https://paper-api.alpaca.markets", True, 10_000, 20_000, False, 2.0, False, False, 1_000)
        with self.assertRaisesRegex(PreviewRejected, "INSUFFICIENT_CASH_WITHOUT_LEVERAGE"):
            preview(account=margin_account)


if __name__ == "__main__":
    unittest.main(verbosity=2)
