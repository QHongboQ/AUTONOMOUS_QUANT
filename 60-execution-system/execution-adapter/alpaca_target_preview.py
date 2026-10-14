"""Fail-closed, non-submitting bridge from frozen P8 targets to an offline preview.

Authority and identity resolvers are deliberately injected: this module does not
own a P2 registry, P4 decision store, human-risk store, market-data feed, or broker.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
import math
import re
from typing import Mapping, Protocol


P2SEC = re.compile(r"^P2SEC[0-9A-F]{64}$")
SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")


def _content_reference(value: object) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("reference"), str)
        and bool(value["reference"])
        and isinstance(value.get("sha256"), str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", value["sha256"]))
    )


@dataclass(frozen=True)
class RiskPolicy:
    max_single_asset_weight: float
    max_gross_weight: float
    max_quote_age_seconds: int
    shorting_permitted: bool
    leverage_permitted: bool


@dataclass(frozen=True)
class Identity:
    symbol: str
    episode_id: str
    effective_from: datetime
    effective_until: datetime | None
    verified: bool


@dataclass(frozen=True)
class Quote:
    price_usd: float
    observed_at: datetime


@dataclass(frozen=True)
class Position:
    quantity: float
    market_value_usd: float


@dataclass(frozen=True)
class AccountState:
    endpoint: str
    paper: bool
    equity_usd: float
    buying_power_usd: float
    shorting_enabled: bool
    multiplier: float
    trading_blocked: bool
    account_blocked: bool
    cash_usd: float


class AuthorityResolver(Protocol):
    def p2_certified(self, candidate_id: str, decision_ref: Mapping) -> bool: ...
    def p4_champion(self, candidate_id: str, decision_ref: Mapping) -> bool: ...
    def human_risk_policy(self, reference: Mapping, effective_time: datetime) -> RiskPolicy | None: ...


class IdentityResolver(Protocol):
    def resolve_p2sec(self, instrument_id: str, effective_time: datetime) -> Identity | None: ...


@dataclass(frozen=True)
class PreviewLine:
    symbol: str
    side: str
    notional_usd: float
    reference_price_usd: float
    estimated_quantity: float


@dataclass(frozen=True)
class Preview:
    target_portfolio_id: str
    executable: bool
    lines: tuple[PreviewLine, ...]
    strategy_uses_leverage: bool


class PreviewRejected(ValueError):
    pass


def _aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _parse_datetime(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if _aware(parsed) else None


def _verify_target_identity(target: Mapping, portfolio_id: str) -> None:
    """Verify the frozen P8 content identity with the upstream JCS library.

    There is deliberately no canonicalization fallback: identity validation is
    unavailable unless the project's approved ``rfc8785`` package is installed.
    """
    try:
        jcs = importlib.import_module("rfc8785")
    except ImportError:
        raise PreviewRejected("RFC8785_VALIDATOR_UNAVAILABLE") from None
    identity_fields_omitted = dict(target)
    identity_fields_omitted.pop("target_portfolio_id", None)
    try:
        canonical = jcs.dumps(identity_fields_omitted)
    except Exception:
        raise PreviewRejected("TARGET_IDENTITY_NOT_CANONICALIZABLE") from None
    expected = "sha256:" + hashlib.sha256(canonical).hexdigest()
    if portfolio_id != expected:
        raise PreviewRejected("TARGET_IDENTITY_MISMATCH")


def build_offline_preview(
    target: Mapping,
    *,
    authorities: AuthorityResolver | None,
    identities: IdentityResolver | None,
    account: AccountState,
    positions: Mapping[str, Position],
    quotes: Mapping[str, Quote],
    now: datetime,
    prior_intent_ids: frozenset[str] = frozenset(),
    order_state_known: bool = True,
) -> Preview:
    """Create an in-memory preview only. This module exposes no submit API."""
    if not _aware(now):
        raise PreviewRejected("NOW_MUST_BE_TIMEZONE_AWARE")
    portfolio_id = target.get("target_portfolio_id")
    if not isinstance(portfolio_id, str) or not SHA256_REF.fullmatch(portfolio_id):
        raise PreviewRejected("INVALID_TARGET_ID")
    if set(target) != {
        "contract_version", "target_portfolio_id", "effective_time", "provenance",
        "input_references", "target_weights", "cash_target_weight", "risk_envelope",
    } or target.get("contract_version") != "AQ_TARGET_PORTFOLIO_V1":
        raise PreviewRejected("FROZEN_P8_CONTRACT_SHAPE_REQUIRED")
    _verify_target_identity(target, portfolio_id)
    if portfolio_id in prior_intent_ids:
        raise PreviewRejected("DUPLICATE_EXECUTION_INTENT")
    effective = _parse_datetime(target.get("effective_time"))
    if effective is None or effective > now:
        raise PreviewRejected("INVALID_OR_FUTURE_EFFECTIVE_TIME")
    if not order_state_known:
        raise PreviewRejected("ORDER_STATE_UNKNOWN")
    if account.endpoint != "https://paper-api.alpaca.markets" or not account.paper:
        raise PreviewRejected("PAPER_ENDPOINT_REQUIRED")
    if account.trading_blocked or account.account_blocked:
        raise PreviewRejected("ACCOUNT_BLOCKED")
    if not math.isfinite(account.equity_usd) or account.equity_usd <= 0:
        raise PreviewRejected("INVALID_ACCOUNT_EQUITY")
    if not math.isfinite(account.buying_power_usd) or account.buying_power_usd < 0:
        raise PreviewRejected("INVALID_ACCOUNT_BUYING_POWER")
    if not math.isfinite(account.cash_usd):
        raise PreviewRejected("INVALID_ACCOUNT_CASH")
    if not math.isfinite(account.multiplier) or account.multiplier < 1.0:
        raise PreviewRejected("INVALID_ACCOUNT_MULTIPLIER")

    refs = target.get("input_references")
    if not isinstance(refs, list) or not refs or authorities is None:
        raise PreviewRejected("CERTIFICATION_AUTHORITY_UNAVAILABLE")
    provenance = target.get("provenance")
    if (
        not isinstance(provenance, dict)
        or set(provenance) != {"producer", "producer_version", "method_id", "output_artifact"}
        or provenance.get("producer") not in {"QLIB", "SKFOLIO"}
        or not provenance.get("producer_version")
        or not provenance.get("method_id")
        or not _content_reference(provenance.get("output_artifact"))
    ):
        raise PreviewRejected("TARGET_PROVENANCE_INVALID")
    for ref in refs:
        if not isinstance(ref, dict):
            raise PreviewRejected("INPUT_REFERENCE_INVALID")
        kind = ref.get("input_kind")
        candidate_id = ref.get("candidate_id")
        p2 = ref.get("p2_certification")
        expected_fields = {"input_kind", "candidate_id", "strategy_artifact", "p2_certification"}
        if kind == "P4_CHAMPION":
            expected_fields.add("p4_champion_decision")
        if set(ref) != expected_fields or not _content_reference(ref.get("strategy_artifact")):
            raise PreviewRejected("INPUT_REFERENCE_INVALID")
        if not isinstance(candidate_id, str) or not SHA256_REF.fullmatch(candidate_id):
            raise PreviewRejected("CANDIDATE_REFERENCE_INVALID")
        if not isinstance(p2, dict) or p2.get("status") != "CERTIFIED" or not _content_reference(p2.get("decision")):
            raise PreviewRejected("P2_CERTIFICATION_REQUIRED")
        if not authorities.p2_certified(candidate_id, p2.get("decision", {})):
            raise PreviewRejected("P2_CERTIFICATION_UNVERIFIED")
        if kind == "P4_CHAMPION":
            p4 = ref.get("p4_champion_decision")
            if not _content_reference(p4) or not authorities.p4_champion(candidate_id, p4):
                raise PreviewRejected("P4_CHAMPION_UNVERIFIED")
        if kind not in {"P2_CERTIFIED_CANDIDATE", "P4_CHAMPION"}:
            raise PreviewRejected("UNSUPPORTED_INPUT_KIND")

    risk_ref = target.get("risk_envelope")
    if (
        not isinstance(risk_ref, dict)
        or risk_ref.get("contract_version") != "AQ_HUMAN_RISK_ENVELOPE_REFERENCE_V1"
        or risk_ref.get("status") != "HUMAN_APPROVED"
        or set(risk_ref) != {
            "contract_version", "status", "risk_envelope_id", "effective_from",
            "effective_until", "human_authority_record", "risk_limit_set",
        }
        or not isinstance(risk_ref.get("risk_envelope_id"), str)
        or not SHA256_REF.fullmatch(risk_ref["risk_envelope_id"])
        or not _content_reference(risk_ref.get("human_authority_record"))
        or not _content_reference(risk_ref.get("risk_limit_set"))
    ):
        raise PreviewRejected("HUMAN_RISK_ENVELOPE_UNSET")
    risk_from = _parse_datetime(risk_ref.get("effective_from"))
    risk_until = _parse_datetime(risk_ref.get("effective_until"))
    if risk_from is None or risk_until is None or risk_until <= risk_from or not (risk_from <= effective < risk_until):
        raise PreviewRejected("HUMAN_RISK_AUTHORITY_TIME_INVALID")
    policy = authorities.human_risk_policy(risk_ref, effective)
    if policy is None:
        raise PreviewRejected("HUMAN_RISK_AUTHORITY_UNVERIFIED")
    if (
        not math.isfinite(policy.max_single_asset_weight)
        or policy.max_single_asset_weight < 0
        or not math.isfinite(policy.max_gross_weight)
        or policy.max_gross_weight < 0
        or policy.max_quote_age_seconds <= 0
    ):
        raise PreviewRejected("RISK_POLICY_INVALID")

    target_weights = target.get("target_weights")
    cash_weight = target.get("cash_target_weight")
    if not isinstance(target_weights, dict) or isinstance(cash_weight, bool) or not isinstance(cash_weight, (int, float)):
        raise PreviewRejected("TARGET_WEIGHTS_INVALID")
    weights = dict(target_weights)
    if any(not P2SEC.fullmatch(key) for key in weights):
        raise PreviewRejected("P2SEC_IDENTITY_REQUIRED")
    all_weights = list(weights.values()) + [cash_weight]
    if any(isinstance(w, bool) or not isinstance(w, (int, float)) or not math.isfinite(w) for w in all_weights):
        raise PreviewRejected("TARGET_WEIGHT_NONFINITE")
    total = sum(all_weights)
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise PreviewRejected("TARGET_WEIGHT_BUDGET_MISMATCH")
    gross = sum(abs(float(w)) for w in weights.values())
    if gross > policy.max_gross_weight + 1e-12:
        raise PreviewRejected("GROSS_EXPOSURE_EXCEEDS_AUTHORITY")
    if any(float(w) > policy.max_single_asset_weight + 1e-12 for w in weights.values()):
        raise PreviewRejected("SINGLE_ASSET_EXPOSURE_EXCEEDS_AUTHORITY")
    if any(float(w) < 0 for w in weights.values()) and not policy.shorting_permitted:
        raise PreviewRejected("SHORTING_NOT_AUTHORIZED")
    if gross > 1.0 + 1e-12 and not policy.leverage_permitted:
        raise PreviewRejected("LEVERAGE_NOT_AUTHORIZED")
    if weights and identities is None:
        raise PreviewRejected("P2SEC_IDENTITY_RESOLVER_UNAVAILABLE")
    lines: list[PreviewLine] = []
    buy_notional = 0.0
    seen_symbols: set[str] = set()
    for symbol, position in positions.items():
        if (
            not isinstance(symbol, str)
            or not symbol
            or not isinstance(position, Position)
            or not math.isfinite(position.quantity)
            or not math.isfinite(position.market_value_usd)
        ):
            raise PreviewRejected("POSITION_STATE_INVALID")
    for instrument_id, raw_weight in sorted(weights.items()):
        identity = identities.resolve_p2sec(instrument_id, effective) if identities is not None else None
        if identity is None or not identity.verified or not identity.episode_id:
            raise PreviewRejected("P2SEC_IDENTITY_UNVERIFIED")
        if not _aware(identity.effective_from) or (identity.effective_until is not None and not _aware(identity.effective_until)):
            raise PreviewRejected("P2SEC_IDENTITY_INTERVAL_INVALID")
        if effective < identity.effective_from or (identity.effective_until is not None and effective >= identity.effective_until):
            raise PreviewRejected("P2SEC_IDENTITY_NOT_VALID_AT_EFFECTIVE_TIME")
        symbol = identity.symbol
        if not symbol or symbol.upper() == instrument_id or symbol in seen_symbols:
            raise PreviewRejected("P2SEC_TO_PROVIDER_SYMBOL_MAPPING_INVALID")
        seen_symbols.add(symbol)
        quote = quotes.get(symbol)
        if quote is None or not _aware(quote.observed_at) or not math.isfinite(quote.price_usd) or quote.price_usd <= 0:
            raise PreviewRejected("USD_PRICE_MISSING_OR_INVALID")
        age = (now - quote.observed_at).total_seconds()
        if age < 0 or age > policy.max_quote_age_seconds:
            raise PreviewRejected("USD_PRICE_STALE_OR_FUTURE")
        position = positions.get(symbol, Position(0.0, 0.0))
        if not math.isfinite(position.quantity) or not math.isfinite(position.market_value_usd):
            raise PreviewRejected("POSITION_STATE_INVALID")
        delta = float(raw_weight) * account.equity_usd - position.market_value_usd
        if math.isclose(delta, 0.0, rel_tol=0.0, abs_tol=1e-9):
            continue
        if delta < 0 and position.quantity + delta / quote.price_usd < -1e-9 and not (account.shorting_enabled and policy.shorting_permitted):
            raise PreviewRejected("SELL_WOULD_CREATE_UNAUTHORIZED_SHORT")
        side = "buy" if delta > 0 else "sell"
        notional = abs(delta)
        if side == "buy":
            buy_notional += notional
        lines.append(PreviewLine(symbol, side, round(notional, 2), quote.price_usd, notional / quote.price_usd))

    unrepresented_positions = {
        symbol for symbol, position in positions.items()
        if (abs(position.quantity) > 1e-12 or abs(position.market_value_usd) > 1e-9)
        and symbol not in seen_symbols
    }
    if unrepresented_positions:
        # Omitted assets cannot be mapped back to P2SEC here, and this module
        # intentionally does not own a full liquidation/execution planner.
        raise PreviewRejected("UNREPRESENTED_POSITION_REQUIRES_LIQUIDATION_PLAN")
    cash_shortfall = buy_notional > account.cash_usd + 1e-9
    gross_leverage = gross > 1.0 + 1e-12
    if cash_shortfall and not policy.leverage_permitted:
        raise PreviewRejected("INSUFFICIENT_CASH_WITHOUT_LEVERAGE")
    if buy_notional > account.buying_power_usd + 1e-9:
        raise PreviewRejected("INSUFFICIENT_BUYING_POWER")
    uses_leverage = gross_leverage or cash_shortfall
    return Preview(portfolio_id, False, tuple(lines), uses_leverage)
