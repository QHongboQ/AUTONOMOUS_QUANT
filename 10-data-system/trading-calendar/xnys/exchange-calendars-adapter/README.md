# XNYS exchange_calendars adapter

This leaf owns only XNYS trading-session semantics for the bounded P1 domain.
It pins `exchange_calendars==4.13.2` and exposes ISO-string primitives for
session membership, directional date resolution, adjacent sessions, and
inclusive session ranges.

The adapter deliberately exposes no pandas or upstream calendar objects. Its
calendar construction uses fixed `2000-01-01` through `2035-12-31` bounds so
results do not depend on the wall clock. Invalid dates, unsupported directions,
non-session inputs where a session is required, and dates outside that range
fail closed with `ValueError`.

This leaf does not own index membership, security identity, market data,
certification, portfolio logic, execution, or trading. The current PIT runtime
contains no custom session-conversion logic to replace, so integration is
intentionally deferred until a real consumer requires this contract.

Install the exact leaf dependency in an isolated environment and run:

```text
python -m unittest discover -s tests -v
```
