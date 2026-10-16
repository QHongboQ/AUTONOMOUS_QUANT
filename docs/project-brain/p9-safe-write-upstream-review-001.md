# P9 safe-write upstream patch review 001

**Date:** 2026-10-16
**Classification:** `REVISION_REQUIRED`; independent offline review.
**Packages examined:** alpaca-py 0.44.0 and Lumibot 4.6.18 (`730d5608f3ee625f0a30dc15e8cc512205dd2a2b`).

## Review decision

The isolated patch POC is not ready for upstream submission or Paper use. Its historical local test result remains `ISOLATED_UPSTREAM_FIX_POC_PASS` (two rounds, 22 case assertions), but the independent review found safety and compatibility gaps. The full POC was not rerun during that review. Neither patch was installed or submitted.

### alpaca-py patch candidate — `REVISION_REQUIRED`

The isolated diff appends timeout/retry options, honors zero retries, defaults non-safe methods to no retry, and maps write timeouts/connection failures and 504 to an explicit UNKNOWN exception. Existing normal order handling is not deliberately redesigned. However, the classification is incomplete: post-send response decoding errors and other non-safe 5xx responses can still become ordinary errors. `timeout=None` disables the timeout, `retry_writes=True` re-enables write retries, and malformed settings are not rejected fail-closed. Timeout is Requests connect/read, not a total operation deadline. The SDK lower-version compatibility matrix was not tested.

### Lumibot patch candidate — `REVISION_REQUIRED`

The diff is localized to the Alpaca broker adapter and leaves DriftRebalancerLogic, DriftOrderLogic, order accounting, fill/cancel handling, and position calculation untouched. It passes transport settings and latches writes for the new UNKNOWN exception. It still routes unrecognized exceptions through `Order.ERROR` without a submission block. It does not persist the original intent or automatically restore an unresolved block after restart. The adapter's new arguments may be incompatible with alpaca-py versions allowed by Lumibot's current `>=0.42.0` requirement; only 0.44.0 was tested.

## Three independent safety dimensions

```text
TRANSPORT_SAFETY = OFFLINE POC PASS / UPSTREAM PUBLIC ROUTE BLOCKED
ORDER_LIFECYCLE_SAFETY = NOT_VERIFIABLE
RESTART_RECOVERY_SAFETY = NOT_VERIFIABLE
```

`client_order_id` is a correlation/reconciliation identity, not an exactly-once guarantee. A lost response must remain UNKNOWN; a single 404 or failed lookup cannot authorize a new intent. Pre-submit persistence and restart restoration are demonstrated only by a test-owned manifest/bootstrap, not by the production library path. No recovery engine is proposed here.

## Upstream contribution readiness

`ALPACA_PY_UPSTREAM_PR = NOT_READY` until all ambiguous post-send outcomes are fail-closed, invalid safety configuration is rejected, tests cover wire-level attempts and GET compatibility, and the project API-compatibility gate passes. `LUMIBOT_UPSTREAM_PR = NOT_READY` until the SDK contract is released/targeted, the dependency range is reconciled, every ambiguous exception blocks writes, restart intent restoration has a supported contract, and public docs/tests are added.

Current upstream contribution references and required checks are summarized in the local review. No upstream Issue/PR was created. No source diff, raw test logs, or test manifest is included in this repository.

## Safety status

```text
UPSTREAM_FIX_ACCEPTED = NO
PATCH_INSTALLED = NO
UPSTREAM_PR_CREATED = NO
PAPER_WRITE_AUTHORIZED = NO
LIVE_ENDPOINT_CONTACTED = NO
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
```

The detailed review and prior POC/diff source trees remain in the owner's local research area and are not copied into this public repository.
