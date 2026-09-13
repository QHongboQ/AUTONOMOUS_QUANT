# P2 free upstream market-data binding

This leaf owns provider observations, provider compatibility, provider-to-PIT
episode binding, provenance, and price coverage. The sibling S&P 500 PIT leaf
continues to own membership, identity, and InstrumentEpisode facts; this leaf
consumes only its thin public episode relation and does not duplicate facts.

Upstream ownership is strict:

- OpenBB Core supplies the EquityHistorical Standard Model and Fetcher API.
- Quantiacs and SimFin retain native transport/access ownership.
- OpenFIGI is supporting identity evidence only; `tts-*` remains a Quantiacs
  provider identifier and is never a FIGI.
- edgartools owns SEC retrieval/parsing. AQ retains only decision metadata.
- Pandera validates relation boundaries; DuckDB owns interval and anti joins,
  duplicates, uniqueness, conflicts, coverage, and unresolved inventories.
- AQ supplies only project-specific fail-closed acceptance policy.

Exactly two thin provider translations exist in `providers.py`. Their
`AnnotatedResult` metadata retains provider, provider asset identifier,
provider symbol, adjustment semantics, and the source-observation content
hash. No AQ provider registry, router, normalizer, HTTP/retry/cache framework,
security master, or relational engine exists.

The output states remain distinct:

```text
PROVIDER_BINDING_AUTHORIZED
PROVIDER_BINDING_AMBIGUOUS
PROVIDER_BINDING_NOT_AVAILABLE
KNOWN_PROVIDER_GAP_CANDIDATE
```

Every unique required episode produces exactly one decision. Missing, partial,
duplicate, or out-of-episode required-session input fails closed as
`PROVIDER_BINDING_AMBIGUOUS`; a missing session relation can never make an
episode disappear from the decision output.

Tests use synthetic relations only. Real provider payloads, credentials,
private market data, and SEC document content remain outside Git.

From this directory, using the isolated validated POC environment:

```text
python -m unittest discover -s tests -v
python -m compileall -q aq_market_data_binding tests
```
