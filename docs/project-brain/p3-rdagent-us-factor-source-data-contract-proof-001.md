# P3 RD-Agent US Factor Source-Data Contract Proof 001

Status: **COMPLETE — HISTORICAL BLOCKER RESOLVED BY FROZEN FACTOR PRESERVATION**

Proof date: 2026-09-14

This documentation-only proof resolves whether the current AQ US Qlib
provider can safely supply the pinned RD-Agent Factor CoSTEER source-data
contract. It did not implement the binding, materialize `daily_pv.h5`, modify
RD-Agent or Qlib, run an LLM, train, predict, backtest, download data, or alter
P2 authority.

## 1. Authority and result at proof time

```text
RD_AGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
AQ_QLIB_PROVIDER = /mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data
SOURCE_DATA_MATERIALIZATION = BLOCKED
MATERIALIZER_IMPLEMENTATION = NONE
FACTOR_SOURCE_DATA_CONTRACT = BLOCKED
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_RDAGENT_US_QLIB_FACTOR_FIELD_PRESERVATION_001
```

Exact blocker:

> The current AQ Qlib provider does not expose `$factor`; Qlib's public API
> returns NaN for it while returning valid OHLCV. Qlib defines `$factor` as a
> restoration/price-adjustment factor, and the frozen Quantiacs source has a
> nonconstant `split_cumprod` with the same adjusted/original direction.
> Substituting `1.0` would therefore invent incorrect adjustment semantics.
> Preserving the upstream factor through the Qlib provider build requires a
> separately authorized provider-handoff change and is outside this task.

## 2. Pinned RD-Agent contract

The pinned files were inspected directly:

- `rdagent/scenarios/qlib/experiment/utils.py`
- `rdagent/scenarios/qlib/experiment/factor_data_template/generate.py`
- `rdagent/scenarios/qlib/experiment/factor_data_template/README.md`

The official generator initializes the China provider directly with
`provider_uri="~/.qlib/qlib_data/cn_data"`, queries all instruments through
Qlib `D.features`, and exports:

```text
columns = $open, $close, $high, $low, $volume, $factor
HDF key = data
outputs = daily_pv_all.h5, daily_pv_debug.h5
```

`utils.py` copies the generated file to the configured native factor data
folder as `daily_pv.h5` together with the official `README.md`. The README
describes the file as adjusted daily price and volume data. Direct upstream
generator reuse is not possible because its provider and date/instrument
selection are China-specific. RD-Agent does not consume the existing AQ Qlib
binary provider directly in place of this HDF source-data contract.

## 3. Read-only Qlib public-API proof

One bounded instrument sample was queried through the pinned Qlib public API
for 2015-01-02 through 2015-01-06. No provider bytes were changed.

```text
QLIB_OPEN_AVAILABLE = YES
QLIB_CLOSE_AVAILABLE = YES
QLIB_HIGH_AVAILABLE = YES
QLIB_LOW_AVAILABLE = YES
QLIB_VOLUME_AVAILABLE = YES
QLIB_FACTOR_AVAILABLE = NO
```

The selected instrument returned finite OHLCV values on all three sessions;
`$factor` was NaN on all three. Filesystem inspection corroborated, but did
not substitute for, the API proof: the provider has `open`, `high`, `low`,
`close`, and `volume` daily binaries and no factor daily binary.

## 4. Exact Qlib factor semantics

Pinned Qlib documentation defines the field as the **restoration
price-adjustment factor**, normally:

```text
factor = adjusted_price / original_price
original_price = adjusted_price / factor
adjusted-price reference = split adjusted
```

