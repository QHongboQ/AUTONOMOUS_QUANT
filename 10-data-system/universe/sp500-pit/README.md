# S&P 500 point-in-time universe adapter

This project-owned compatibility adapter uses the same Wikipedia source family
as Qlib's US index collector but does not modify Qlib.  It accepts a single
frozen HTML revision, identifies the current and historical-change tables by
semantic headers (including merged headers), and fails closed on ambiguity.

Membership intervals are half-open: `[start, end)`. A trading session is active
when `start <= session < end`; both bounds are the source-reported effective
dates. The reconstruction rolls a validated terminal constituent set backward,
then replays changes forward. Symbol mapping is a separate versioned artifact;
dot/dash format changes and corporate aliases are explicit rather than silent
historical rewrites.

The CLI only writes compact JSON evidence outside Git. It never downloads price
data, trains a model, predicts, calculates returns, or inspects performance.

```text
python -m sp500_pit.cli reconstruct --html <frozen.html> --out <evidence-dir> \
  --cutoff 2024-12-31 --source-url <url> --retrieved-at <timestamp> --revision-id <id>
```
