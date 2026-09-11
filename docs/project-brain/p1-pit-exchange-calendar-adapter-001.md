# P1 PIT XNYS Exchange Calendar Adapter

Task: `AUTONOMOUS-QUANT-P1-PIT-EXCHANGE-CALENDAR-ADAPTER-001`

Status: COMPLETE

## Boundary

`10-data-system/trading-calendar/xnys/exchange-calendars-adapter` is the sole
leaf introduced by this task. It owns XNYS session semantics through the exact
dependency `exchange_calendars==4.13.2`.

The public contract accepts and returns canonical ISO `YYYY-MM-DD` strings:

- `is_session`
- `date_to_session`
- `previous_session`
- `next_session`
- `sessions_in_range`

No pandas, timezone, `DatetimeIndex`, or `exchange_calendars` object crosses
the public boundary. Calendar construction uses explicit `2000-01-01` through
`2035-12-31` bounds and all unsupported or ambiguous requests fail explicitly.

The leaf does not own membership, security identity, ticker changes, FJA
parsing, market data, certification, portfolio construction, or execution. It
contains no S&P 500 or symbol-specific business logic.

## Dependency and upstream use

The repository had no shared Python dependency convention at this baseline, so
the exact dependency is declared locally in the leaf. The implementation uses
only the documented public `get_calendar`, `is_session`, `date_to_session`,
`previous_session`, `next_session`, and `sessions_in_range` APIs for XNYS.

No generic calendar framework, alternate exchange, fallback calendar, holiday
table, weekday approximation, private upstream API, or unrelated dependency was
added.

## PIT integration decision

The authoritative-main PIT runtime validates ISO dates and consumes already
selected `effective_session` values. It contains no custom holiday schedule or
date-to-session conversion to replace. Therefore this task does not manufacture
an integration layer or change PIT behavior. A future thin-runtime shrink may
consume this public contract when it has a real session-resolution requirement.

## Verification evidence

- pinned upstream: `exchange_calendars==4.13.2`
- validation runtime: Python 3.12.14
- isolated package check: PASS
- focused calendar tests: 11 PASS
- authoritative-main PIT tests: 93 PASS, including 13 frozen regressions
- touched Python `compileall`: PASS
- Saturday, Sunday, and known XNYS holiday behavior: PASS
- directional and adjacent-session resolution: PASS
- exact inclusive session range: PASS
- invalid ISO and non-session `direction="none"`: fail closed
- 20 accepted identity effective sessions read from reference oracle commit
  `5ea3c1cc6971686a6f1d1e4e1c415e4d0a0de490`: all valid XNYS sessions
- reference oracle imported, mutated, based upon, cherry-picked, or pushed: NO

PIT reconciliation certification and all later data, Qlib, certification,
portfolio, execution, account, and trading work remain outside this task.