It is not a raw research alpha feature. The official custom-data conversion
example includes `open,close,high,low,volume,factor`, and the documentation
says those fields should be present in a Qlib dataset. See the
[pinned Qlib data documentation](https://github.com/microsoft/qlib/blob/2fb9380b342556ddb50a4b24e4fe8655d548b2b8/docs/component/data.rst)
and the current [official custom-data convention](https://github.com/microsoft/qlib/blob/main/docs/component/data.rst).

The frozen Quantiacs source manifest records:

```text
semantics = QUANTIACS_SPX_ORIGIN_OHLCV_WITH_EXPLICIT_DIVS_AND_SPLIT_CUMPROD
fields = open, low, high, close, vol, divs, split_cumprod, is_liquid
```

Existing Project Brain evidence establishes that the delivered Quantiacs
OHLC is split-adjusted and that original OHLC is reconstructed by division by
`split_cumprod`. A bounded frozen-source check across the AAPL 2020 split
boundary observed `split_cumprod=0.25` on 2020-08-28 and `1.0` on 2020-08-31
and 2020-09-01. This matches Qlib's factor direction and proves the factor is
not globally constant.

```text
QLIB_FACTOR_SEMANTICS = RESTORATION_PRICE_ADJUSTMENT_FACTOR_SPLIT_ADJUSTED
AQ_PROVIDER_PRICE_ADJUSTMENT_SEMANTICS = SPLIT_ADJUSTED_OHLC_WITH_EXPLICIT_NONCONSTANT_SPLIT_CUMPROD_AT_SOURCE
CONSTANT_FACTOR_SEMANTICALLY_VALID = NO
```

Qlib can operate some backtest paths without a factor binary by treating the
prices as adjusted, but that fallback does not satisfy RD-Agent's explicit
six-column Factor CoSTEER HDF contract and does not authorize fabricating the
missing column.

## 5. RD-Agent dependency classification

A fixed-string search of the selected pinned factor/quant Scenario path found
only three direct `$factor` references:

| Use | Classification | Consequence |
|---|---|---|
| both field lists in `factor_data_template/generate.py` | `SOURCE_DATA_REQUIRED` | the official export contract always requests the column |
| field description in `factor_data_template/README.md` | `PROMPT_DOCUMENTATION_ONLY` | the source description presented to factor coding documents the field |
| factor code generated later by the autonomous coder | `OPTIONAL_GENERATED_FACTOR_USE` | not every generated factor must use it, but factors that do require valid source semantics |

No fixed runner, coder, evaluator, or Scenario implementation directly
indexes `$factor` outside the source export. Therefore omission does not prove
that Factor CoSTEER will fail unconditionally for every generated factor; it
does make the official source contract incomplete and can invalidate generated
factors that use the documented field. The contract is not weakened on that
basis.

```text
RD_AGENT_FACTOR_COLUMN_REQUIREMENT = OFFICIAL_SOURCE_DATA_REQUIRED_AND_OPTIONALLY_CONSUMED_BY_GENERATED_FACTORS
```

## 6. Official and community practice

The authoritative convention remains Qlib's: adjusted OHLCV is accompanied
by a restoration factor; the factor is not an arbitrary research feature.
The [official RD-Agent template](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/experiment/factor_data_template/generate.py)
requests it and the [official RD-Agent data README](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/experiment/factor_data_template/README.md)
documents it. The public
[RD-Agent custom-Qlib report in issue 1224](https://github.com/microsoft/RD-Agent/issues/1224)
demonstrates use of a custom Qlib binary provider, but does not establish that
`factor=1` is valid for split-adjusted US history. No mature community
convention inspected overrides the upstream semantic requirement.

```text
OFFICIAL_COMMUNITY_CONVENTION = QLIB_RESTORATION_FACTOR_REQUIRED_FOR_ADJUSTED_CUSTOM_DATA_NO_VALID_CONSTANT_ONE_OVERRIDE_FOUND
```

## 7. Materialization decision

The four allowed alternatives were evaluated:

| Alternative | Decision | Reason |
|---|---|---|
| direct upstream generator reuse | rejected | pinned generator hard-codes the China provider and its own ranges |
| thin configured Qlib export | not yet safe | this is the eventual minimal shape, but the configured AQ provider currently returns NaN for `$factor` |
| existing provider direct use | rejected | the selected RD-Agent path requires native `daily_pv.h5` source data |
| blocked | selected | correct factor cannot be exported through the present Qlib public interface without first preserving the frozen upstream field |

The future preservation task must determine the smallest upstream-native way
to carry the already-frozen Quantiacs `split_cumprod` semantics into the Qlib
provider. It must not recompute adjustment factors heuristically, add a generic
data engine, or change PIT/ragged/sealed-OOS policy. Only after Qlib's public
API returns a correct finite `$factor` may the previously designed thin HDF
export and scenario binding proceed.

```text
SOURCE_DATA_MATERIALIZATION = BLOCKED
MATERIALIZER_IMPLEMENTATION = NONE
```

## 8. Preserved authority and non-actions

```text
PIT_MEMBERSHIP_AUTHORITY_CHANGED = NO
RAGGED_POLICY_CHANGED = NO
SEALED_OOS_ISOLATION = PASS
CODE_CHANGED = NO
DVC_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
DATASET_DOWNLOADS = 0
MARKET_DATA_NETWORK_CALLS = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## 9. Subsequent bounded resolution

The follow-up preservation task located the exact frozen Quantiacs source and
used `split_cumprod` only for rows whose episode, provider asset, session, and
`OBSERVED_PRIMARY` selection were already proven. It did not change the P2
Qlib provider. The resulting full/debug native HDF inputs passed exact row,
factor, schema, native-reader, and China-fallback isolation checks.

The blocked statements above remain the historical result of this proof at
the then-current provider interface. The current state is:

```text
QLIB_FACTOR_FIELD_PRESERVATION = PASS
SOURCE_DATA_MATERIALIZATION = THIN_CONFIGURED_QLIB_EXPORT
MATERIALIZER_IMPLEMENTATION = ONE_THIN_CONTRACT_MATERIALIZER
FACTOR_SOURCE_DATA_CONTRACT = READY_FOR_THIN_BINDING_IMPLEMENTATION
CURRENT_NEXT = P3_RDAGENT_US_THIN_SCENARIO_BINDING_IMPLEMENTATION_001
```
