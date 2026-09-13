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

The leaf also owns one SHA-256-frozen declarative authority artifact,
`accepted_provider_binding_facts.json`. Its 12 facts bind an exact accepted
PIT episode to one exact provider and provider asset for one exact half-open
date interval. The loader rejects altered bytes, another schema or count,
duplicate episode/provider bindings, invalid intervals or evidence hashes,
and any scope other than `PROVIDER_BINDING_ONLY`. These facts contain no
membership or price rows and cannot authorize forward fill, synthetic rows,
successor-price substitution, or ticker/name/price-continuity inference.

Authority is applied through DuckDB's episode/provider/asset/date-valid join.
It can make only the exact candidate identity-supported; coverage remains an
independent required-session anti-join result. In particular, the accepted
ARNC/HWM binding retains 1,323 required sessions, 868 observed sessions, and
455 missing sessions.

Exactly two thin provider translations exist in `providers.py`. Their
`AnnotatedResult` metadata retains provider, provider asset identifier,
provider symbol, adjustment semantics, and the source-observation content
hash. No AQ provider registry, router, normalizer, HTTP/retry/cache framework,
security master, or relational engine exists.

Identity and required-session price coverage are separate, orthogonal facts.
Identity has these states:

```text
PROVIDER_BINDING_AUTHORIZED
PROVIDER_BINDING_AMBIGUOUS
PROVIDER_BINDING_NOT_AVAILABLE
```

Coverage has these states and is evaluated only for a uniquely authorized
identity:

```text
COMPLETE_PROVIDER_COVERAGE
ZERO_PROVIDER_COVERAGE
PARTIAL_PROVIDER_COVERAGE
COVERAGE_NOT_EVALUATED
```

The compatibility decision output combines them without hiding partial
coverage:

```text
PROVIDER_BINDING_AUTHORIZED
PROVIDER_BINDING_AMBIGUOUS
PROVIDER_BINDING_NOT_AVAILABLE
KNOWN_PROVIDER_GAP_CANDIDATE
PARTIAL_PROVIDER_COVERAGE
```

Every unique required episode produces exactly one decision. Missing, partial,
duplicate, or out-of-episode required-session input fails closed as an identity
ambiguity. This is distinct from complete required-session input accompanied by
partial provider observations, which returns `PARTIAL_PROVIDER_COVERAGE` and is
fail-closed for certification readiness. Coverage is computed from the exact
required-session anti-join, not total observations in the episode interval. A
missing session relation can never make an episode disappear from the decision
output.

Tests use synthetic relations only. Real provider payloads, credentials,
private market data, and SEC document content remain outside Git.

From this directory, using the isolated validated POC environment:

```text
python -m unittest discover -s tests -v
python -m compileall -q aq_market_data_binding tests
```
