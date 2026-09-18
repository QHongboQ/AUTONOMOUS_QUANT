# Episode-to-SEC-CIK binding

`EpisodeSecCikBindingV1` is the thin, immutable bridge between a full P1
`InstrumentEpisodeV1` identity and a date-bounded SEC filer CIK. Admission
requires the exact P1 episode ID and an interval contained by that episode.

The public contract contains exactly seven fields. Its `binding_id` is SHA-256
over the RFC 8785 canonical JSON representation of the other six fields; the
evidence list order is authoritative and is never sorted. Only `PASS_EXACT`
and `PASS_CORROBORATED` are admissible classifications.

This component does not resolve tickers, crawl SEC data, infer corporate
lineage, or maintain a security master. A current ticker lookup or a bounded
P2 window episode ID cannot substitute for full P1 episode authority.

Intervals use `[valid_from, valid_to)` semantics. A binding set may contain
non-overlapping intervals, but any overlap for one episode fails closed,
including overlaps that repeat the same CIK. Coverage reporting is descriptive
only (`FULL`, `PARTIAL`, or `UNBOUND`) and never creates authority.
