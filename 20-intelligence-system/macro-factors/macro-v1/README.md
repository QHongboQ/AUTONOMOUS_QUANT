# Macro V1

This boundary materializes the frozen, session-global Macro V1 surface from
official FRED/ALFRED evidence exposed by Vintage 0.9.0. DuckDB owns revision,
window, transformation, and carry-forward composition; `aq_xnys_calendar`
owns XNYS sessions; Pandera validates the boundary; PyArrow writes Parquet.

The two features are `macro_v1_cpiaucsl_d2_log` (FRED code 6) and
`macro_v1_unrate_d1` (FRED code 2). GDP and GDPC1 are excluded. The output is
global by session and is never permanently broadcast by instrument. Consumers
may mechanically join it onto an explicit `(datetime, instrument)` grid.

The credential is external runtime configuration expected by Vintage. It is
not a source dependency or artifact field.

## Terminal status

```text
STATUS = RETIRED_FROM_ACTIVE_CANDIDATE_PATH
SCIENTIFIC_RESULT = NO_MEASURABLE_INCREMENTAL_VALUE
ROLE = HISTORICAL_REPRODUCIBILITY_REFERENCE_ONLY
ACTIVE_DVC_STAGE = NO
```

The implementation and tests remain unchanged as historical reproducibility
references. They are not an active production or candidate feature path.
