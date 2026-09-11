"""Evidence-backed materialization for the accepted 2010-2024 reconciliation.

All ticker-specific facts in this module are declarative evidence data.  The
runtime algorithms remain generic and live in overlays.py, fja_sp500.py and
compiler.py.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from .canonical import canonical_bytes, deterministic_id, sha256_hex
from .compiler import compile_universe
from .contracts import (
    AmbiguityState,
    CompilationResultV1,
    CompilePolicyV1,
    FindingSeverity,
    FindingType,
    IndexMembershipEventV1,
    InstrumentEpisodeV1,
    OverlayOperation,
    ReviewState,
    SessionBoundary,
    SnapshotObservationV1,
    SourceManifestV1,
    SourceRole,
    TickerEpisodeOverlayV1,
    TickerIdentityEventV1,
)
from .overlays import ResolvedObservation, apply_ticker_overlays
from .sources.fja_sp500 import (
    build_reconciled_membership_event_manifest,
    derive_reconciled_membership_events,
)
from .validation import (
    AmbiguousTickerEpisodeError,
    lookup_episode,
    validate_terminal_set,
    validate_year_continuity,
)


AUDIT_REVISION = "AUTONOMOUS-QUANT-P1-PIT-RECONCILIATION-EVIDENCE-AUDIT-001"
RETRIEVED_AT = "2026-09-10T00:00:00Z"
WINDOW_END_EXCLUSIVE = "2025-01-01"


@dataclass(frozen=True, slots=True)
class EvidenceSpec:
    evidence_id: str
    publisher: str
    title: str
    evidence_date: str
    url: str


@dataclass(frozen=True, slots=True)
class IdentitySpec:
    old_ticker: str
    new_ticker: str
    announcement_date: str | None
    effective_session: str
    evidence_id: str


@dataclass(frozen=True, slots=True)
class OverlayCaseSpec:
    case_id: str
    old_ticker: str
    new_ticker: str
    effective_session: str
    start_session: str | None = None


@dataclass(frozen=True, slots=True)
class FindingResolutionSpec:
    finding_id: str
    final_resolution: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReconciliationBundle:
    evidence_manifests: tuple[SourceManifestV1, ...]
    identity_events: tuple[TickerIdentityEventV1, ...]
    overlays: tuple[TickerEpisodeOverlayV1, ...]
    resolved_observations: tuple[ResolvedObservation, ...]
    reconciled_manifest: SourceManifestV1
    membership_events: tuple[IndexMembershipEventV1, ...]
    compilation: CompilationResultV1
    resolved_ledger: tuple[dict[str, object], ...]
    gate_results: dict[str, object]


EVIDENCE_SPECS = (
    EvidenceSpec("E01", "SAIC / S&P DJI", "SAIC spin-off and S&P index changes", "2013-09-11", "https://www.sec.gov/Archives/edgar/data/353394/000119312513362164/d595478dex991.htm"),
    EvidenceSpec("E02", "Aptiv / S&P DJI", "Delphi separation and Aptiv continuity", "2017-12-04", "https://www.sec.gov/Archives/edgar/data/1707092/000119312517364954/d494581d8k.htm"),
    EvidenceSpec("E03", "Capri Holdings", "Capri name and ticker change", "2018-12-31", "https://www.sec.gov/Archives/edgar/data/1530721/000119312518362322/d653406d8k.htm"),
    EvidenceSpec("E04", "IQVIA / S&P DJI", "IQVIA name and ticker change", "2017-11-06", "https://www.sec.gov/Archives/edgar/data/1478242/000119312517335879/d484556d8k.htm"),
    EvidenceSpec("E05", "L3Harris / S&P DJI", "L3Harris merger completion and index continuity", "2019-07-01", "https://investors.l3harris.com/news/news-details/2019/L3Harris-Technologies-Merger-Successfully-Completed-Board-of-Directors-Leadership-and-Organization-Structure-Announced-07-01-2019/default.aspx"),
    EvidenceSpec("E06", "Healthpeak Properties", "HCP name and ticker change", "2019-10-30", "https://www.sec.gov/Archives/edgar/data/765880/000162828019012829/ex9919302019.htm"),
    EvidenceSpec("E07", "Jacobs", "Jacobs begins trading as J", "2019-12-10", "https://www.jacobs.com/newsroom/press-release/jacobs-begins-trading-today-j-celebrates-30th-anniversary-nyse"),
    EvidenceSpec("E08", "Willis Towers Watson", "Nasdaq ticker change to WTW", "2022-01-07", "https://investors.wtwco.com/news-releases/news-release-details/willis-towers-watson-announces-nasdaq-ticker-symbol-change-wltw"),
    EvidenceSpec("E09", "Ball Corporation", "Ball ticker change to BALL", "2022-05-03", "https://www.sec.gov/Archives/edgar/data/9389/000000938922000010/bll-20220427x8k.htm"),
    EvidenceSpec("E10", "Dayforce", "CDAY ceased and DAY began", "2024-02-01", "https://www.sec.gov/Archives/edgar/data/1725057/000095017024009619/day-20240131.htm"),
    EvidenceSpec("E11", "Corpay", "Corpay rebrand and CPAY ticker", "2024-03-07", "https://www.sec.gov/Archives/edgar/data/1175454/000162828024010593/exhibit991corpayrebrand_re.htm"),
    EvidenceSpec("E12", "Baker Hughes", "BKR trading commencement", "2019-10-18", "https://www.sec.gov/Archives/edgar/data/1701605/000170160520000019/fiscalyear2019form10-k.htm"),
    EvidenceSpec("E13", "Trane Technologies / S&P DJI", "Old IR becomes TT and new IR joins", "2020-02-27", "https://press.spglobal.com/2020-02-27-Gardner-Denver-Holdings-Set-to-Join-S-P-500-Cimarex-Energy-to-Join-S-P-MidCap-400"),
    EvidenceSpec("E14", "Paramount Global", "PARAA and PARA trading commencement", "2022-02-16", "https://www.sec.gov/Archives/edgar/data/813828/000081382822000011/viac-20220216.htm"),
    EvidenceSpec("E15", "Everest Group", "Everest rebrand and EG ticker", "2023-05-18", "https://investors.everestglobal.com/news/news-details/2023/Everest-to-Rebrand-Company-Name-and-NYSE-Ticker-to-Reflect-its-Evolution-Global-Growth-and-Diversification-Strategy/default.aspx"),
    EvidenceSpec("E16", "Meta Platforms", "META ticker effective before market open", "2022-05-31", "https://www.sec.gov/Archives/edgar/data/1326801/000132680122000070/may312022-exhibit991.htm"),
    EvidenceSpec("E17", "AGL Resources", "AGL-Nicor merger and GAS ticker assumption", "2011-12-09", "https://www.sec.gov/Archives/edgar/data/72020/000011010411000028/exhibit_99-1.htm"),
    EvidenceSpec("E18", "S&P DJI", "Constellation removal and later spin-off addition", "2022-01-26", "https://press.spglobal.com/2022-01-26-Constellation-Energy-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600"),
    EvidenceSpec("E19", "T-Mobile US / S&P DJI", "PCS combination and later TMUS addition", "2019-07-09", "https://press.spglobal.com/2019-07-09-T-Mobile-US-Set-to-Join-S-P-500"),
    EvidenceSpec("E20", "S&P DJI", "AMD removal and re-entry", "2017-03-10", "https://press.spglobal.com/2017-03-10-S-P-Dow-Jones-Indices-Announces-Changes-to-U-S-Indices-and-Updates-to-U-S-Indices-Methodology-and-Market-Cap-Guidelines"),
    EvidenceSpec("E21", "S&P DJI", "Leidos re-entry", "2019-08-01", "https://press.spglobal.com/2019-08-01-Leidos-Holdings-IDEX-Set-to-Join-S-P-500-Grubhub-Foot-Locker-to-Join-S-P-MidCap-400-National-Beverage-to-Join-S-P-SmallCap-600"),
    EvidenceSpec("E22", "S&P DJI", "Dell going-private removal and Dell Technologies addition", "2024-09-06", "https://press.spglobal.com/2024-09-06-Palantir-Technologies,-Dell-Technologies,-and-Erie-Indemnity-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600"),
    EvidenceSpec("E23", "S&P DJI", "Teradyne exit and re-entry", "2020-09-04", "https://press.spglobal.com/2020-09-04-Etsy-Teradyne-and-Catalent-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600"),
    EvidenceSpec("E24", "S&P DJI", "Jabil exit and re-entry", "2023-12-01", "https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20231201-1467851/1467851_dec2023shuf.pdf"),
    EvidenceSpec("E25", "DXC Technology / S&P DJI", "DXC transaction and membership change", "2017-04-03", "https://www.sec.gov/Archives/edgar/data/1688568/000119312517112036/d250548d8k.htm"),
    EvidenceSpec("E26", "S&P DJI", "First Solar exit and re-entry", "2022-12-12", "https://press.spglobal.com/2022-12-12-First-Solar-Set-to-Join-S-P-500-Fortune-Brands-Innovations-to-Join-S-P-MidCap-400-MasterBrand-to-Join-S-P-SmallCap-600"),
    EvidenceSpec("E27", "S&P DJI", "DowDuPont combination and successor additions", "2019-05-28", "https://press.spglobal.com/2019-05-28-Corteva-Set-to-Join-S-P-500-Fluor-to-Join-S-P-MidCap-400-and-Realogy-and-Bloomin-Brands-to-Join-S-P-SmallCap-600"),
    EvidenceSpec("E28", "S&P DJI / Keurig Dr Pepper", "DPS removal, KDP identity, and later addition", "2022-06-03", "https://press.spglobal.com/2022-06-03-Keurig-Dr-Pepper,-VICI-Properties-and-ON-Semiconductor-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400,-and-S-P-SmallCap-600"),
    EvidenceSpec("E29", "S&P DJI", "EQT exit and re-entry", "2022-09-23", "https://press.spglobal.com/2022-09-23-PG-E-and-EQT-Set-to-Join-S-P-500-ExlService-to-Join-S-P-MidCap-400-Others-to-Join-S-P-SmallCap-600"),
    EvidenceSpec("E30", "S&P DJI", "PG&E exit and re-entry", "2022-09-23", "https://press.spglobal.com/2022-09-23-PG-E-and-EQT-Set-to-Join-S-P-500-ExlService-to-Join-S-P-MidCap-400-Others-to-Join-S-P-SmallCap-600"),
)


IDENTITY_SPECS = (
    IdentitySpec("SAI", "LDOS", "2013-09-09", "2013-09-30", "E01"),
    IdentitySpec("DLPH", "APTV", "2017-11-28", "2017-12-05", "E02"),
    IdentitySpec("KORS", "CPRI", "2018-12-31", "2019-01-02", "E03"),
    IdentitySpec("Q", "IQV", "2017-11-06", "2017-11-15", "E04"),
    IdentitySpec("HRS", "LHX", "2019-06-24", "2019-07-01", "E05"),
    IdentitySpec("HCP", "PEAK", "2019-10-30", "2019-11-05", "E06"),
    IdentitySpec("JEC", "J", "2019-11-25", "2019-12-10", "E07"),
    IdentitySpec("WLTW", "WTW", "2022-01-07", "2022-01-10", "E08"),
    IdentitySpec("BLL", "BALL", "2022-04-27", "2022-05-10", "E09"),
    IdentitySpec("CDAY", "DAY", "2024-01-22", "2024-02-01", "E10"),
    IdentitySpec("FLT", "CPAY", "2024-03-07", "2024-03-25", "E11"),
    IdentitySpec("BHGE", "BKR", "2019-10-17", "2019-10-18", "E12"),
    IdentitySpec("IR", "TT", "2020-02-27", "2020-03-03", "E13"),
    IdentitySpec("VIAC", "PARA", "2022-02-15", "2022-02-17", "E14"),
    IdentitySpec("RE", "EG", "2023-05-18", "2023-07-10", "E15"),
    IdentitySpec("FB", "META", "2022-05-31", "2022-06-09", "E16"),
    IdentitySpec("AGL", "GAS", "2011-12-09", "2011-12-16", "E17"),
    IdentitySpec("PCS", "TMUS", "2013-04-24", "2013-05-01", "E19"),
    IdentitySpec("CSC", "DXC", "2017-03-28", "2017-04-03", "E25"),
    IdentitySpec("DPS", "KDP", "2018-06-25", "2018-07-10", "E28"),
)


OVERLAY_CASE_SPECS = (
    OverlayCaseSpec("O1", "SAI", "LDOS", "2013-09-30"),
    OverlayCaseSpec("O2", "DLPH", "APTV", "2017-12-05"),
    OverlayCaseSpec("O3", "KORS", "CPRI", "2019-01-02"),
    OverlayCaseSpec("O4", "Q", "IQV", "2017-11-15"),
    OverlayCaseSpec("O5", "HRS", "LHX", "2019-07-01"),
    OverlayCaseSpec("O6", "AGL", "GAS", "2011-12-16", "2011-12-13"),
    OverlayCaseSpec("O7", "PCS", "TMUS", "2013-05-01"),
    OverlayCaseSpec("O8", "CSC", "DXC", "2017-04-03"),
    OverlayCaseSpec("O9", "DPS", "KDP", "2018-07-10"),
)


# Canonical ledger identity is retained verbatim.  Values are the accepted
# principal classifications and evidence packages from the two read-only audits.
FINDING_RESOLUTIONS = (
    ("4832f5f16e7010888c70c73c7422cc0c8cc1143a16056d8e1e66298c93b287fb", "SOURCE_BACKFILL", ("E01",)),
    ("f22b3e08be015d9a35779e72e65aa7eda0578671f7996f8ca61eaeef772f4e1a", "SOURCE_BACKFILL", ("E02",)),
    ("7e41f91402a63331e6a83cf02687f62b65cdf4f01080dba62e38af33451aa4a3", "SOURCE_BACKFILL", ("E03",)),
    ("19ba9629a68b280c4b3a79e9c000632add44af2bfc969cdb2c53b52c090e7f82", "SOURCE_BACKFILL", ("E04",)),
    ("c97580aea4add50bdba8f674bc44727a979b99d3b082cb27ab222a0f631aa9ae", "SOURCE_BACKFILL", ("E05",)),
    ("d60dccba136042ea9451a84e0b11ac9be793a8073db3907980f1863a89de1779", "FALSE_DIAGNOSTIC_BOUNDARY", ("E06",)),
    ("88132abda2ee4f905b3baa835415fbdb1b45f5307ab332172143b1139b9de84c", "FALSE_DIAGNOSTIC_BOUNDARY", ("E07",)),
    ("441793fb26c1082d6f85f4f526ba7db58940a21c15db6c0b1b04a735176e9d01", "FALSE_DIAGNOSTIC_BOUNDARY", ("E08",)),
    ("5b72c2b6e24abc909949ebe589aa97b798bec714f49f4bb5cb2d3c5906b8635c", "FALSE_DIAGNOSTIC_BOUNDARY", ("E09",)),
    ("dee00eb7ebb9ba75dcfa98d1dea474edd56d4abc4f32fcabdcd1dd6bc3c60a4a", "FALSE_DIAGNOSTIC_BOUNDARY", ("E10",)),
    ("a557f491e80c76a4331d18db2029ae35092c1764755491169330283124bcffd2", "FALSE_DIAGNOSTIC_BOUNDARY", ("E11",)),
    ("103b09784924f53fdb8707681ce657701f66666e05462f2475b27ed003d2a753", "FALSE_DIAGNOSTIC_BOUNDARY", ("E12",)),
    ("b059daaf24be8a6f5f8e1ee5a45e39a5c7fc1466cbcf341c8ef0af7c50f9fc14", "CORPORATE_SUCCESSION_NOT_MEMBERSHIP_TRANSFER", ("E13",)),
    ("449a816300c71f8097a9313d8d2faf34592e42a29e7af6f472187d1b43c9750b", "FALSE_DIAGNOSTIC_BOUNDARY", ("E14",)),
    ("5c04d73b193384e73172f589ecac80b267d0c2a270d4895563c830035d653084", "FALSE_DIAGNOSTIC_BOUNDARY", ("E15",)),
    ("522d3241c86c63c26182aec1a95b62428d2947d8b36b6d4082bb5605bcb7cf19", "GENUINE_RENAME", ("E16",)),
    ("3e0ce479f4121e28f93f9e9c8e3edac006ab91e7f7684074d9e4118a8e9ea465", "GENUINE_RENAME", ("E10",)),
    ("c4b25345aadff7227b91e5092d2c4b904354e21bdf60f462ed24c946fba74c3c", "GENUINE_RENAME", ("E15",)),
    ("931b474f3462d03170621e8d228b92c862015b1da691272de064358376a7eb8d", "GENUINE_RENAME", ("E08",)),
    ("a1664780869b02c59476233d533218a7bf8454327a8704e6f3d07a4776eb2b30", "GENUINE_RENAME", ("E03",)),
    ("81f0f029cc63a8d30210ea377bcebf05fe0570768fa61a0cea2d202eb79ba936", "GENUINE_RENAME", ("E04",)),
    ("13c91636c5f12f09f492000efdfa9d9fabcfa58de8456a7b64085d3d4568cbe6", "GENUINE_RENAME", ("E02",)),
    ("d2c78dbe3d19dbfca5669058cec625a1382a6653b4e522c95256900c958ebd61", "TICKER_REUSE", ("E17",)),
    ("0c5dd15b5a0c049f939527ff82b06b11ec7a2701ff2ded503c57e038f0b132f2", "TICKER_REUSE", ("E18",)),
    ("9972512c4c6784543dc5eb26734b7255c048d17a15bc3b5bc9220c9aeb18ff2e", "SOURCE_BACKFILL", ("E19",)),
    ("d8096ff68bc626fc649aa1eb54b26671125cdbf9b4fb138c9cafd81cd6ccbc6b", "MEMBERSHIP_EXIT_REENTRY", ("E20",)),
    ("8ec7ed1a227bc23aef5aa87064cf3dcafc8f9fb004e0ee600f253eda1e6833ed", "MEMBERSHIP_EXIT_REENTRY", ("E01", "E21")),
    ("6a656f6ef13c4b4ec6d7f8c981c6299754c8037b2862e5c345e0be9b47e55677", "TICKER_REUSE", ("E22",)),
    ("b09b3debff19aefca8369b4b73ebfc3dae7e01bc553ab71df3ba4f6ce4f66c42", "MEMBERSHIP_EXIT_REENTRY", ("E23",)),
    ("167ee0808a0607a7bcdcb76135162002a9f8e8d87fcaba144751709bd3e9387d", "MEMBERSHIP_EXIT_REENTRY", ("E24",)),
    ("b626d89eb166dac347db75d969469dd6b7477f132313cc0ffe338f30d054d54a", "SOURCE_BACKFILL", ("E25",)),
    ("6f89c374b9ed230ea97a69edc681dcfcd5545d767cf759bee2a30e7d8bdbd1ea", "MEMBERSHIP_EXIT_REENTRY", ("E26",)),
    ("92a6c588a12026d6195c11662af17d4e66d3781ade7dbde062b8d69287d3f991", "TICKER_REUSE", ("E27",)),
    ("4feeeb2a7244454e92d75ef7239ced53e9d8632cf1b2050a6c6edbaa360db3eb", "TICKER_REUSE", ("E27",)),
    ("06878b168814b1de994e992ba34248011ec4174784948f518149590449cd159c", "SOURCE_BACKFILL", ("E28",)),
    ("fd4e1677129e8b0bc7e0d1053eb022a6a9bd32b2de48a8b6cbe6f88fce3f9334", "MEMBERSHIP_EXIT_REENTRY", ("E29",)),
    ("9e335320d7d71faecd774732e6133d30ba30c5c3eea45e55f270ee7fcf27c2d5", "MEMBERSHIP_EXIT_REENTRY", ("E30",)),
)


def build_evidence_manifests() -> tuple[SourceManifestV1, ...]:
    identity_evidence = {item.evidence_id for item in IDENTITY_SPECS}
    result = []
    for spec in EVIDENCE_SPECS:
        logical = {
            "audit_revision": AUDIT_REVISION,
            "evidence_id": spec.evidence_id,
            "publisher": spec.publisher,
            "title": spec.title,
            "evidence_date": spec.evidence_date,
            "url": spec.url,
        }
        digest = sha256_hex(logical)
        result.append(SourceManifestV1(
            source_id=deterministic_id("P1SRC-", logical),
            source_role=(
                SourceRole.TICKER_IDENTITY_EVIDENCE
                if spec.evidence_id in identity_evidence
                else SourceRole.OFFICIAL_CONFLICT_RESOLUTION
            ),
            source_type="accepted_primary_evidence_package_locator",
            source_url_or_repo=spec.url,
            source_commit_or_revision=spec.evidence_date,
            retrieved_at=RETRIEVED_AT,
            media_type="application/vnd.aq.pit-evidence-locator+json",
            byte_length=len(canonical_bytes(logical)),
            sha256=digest,
            license_observation="not assessed; official evidence locator only",
            coverage_start=spec.evidence_date,
            coverage_end=spec.evidence_date,
            ancestry=(),
            adapter_version="accepted-reconciliation-evidence-audit-v1",
        ))
    return tuple(result)


def build_identity_events(
    evidence_manifests: tuple[SourceManifestV1, ...],
) -> tuple[TickerIdentityEventV1, ...]:
    source_by_evidence = {
        spec.evidence_id: manifest
        for spec, manifest in zip(EVIDENCE_SPECS, evidence_manifests)
    }
    result = []
    for spec in IDENTITY_SPECS:
        source = source_by_evidence[spec.evidence_id]
        logical = {
            "old_ticker": spec.old_ticker,
            "new_ticker": spec.new_ticker,
            "announcement_date": spec.announcement_date,
            "effective_session": spec.effective_session,
            "evidence_id": spec.evidence_id,
            "evidence_hash": source.sha256,
        }
        result.append(TickerIdentityEventV1(
            event_id=deterministic_id("P1TID-", logical),
            old_ticker=spec.old_ticker,
            new_ticker=spec.new_ticker,
            announcement_date=spec.announcement_date,
            effective_date=spec.effective_session,
            effective_session=spec.effective_session,
            boundary_semantics=SessionBoundary.EFFECTIVE_SESSION,
            source_id=source.source_id,
            evidence_hash=source.sha256,
            identity_anchor=deterministic_id("P1ANCHOR-", logical),
            ambiguity_state=AmbiguityState.CLEAR,
        ))
    return tuple(result)


def build_overlays(
    observations: tuple[SnapshotObservationV1, ...],
    identity_events: tuple[TickerIdentityEventV1, ...],
) -> tuple[TickerEpisodeOverlayV1, ...]:
    event_by_key = {
        (item.old_ticker, item.new_ticker, item.effective_session): item
        for item in identity_events
    }
    result = []
    for case in OVERLAY_CASE_SPECS:
        event = event_by_key[(case.old_ticker, case.new_ticker, case.effective_session)]
        for observation in observations:
            if observation.effective_session >= case.effective_session:
                continue
            if case.start_session is not None and observation.effective_session < case.start_session:
                continue
            if case.new_ticker not in observation.tickers:
                continue
            operation = (
                OverlayOperation.DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY
                if case.old_ticker in observation.tickers
                else OverlayOperation.MAP_SUCCESSOR_TO_PREDECESSOR
            )
            logical = {
                "case_id": case.case_id,
                "raw_observation_id": observation.observation_id,
                "ticker_identity_event_id": event.event_id,
                "operation": operation,
                "effective_session": case.effective_session,
            }
            result.append(TickerEpisodeOverlayV1(
                overlay_id=deterministic_id("P1OVR-", logical),
                raw_observation_id=observation.observation_id,
                ticker_identity_event_id=event.event_id,
                effective_session=case.effective_session,
                operation=operation,
                reason=f"accepted evidence-backed reconciliation overlay {case.case_id}",
                evidence_hashes=(observation.evidence_hash, event.evidence_hash),
                review_state=ReviewState.ACCEPTED,
            ))
    return tuple(sorted(result, key=lambda item: item.overlay_id))


def _finding_rows(
    historical_ledger: tuple[dict[str, object], ...],
    evidence_manifests: tuple[SourceManifestV1, ...],
    identity_events: tuple[TickerIdentityEventV1, ...],
    overlays: tuple[TickerEpisodeOverlayV1, ...],
    episodes: tuple[InstrumentEpisodeV1, ...],
) -> tuple[dict[str, object], ...]:
    history = {str(item["finding_id"]): item for item in historical_ledger}
    evidence_sources = {
        spec.evidence_id: manifest.source_id
        for spec, manifest in zip(EVIDENCE_SPECS, evidence_manifests)
    }
    event_by_evidence = {
        spec.evidence_id: event.event_id
        for spec, event in zip(IDENTITY_SPECS, identity_events)
    }
    overlays_by_event: dict[str, list[str]] = {}
    for overlay in overlays:
        overlays_by_event.setdefault(overlay.ticker_identity_event_id, []).append(overlay.overlay_id)
    rows = []
    for suffix, resolution, evidence_ids in FINDING_RESOLUTIONS:
        finding_id = f"P1UNRES-{suffix}"
        original = history.get(finding_id)
        if original is None:
            raise ValueError(f"canonical historical finding missing: {finding_id}")
        tickers = tuple(str(item) for item in original["tickers"])
        runtime_ids: set[str] = set()
        for evidence_id in evidence_ids:
            event_id = event_by_evidence.get(evidence_id)
            if event_id:
                runtime_ids.add(event_id)
                runtime_ids.update(overlays_by_event.get(event_id, ()))
        runtime_ids.update(
            item.episode_id for item in episodes
            if item.normalized_ticker in tickers
        )
        rows.append({
            "finding_id": finding_id,
            "original_type": original["finding_type"],
            "ticker_or_pair": tickers,
            "final_resolution": resolution,
            "evidence_ids": evidence_ids,
            "evidence_source_ids": tuple(evidence_sources[item] for item in evidence_ids),
            "runtime_object_ids": tuple(sorted(runtime_ids)),
            "resolution_state": "RESOLVED",
            "blocking_after_implementation": "NO",
        })
    if len(rows) != 37 or len({item["finding_id"] for item in rows}) != 37:
        raise ValueError("resolved ledger must contain 37 unique canonical findings")
    return tuple(sorted(rows, key=lambda item: str(item["finding_id"])))


def _year_continuity_findings(
    resolved: tuple[ResolvedObservation, ...],
    membership_events: tuple[IndexMembershipEventV1, ...],
    identity_events: tuple[TickerIdentityEventV1, ...],
) -> tuple[object, ...]:
    ordered = tuple(sorted(
        resolved, key=lambda item: (item.effective_session, item.observation_id),
    ))
    findings = []
    for year in range(2010, 2024):
        prior = [item for item in ordered if item.effective_session.startswith(f"{year}-")][-1]
        following = [item for item in ordered if item.effective_session.startswith(f"{year + 1}-")][0]
        roster = set(prior.tickers)
        identities = sorted(
            (
                item for item in identity_events
                if prior.effective_session < item.effective_session <= following.effective_session
            ),
            key=lambda item: (item.effective_session, item.event_id),
        )
        for identity in identities:
            if identity.old_ticker in roster:
                roster.remove(identity.old_ticker)
                roster.add(identity.new_ticker)
        boundary = [
            item for item in membership_events
            if prior.effective_session < item.effective_session <= following.effective_session
        ]
        for event in sorted(
            boundary,
            key=lambda item: (
                item.effective_session,
                0 if item.action.value == "REMOVE" else 1,
                item.event_id,
            ),
        ):
            if event.action.value == "REMOVE":
                roster.discard(event.source_ticker)
            else:
                roster.add(event.source_ticker)
        findings.extend(validate_year_continuity(roster, following.tickers, (item.event_id for item in boundary)))
    return tuple(findings)


def build_reconciliation(
    *,
    seed_manifest: SourceManifestV1,
    observations: tuple[SnapshotObservationV1, ...],
    historical_ledger: tuple[dict[str, object], ...],
    terminal_roster: tuple[str, ...],
) -> ReconciliationBundle:
    evidence_manifests = build_evidence_manifests()
    identity_events = build_identity_events(evidence_manifests)
    overlays = build_overlays(observations, identity_events)
    application = apply_ticker_overlays(observations, identity_events, overlays)
    reconciled_manifest = build_reconciled_membership_event_manifest(
        seed_manifest, observations, application.observations, identity_events, overlays,
    )
    membership_events = derive_reconciled_membership_events(
        observations,
        application.observations,
        identity_events,
        reconciled_manifest,
        seed_manifest=seed_manifest,
        overlays=overlays,
    )
    policy = CompilePolicyV1(
        "SP500", observations[0].effective_session, WINDOW_END_EXCLUSIVE,
        "FJA-source-session-calendar-v1", "p1-evidence-backed-reconciliation-v1",
    )
    compilation = compile_universe(
        policy=policy,
        manifests=(seed_manifest, *evidence_manifests, reconciled_manifest),
        observations=observations,
        membership_events=membership_events,
        ticker_events=identity_events,
        overlays=overlays,
    )
    unresolved = tuple(
        item for item in compilation.findings
        if item.severity in {FindingSeverity.ERROR, FindingSeverity.CRITICAL}
    )
    terminal_findings = validate_terminal_set(
        max(application.observations, key=lambda item: item.effective_session).tickers,
        terminal_roster,
        (seed_manifest.source_id,),
    )
    continuity_findings = _year_continuity_findings(
        application.observations, membership_events, identity_events,
    )
    member_counts = tuple(len(item.tickers) for item in application.observations)
    duplicate_event_keys = {
        (item.effective_session, item.action.value, item.source_ticker)
        for item in membership_events
    }
    duplicate_events = len(duplicate_event_keys) != len(membership_events)
    finding_counts = {
        kind: sum(item.finding_type is kind for item in compilation.findings)
        for kind in FindingType
    }
    episode_groups: dict[str, list[InstrumentEpisodeV1]] = {}
    for episode in compilation.episodes:
        episode_groups.setdefault(episode.normalized_ticker, []).append(episode)
    ambiguous_reuse_failures = 0
    for ticker, matches in episode_groups.items():
        if len(matches) < 2:
            continue
        try:
            lookup_episode(compilation.episodes, ticker)
        except AmbiguousTickerEpisodeError:
            continue
        ambiguous_reuse_failures += 1
    ledger = _finding_rows(
        historical_ledger, evidence_manifests, identity_events, overlays, compilation.episodes,
    )
    gates = {
        "year_continuity": "PASS" if not continuity_findings else "FAIL",
        "member_count_sanity": "PASS" if min(member_counts) >= 490 and max(member_counts) <= 510 else "FAIL",
        "member_count_min": min(member_counts),
        "member_count_max": max(member_counts),
        "duplicate_membership_event": "FAIL" if duplicate_events else "PASS",
        "duplicate_event_count": finding_counts[FindingType.DUPLICATE_EVENT],
        "duplicate_episode": "PASS" if len({item.episode_id for item in compilation.episodes}) == len(compilation.episodes) else "FAIL",
        "duplicate_episode_count": finding_counts[FindingType.DUPLICATE_EPISODE],
        "overlap_count": finding_counts[FindingType.OVERLAPPING_TICKER_EPISODES],
        "future_ticker_count": finding_counts[FindingType.FUTURE_TICKER_BEFORE_RENAME],
        "stale_predecessor_count": finding_counts[FindingType.STALE_OLD_TICKER_AFTER_RENAME],
        "ticker_reuse_ambiguity": "PASS" if ambiguous_reuse_failures == 0 else "FAIL",
        "add_present_count": finding_counts[FindingType.ADD_PRESENT],
        "remove_absent_count": finding_counts[FindingType.REMOVE_ABSENT],
        "unresolved_correction_count": finding_counts[FindingType.UNRESOLVED_CORRECTION],
        "terminal_exact_set": "PASS" if not terminal_findings else "FAIL",
        "terminal_set_difference_count": len(
            set(max(application.observations, key=lambda item: item.effective_session).tickers)
            ^ set(terminal_roster)
        ),
        "source_provenance_authority": "PASS" if not unresolved else "FAIL",
        "unresolved_error_count": sum(item.severity is FindingSeverity.ERROR for item in unresolved),
        "unresolved_critical_count": sum(item.severity is FindingSeverity.CRITICAL for item in unresolved),
        "invalid_overlay_authority_count": len(application.findings),
        "invalid_reconciled_derivation_context_count": finding_counts[FindingType.INVALID_AUTHORITY_REFERENCE],
        "exact_reconciled_event_stream_binding": (
            "PASS" if finding_counts[FindingType.INVALID_AUTHORITY_REFERENCE] == 0 else "FAIL"
        ),
        "resolved_ledger_count": len(ledger),
    }
    return ReconciliationBundle(
        evidence_manifests=evidence_manifests,
        identity_events=identity_events,
        overlays=overlays,
        resolved_observations=application.observations,
        reconciled_manifest=reconciled_manifest,
        membership_events=membership_events,
        compilation=compilation,
        resolved_ledger=ledger,
        gate_results=gates,
    )


def parse_terminal_roster(raw: bytes) -> tuple[str, ...]:
    text = raw.decode("utf-8")
    start = text.index('id="constituents"')
    end = text.index("\n|}", start)
    symbols = re.findall(
        r"\{\{(?:(?:Nyse|Nasdaq)Symbol|BZX link)\|([^}|]+)", text[start:end],
    )
    roster = tuple(sorted(item.strip().upper().replace("-", ".") for item in symbols))
    if len(roster) != len(set(roster)) or len(roster) < 500:
        raise ValueError("terminal roster is not a unique S&P 500 set")
    return roster


def all_gates_pass(gates: dict[str, object]) -> bool:
    named = (
        "year_continuity", "member_count_sanity", "duplicate_membership_event",
        "duplicate_episode", "ticker_reuse_ambiguity", "terminal_exact_set",
        "source_provenance_authority", "exact_reconciled_event_stream_binding",
    )
    return all(gates[item] == "PASS" for item in named) and all(
        gates[item] == 0 for item in (
            "unresolved_error_count", "unresolved_critical_count",
            "invalid_overlay_authority_count", "terminal_set_difference_count",
            "duplicate_event_count", "duplicate_episode_count", "overlap_count",
            "future_ticker_count", "stale_predecessor_count", "add_present_count",
            "remove_absent_count", "unresolved_correction_count",
            "invalid_reconciled_derivation_context_count",
        )
    )
