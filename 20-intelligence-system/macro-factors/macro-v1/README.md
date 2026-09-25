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
