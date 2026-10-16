# P9 execution-safety evidence rollup 001

**Date:** 2026-10-16
**Classification:** evidence rollup only; no runtime, broker, or strategy authorization.
**Upstream:** Lumibot 4.6.18 at `730d5608f3ee625f0a30dc15e8cc512205dd2a2b`; alpaca-py 0.44.0.

## Authority and current state

PR #149 (Qlib feasibility), #151 (Lumibot selection), and #153 (supervised Stage A/B/C Paper lifecycle) are merged. PR #150 remains OPEN and unmerged. The Stage A/B/C acceptance is authoritative in [P9 supervised Paper lifecycle acceptance 001](p9-supervised-paper-lifecycle-acceptance-001.md); this rollup does not duplicate or alter it.

```text
P9_EXECUTION_UPSTREAM = LUMIBOT_4.6.18
P9_PAPER_BROKER = ALPACA_PAPER
P9_SUPERVISED_PAPER_LIFECYCLE = PASS (PR #153; ENGINEERING_TEST_ONLY)
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
P8_CONTRACT_MODIFIED = NO
P2_SEALED_OOS_ACCESSED = NO
```

## Chronological evidence ledger

The classifications below preserve the scope of each test. A PASS in an offline/backtest/engineering scope is not a production authorization.

| Sequence / evidence | Result | Scope and limitation |
|---|---|---|
| Earlier official native lifecycle: cash-only target and simulated liquidation | `PASS` (local report references two successful end-to-end runs) | Source A cites this predecessor harness. Its raw harness/logs are outside the five specified evidence directories: `RAW_CASH_ONLY_ARTIFACTS = MISSING` for this rollup. This does not close the canonical Project Brain cash-only gate, which remains `NOT_VERIFIABLE` pending evidence reconciliation. |
| Earlier native cancel-race finding | `FAIL` (preserved historical result) | Prior `pending_cancel → canceled` normalization can make a cancel-pending order look terminal to Lumibot. The original raw cancel-race artifact is `MISSING` from Sources A–E. Conservative policy must rely on raw broker status and fail closed; this rollup does not claim the upstream behavior was fixed. |
| Conservative Execution V1 offline feasibility (Source A) | `PASS` for no-auto-cancel strategy override, unresolved-order policy truth table, two-session DAY simulation, and seven-file normalized source equivalence; `NOT_VERIFIABLE` for native partial-fill E2E and real restart/ambiguous-submit recovery | DAY result is simulator-only. The offline policy does not constitute a deployed Strategy guard or Paper integration. Original report records raw installed-vs-pinned byte hashes differing only by line endings after normalization. |
| Multi-order Paper read-only preflight (Source B) | `BLOCKED_SAFETY` for multi-order writes; `PASS_WITHIN_CURRENT_RESPONSE` for the observed read snapshot | 11 logical SDK reads; physical retry count unknown; zero writes. The 500-item response limit means lifetime order inventory completeness was not proven. Historical snapshot is not current account state. |
| alpaca-py/Lumibot safe-write public seam audit (Source C) | `BLOCKED_UPSTREAM` | Pinned public TradingClient route had no usable supported finite timeout/write-retry-off configuration; Lumibot client injection was source-only. No broker calls. |
| Isolated upstream fix POC (Source D) | `ISOLATED_UPSTREAM_FIX_POC_PASS` | Two rounds, 11 cases per round; eight loopback POSTs, four loopback GETs, four mocked transport attempts; zero external requests. The POC is not upstream-accepted, not installed, and does not prove durable intent/restart recovery. |
| Independent patch review (Source E) | `REVISION_REQUIRED` | Found unclassified ambiguous response/error paths, test-harness-only pre-submit intent persistence/restart restoration, unsafe config not rejected, and unverified compatibility with Lumibot's declared alpaca-py lower bound. |
| Supervised Paper lifecycle Stage A/B/C (PR #153) | `PASS` | Read-only sync, one authorized test buy with fresh-process recovery, and one authorized cleanup sell passed. This remains `ENGINEERING_TEST_ONLY`; no forward/continuous/production readiness follows. See the merged authoritative record, not this summary, for redacted results and private evidence fingerprints. |

The first two entries are retained to make the known historical results visible, but their original raw evidence is not present in the bounded Source A–E set. No new claim is inferred from missing files.

## Evidence fingerprints

SHA-256 fingerprints refer to local files that remain outside Git. The repository contains no raw broker responses, local logs, patch source trees, account identifiers, or private order IDs.

| Local evidence | SHA-256 |
|---|---|
| Source A `final-report.md` | `974b322922047777f053a3cc17fd677f08cf38c806313834c59dd29cfc460601` |
| Source A `day-order-run-1.json` | `21b8fe4fc3c9603ffde380185f08f7a03c0acce21abe3a1faaf620dd45f3384` |
| Source A `day-order-run-2.json` | `7b52ccdf835b687a6974db0c245a23135d7264da3e34eeee961b443154065eb9` |
| Source B `final-report.md` | `65898fdcaa1d20d97fbb4045238e9ad2977667a59a0c8baab19029e5001c9755` |
| Source C `final-report.md` | `7001262fc67e43afded632b1dda2659171d92a895f8a24595c0faaff3d9a0e3e3` |
| Source D `final-report.md` | `542801e3d1386d8e33d0d8323ab97d0a4e85f73690033a19555083252bb10ab5` |
| Source D `fault-injection-poc.py` | `2b493a17d819bfcbb63cd8a76af5477d05f9e00f4fe839d072cd990e2c84b2e05` |
| Source D round-1 / round-2 JSON (same digest) | `6e8f8753a6195d6dc1a32c9387df8bbe5cdf23f6307b29772bbba559e730c6e0` |
| Source D test `summary.json` | `b677791e5068e18973b8edf4a88be484b934b68e01b0f4e92903a618c46cbdc9` |
| Source D `patch-review.diff.md` | `68adf39f5315be8d8579bae17ba2c6c8098e436b94348d17b111cbd6d2346894` |
| Source E `final-report.md` | `e6f6da9e76b2eaeac91d47f28dfb9cf7eb52708b9743afc614c055d2acda3689` |
| Source E `independent-review.md` | `baae3c02f9bd57bd5ea318ea77e1760e9aba75062f4ea2f98363bfb403108747` |
| Source E `compatibility-review.md` | `2b1142907a49ac450c6ec7303a793046abec3f00ee71b1eaa888979362d55ad4` |
| Source E `remaining-safety-blockers.md` | `fcf3d6ed08ce63eb06a0d9a86386e8b1e15873899b1a0f9409eb7a72b7eb353e` |
| Source E `upstream-submission-plan.md` | `ad878f765357556d76ee771d004928078230a2dad97345b1fb9adead11c66878` |

Source B's account-state JSON and Source D's full source copies are intentionally not committed. All five evidence directories were present; missing raw cash-only and original cancel-race artifacts are explicitly identified above.

## Remaining P9 gates

`P9 safe write` is **`BLOCKED_UPSTREAM`**, with the isolated candidate needing revision. Transport-level no-replay in a local POC does not settle order lifecycle safety or restart recovery. Still open: complete unknown-outcome classification; durable client-order intent before submit; restart restoration; reconciliation/unblocking criteria; safe behavior on query failure and incomplete order inventory; partial-fill/cancel-race handling; the official cash-liquidation gate; valid P2/P4 strategy authority; P2SEC-to-broker instrument mapping; human-approved capital/risk bounds; and unattended runtime/recovery. Do not infer those gates from PR #153.

```text
TRANSPORT_SAFETY = BLOCKED_UPSTREAM (POC ONLY; REVISION_REQUIRED)
ORDER_LIFECYCLE_SAFETY = NOT_VERIFIABLE
RESTART_RECOVERY_SAFETY = NOT_VERIFIABLE
MULTI_ORDER_PAPER = NOT_EXECUTED
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
```

## Next single action

Revise the alpaca-py candidate to classify every ambiguous non-idempotent write outcome fail-closed and add upstream-native transport regression tests; then reassess whether a Lumibot adapter proposal is warranted. No Paper test is authorized by this rollup.
