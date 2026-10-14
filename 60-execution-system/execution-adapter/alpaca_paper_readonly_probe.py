"""One-shot, read-only Alpaca Paper account probe. Secrets arrive only on stdin."""

from __future__ import annotations

import json
import sys
from collections import Counter
from importlib.metadata import version

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest


EXPECTED_ENDPOINT = "https://paper-api.alpaca.markets"
EXPECTED_SDK_VERSION = "0.44.0"


class ReadOnlyProbeError(Exception):
    pass


def validate_payload(payload: object) -> dict[str, str]:
    if not isinstance(payload, dict) or set(payload) != {"endpoint", "api_key", "api_secret"}:
        raise ValueError("INPUT_SHAPE_REJECTED")
    if not isinstance(payload["endpoint"], str) or payload["endpoint"].rstrip("/") not in (
        EXPECTED_ENDPOINT,
        EXPECTED_ENDPOINT + "/v2",
    ):
        raise ValueError("PAPER_ENDPOINT_GUARD_REJECTED")
    if not all(isinstance(payload[name], str) and payload[name] for name in ("api_key", "api_secret")):
        raise ValueError("CREDENTIAL_FIELDS_EMPTY")
    return payload


def read_account(client):
    try:
        return client.get_account()
    except Exception as exc:
        # Never propagate an SDK response body or request detail to the caller.
        raise ReadOnlyProbeError(type(exc).__name__) from None


def main() -> int:
    try:
        payload = validate_payload(json.loads(sys.stdin.readline()))
        sdk_version = version("alpaca-py")
        if sdk_version != EXPECTED_SDK_VERSION:
            raise ValueError("SDK_VERSION_GUARD_REJECTED")

        client = TradingClient(
            api_key=payload["api_key"],
            secret_key=payload["api_secret"],
            paper=True,
        )
        actual_base = str(getattr(client._base_url, "value", client._base_url)).rstrip("/")
        if actual_base != EXPECTED_ENDPOINT:
            raise ValueError("SDK_PAPER_BASE_URL_GUARD_REJECTED")

        account = read_account(client)
        clock = client.get_clock()
        positions = client.get_all_positions()
        orders = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, limit=500))
        order_states = Counter(str(getattr(order, "status", "unknown")) for order in orders)
        result = {
            "endpoint": EXPECTED_ENDPOINT,
            "paper_client": True,
            "sdk_version": sdk_version,
            "account_read": "PASS",
            "account_status": str(getattr(account, "status", "unavailable")),
            "clock_read": "PASS",
            "market_open": bool(getattr(clock, "is_open", False)),
            "positions_read": "PASS",
            "position_count": len(positions),
            "orders_read": "PASS",
            "order_count": len(orders),
            "order_status_counts": dict(sorted(order_states.items())),
        }
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except Exception as exc:  # Return type only; SDK response bodies may contain sensitive data.
        print(json.dumps({"error_type": type(exc).__name__}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
