# P1 Qlib Dataset Handoff 001

## Result

The public 832-row PIT DatasetSnapshot now has one thin, deterministic handoff
into Qlib's local instrument-membership representation. The adapter lives at
`30-research-system/qlib/dataset-adapter`, reads only `snapshot.json` and
`episodes.jsonl`, and emits:

- `instruments/aq_pit.txt`: Qlib instrument, inclusive start, inclusive end;
- `episode-map.jsonl`: the AQ episode identity and original half-open membership
  interval beside the Qlib inclusive end;
- `handoff.json`: the small logical handoff result.

Every DatasetSnapshot episode remains exactly one Qlib range. The conversion
from AQ's half-open `membership_to` to Qlib's inclusive end subtracts one
calendar day. Because the bound is an exclusive effective-session boundary,
this prevents the ticker from being active on the removal/replacement session;
Qlib's actual trading calendar selects valid sessions inside that span. No
calendar implementation or import was added here.

## Accepted upstream runtime and public APIs

The consumer authority remains the existing WSL `rdagent4qlib` environment:
Qlib `0.9.8.dev26` from source commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`. Windows Qlib `0.9.7` is retained
only as historical deployment evidence. No Qlib environment or package was
created, upgraded, or modified.

The compatibility probe uses public Qlib surfaces:

- `qlib.init`;
- `qlib.data.D.instruments` and `D.list_instruments`;
- `qlib.data.dataset.DatasetH`;
- `qlib.contrib.data.handler.Alpha158`;
- `qlib.workflow.R`;
- `qlib.contrib.strategy.signal_strategy.TopkDropoutStrategy`;
- `qlib.backtest.backtest`;
- `qlib.workflow.record_temp.PortAnaRecord`.

The tiny synthetic provider proved that Qlib accepts one instrument with two
separate membership spans and does not fill the intervening gap. It also proved
the ownership APIs are present. It did not load real market features or execute
DatasetH, Alpha158, a model, predictions, Top-K, a backtest, or portfolio
analysis. Qlib's official data design documents the local `calendars`,
`instruments`, and `features` structure and public instrument provider:
[Qlib data documentation](https://qlib.readthedocs.io/en/latest/component/data.html).

## Episode firewall

The real handoff preserves 832 input episodes and 832 output ranges. Tests
retain the DLPH/APTV and Q/IQV boundaries, two distinct GAS episodes, old IR to
TT plus the later separate IR episode, and the AMD, TER, JBL, FSLR, EQT, and PCG
exit/re-entry gaps. Duplicate episode IDs fail closed. The DatasetSnapshot tree
hash is identical before and after conversion.

Qlib keys native ranges by ticker, so `episode_id` remains AQ-side identity in
the parallel map. Multiple non-overlapping ranges for the same ticker remain
separate entries in Qlib's supported instruments file; the adapter never turns
Qlib into a security master and performs no corporate-lineage stitching.

## Ownership and non-duplication

Qlib owns Dataset/DatasetH, Alpha158 and handlers, model workflow/recording,
prediction generation, Top-K strategy, portfolio backtest, transaction costs,
and portfolio analysis. AQ owns only DatasetSnapshot-to-Qlib conversion and
minimal routing. The checked-in skeleton is explicitly
`NOT_EXECUTED_ON_REAL_MARKET_DATA`.

No AQ dataset, factor, Alpha158, model-tournament, prediction, ranking, Top-K,
backtest, portfolio-analysis, or experiment-tracking framework was added. The
adapter imports no PIT implementation, Pandera, calendar, DVC runtime, or Qlib
private module. PIT, DatasetSnapshot, DVC, calendar, and Pandera leaves were not
modified.

## Verification and state

The previous stack remains 129/129 PASS. Fourteen focused Qlib handoff tests
PASS, yielding 143/143 combined tests. The separate 11 calendar tests PASS and
compileall passes for touched AQ Python.

```text
P0 = COMPLETE
P1 = STARTED
P1_MINIMAL_QUANT = IN_PROGRESS
PIT_UNIVERSE_RESEARCH_READY = YES
DATASET_SNAPSHOT_READY = YES
QLIB_HANDOFF_READY = YES
PIT_UNIVERSE_CERTIFIED = NO
REAL_MARKET_DATA_READY = NO
REAL_ALPHA158_RUN = NO
REAL_MODEL_TRAINING = NO
REAL_BACKTEST = NO
CURRENT_NEXT = P1_MARKET_DATA_HANDOFF
OPENBB_ADDED = NO
ZIPLINE_ADDED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
```
