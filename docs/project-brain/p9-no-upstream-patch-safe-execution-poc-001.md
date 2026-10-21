# P9 no-upstream-patch safe-execution public-seam feasibility 001

**Date:** 2026-10-16
**Classification:** `BLOCKED_NO_PUBLIC_SEAM`; offline interface audit only.
**Authority:** AQ `origin/main` `7c55ab7277041d303dcd27885915a3caf1ff455a`.
**Upstreams:** Lumibot 4.6.18 (`730d5608f3ee625f0a30dc15e8cc512205dd2a2b`), alpaca-py 0.44.0.

## Purpose and result

This task tested whether Lumibot's selected Strategy/Broker execution and Alpaca's official Python SDK can be composed through supported public APIs to provide a bounded write transport, no implicit replay of non-idempotent POSTs, durable pre-submit intent, fail-closed UNKNOWN handling, and process-restart recovery—without modifying upstream packages.

The public seam is **not available** in these pinned versions. alpaca-py 0.44.0's public `TradingClient` constructor has no timeout, retry-policy, or Session/transport injection argument. The pinned REST implementation owns the `requests.Session`; its default retry path is not method-aware, and the public retry setting does not provide the required supported no-write-retry contract. Lumibot constructs the client internally. Although its source contains a settable `Alpaca.api` property, that setter is undocumented and is not established as a supported extension contract. Source visibility alone does not make it a stable API.

Using that setter, mutating an SDK private Session, directly posting with requests/httpx, or introducing a local proxy would violate the no-private-override/no-custom-execution-boundary requirements. Therefore no integrated POC was built, and all conditional behavior tests are `NOT_RUN`, not PASS.

## What remains upstream-owned

- Lumibot: Strategy lifecycle, rebalancing, order creation/dispatch, broker order mapping, fills and positions.
- alpaca-py: official Trading API client, request/response schemas and order lookup APIs.
- AQ (future, thin policy only): pre-submit intent facts, authorization/write blocking, and fail-closed policy—only after the upstream seams and restart contract exist.

`client_order_id` is a correlation/reconciliation identifier, not proof of idempotent request replay. A timeout, unknown response, single 404, or failed lookup cannot be treated as confirmed rejection. The prior isolated patch POC and its `REVISION_REQUIRED` review retain their original classifications and are not promoted by this audit.

## Evidence and scope

The fixed public sources inspected were the [Lumibot pinned Alpaca broker implementation](https://github.com/Lumiwealth/lumibot/blob/730d5608f3ee625f0a30dc15e8cc512205dd2a2b/lumibot/brokers/alpaca.py), [alpaca-py v0.44.0 REST client](https://github.com/alpacahq/alpaca-py/blob/v0.44.0/alpaca/common/rest.py), and [alpaca-py v0.44.0 TradingClient](https://github.com/alpacahq/alpaca-py/blob/v0.44.0/alpaca/trading/client.py). Lumibot's [Alpaca broker documentation](https://lumibot.lumiwealth.com/brokers.alpaca.html) and the [TradingClient reference](https://alpaca.markets/sdks/python/api_reference/trading/trading-client.html) document the supported broker/client configuration but no custom-client injection seam. Local installed signatures confirmed package versions and the absent timeout/session constructor options; no Broker was instantiated.

The prior P9 supervised Paper Stage A/B/C closeout remains a bounded `ENGINEERING_TEST_ONLY` pass. P9 safe write remains blocked; no Paper or Live readiness follows.

```text
PUBLIC_SAFE_TRANSPORT_PATH = NO
SUPPORTED_LUMIBOT_INTEGRATION = NO
CONDITIONAL_POC = NOT_RUN_NO_SUPPORTED_PUBLIC_SEAM
UPSTREAM_PATCHES_APPLIED = NO
ALPACA_API_CONTACT = NO
BROKER_API_CALLS = 0
BROKER_MUTATIONS = 0
PAPER_ORDERS = 0
LIVE_ORDERS = 0
CUSTOM_EXECUTION_ENGINE_COUNT = 0
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

## Existing interrupted patch-revision work

The local alpaca-py v0.44.0 revision directory was found with three modified upstream files and one untracked test file. Its previous task had not installed the candidate, completed its report, or created/pushed a PR. This task did not modify or remove that directory. The isolated candidate remains unreviewed by upstream and is not an approved runtime.

## Next single action

Wait for or request a documented upstream API to configure bounded transport/no write retries, plus a supported Lumibot client-injection and restart-intent contract. Until then, keep Paper writes disabled; do not work around the absent public seam with private hooks or an AQ engine.
