"""Evidence-backed, date-effective security identity and market symbols."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib


FROZEN_SOURCE_URL = "https://en.wikipedia.org/w/index.php?oldid=1265285344"
END = "9999-12-31"


@dataclass(frozen=True)
class SecurityIdentityMapping:
    logical_security_id: str
    source_symbol: str
    source_security_name: str
    market_data_symbol: str
    effective_from: str
    effective_to: str
    transition_type: str
    predecessor_reference: str | None
    successor_reference: str | None
    evidence_url: str
    evidence_date: str
    evidence_hash: str | None
    confidence: str
    resolution_state: str


@dataclass(frozen=True)
class CorporateMembershipTransition:
    effective_date: str
    predecessor_ids: tuple[str, ...]
    predecessor_symbols: tuple[str, ...]
    successor_id: str
    successor_symbol: str
    transition_type: str
    evidence_url: str


def stable_id(key: str) -> str:
    return "AQSEC-" + hashlib.sha256(("sp500-pit-v1:" + key).encode()).hexdigest()[:16].upper()


IDS = {key: stable_id(key) for key in (
    "dayforce", "discovery-a", "discovery-c", "wbd", "aptiv", "delphi-technologies",
    "joy-global", "capri", "qwest", "iqvia", "everest", "wtw", "meta", "elevance",
    "paramount-b", "hollyfrontier", "hf-sinclair", "corpay", "under-armour-a",
    "under-armour-c", "ingersoll-rand-legacy", "ingersoll-rand-2020",
)}


EVIDENCE = {
    "dayforce": ("2024-02-01", "NAME_AND_TICKER_RENAME", "https://investors.dayforce.com/news-and-events/press-releases/press-release-details/2024/Ceridian-to-change-ticker-symbol-to-DAY-on-NYSE-and-TSX-effective-February-1/default.aspx"),
    "wbd": ("2022-04-11", "MERGER_SUCCESSOR", "https://ir.wbd.com/news-and-events/financial-news/financial-news-details/2022/Combination-of-Discovery-and-WarnerMedia-Creates-Warner-Bros.-Discovery-Global-Leader-in-Entertainment-and-Streaming/"),
    "aptiv": ("2017-12-05", "SPINOFF", "https://www.aptiv.com/en/newsroom/article/aptiv-plc-to-transform-future-mobility"),
    "joy-global": ("2011-12-06", "EXCHANGE_OR_SYMBOL_CHANGE", "https://www.sec.gov/Archives/edgar/data/801898/000119312512505211/d413371d10k.htm"),
    "capri": ("2019-01-02", "NAME_AND_TICKER_RENAME", "https://www.capriholdings.com/news/news-details/2018/Capri-Holdings-Limited-Completes-Acquisition-of-Versace/default.aspx"),
    "iqvia": ("2017-11-15", "NAME_AND_TICKER_RENAME", "https://ir.iqvia.com/press-releases/press-release-details/2017/QuintilesIMS-is-now-IQVIA/default.aspx"),
    "everest": ("2023-07-10", "NAME_AND_TICKER_RENAME", "https://www.nasdaq.com/press-release/everest-to-rebrand-company-name-and-nyse-ticker-to-reflect-its-evolution-global"),
    "wtw": ("2022-01-10", "PURE_TICKER_RENAME", "https://investors.wtwco.com/news-releases/news-release-details/willis-towers-watson-announces-nasdaq-ticker-symbol-change-wltw"),
    "meta": ("2022-06-09", "PURE_TICKER_RENAME", "https://investor.atmeta.com/investor-news/press-release-details/2022/Meta-Platforms-Inc.-to-Change-Ticker-Symbol-to-META-on-June-9/default.aspx"),
    "elevance": ("2022-06-28", "NAME_AND_TICKER_RENAME", "https://www.elevancehealth.com/newsroom/anthem-announces-subsidiary-brands-under-elevance-health"),
    "paramount-b": ("2022-02-17", "NAME_AND_TICKER_RENAME", "https://ir.paramount.com/news-releases/news-release-details/viacomcbs-unveils-new-company-name-global-content-slate-and"),
    "hf-sinclair": ("2022-03-15", "MERGER_SUCCESSOR", "https://investor.hfsinclair.com/investor-relations/press-releases/press-releases-details/2022/HollyFrontier-and-Holly-Energy-Partners-Announce-Completion-of-Transactions-with-The-Sinclair-Companies-and-Establishment-of-New-Parent-Company-HF-Sinclair-Corporation/default.aspx"),
    "corpay": ("2024-03-25", "NAME_AND_TICKER_RENAME", "https://investor.corpay.com/news-releases/news-release-details/fleetcor-announces-rebranding-corpay-0"),
}


# Same-security timelines. Corporate successors that create a new security are
# deliberately absent and handled through CORPORATE_MEMBERSHIP_TRANSITIONS.
TIMELINES = {
    "dayforce": (("1900-01-01", "2024-02-01", "CDAY", "Ceridian HCM Holding"), ("2024-02-01", END, "DAY", "Dayforce")),
    "aptiv": (("1900-01-01", "2017-12-05", "DLPH", "Delphi Automotive"), ("2017-12-05", END, "APTV", "Aptiv")),
    "joy-global": (("1900-01-01", "2011-12-06", "JOYG", "Joy Global"), ("2011-12-06", END, "JOY", "Joy Global")),
    "capri": (("1900-01-01", "2019-01-02", "KORS", "Michael Kors"), ("2019-01-02", END, "CPRI", "Capri Holdings")),
    "iqvia": (("2017-08-29", "2017-11-15", "Q", "QuintilesIMS"), ("2017-11-15", END, "IQV", "IQVIA")),
    "everest": (("1900-01-01", "2023-07-10", "RE", "Everest Re"), ("2023-07-10", END, "EG", "Everest Group")),
    "wtw": (("1900-01-01", "2022-01-10", "WLTW", "Willis Towers Watson"), ("2022-01-10", END, "WTW", "Willis Towers Watson")),
    "meta": (("1900-01-01", "2022-06-09", "FB", "Facebook"), ("2022-06-09", END, "META", "Meta Platforms")),
    "elevance": (("1900-01-01", "2022-06-28", "ANTM", "Anthem"), ("2022-06-28", END, "ELV", "Elevance Health")),
    "paramount-b": (("1900-01-01", "2022-02-17", "VIAC", "ViacomCBS Class B"), ("2022-02-17", END, "PARA", "Paramount Global Class B")),
    "corpay": (("1900-01-01", "2024-03-25", "FLT", "FLEETCOR Technologies"), ("2024-03-25", END, "CPAY", "Corpay")),
}


CORPORATE_MEMBERSHIP_TRANSITIONS = (
    CorporateMembershipTransition("2022-04-11", (IDS["discovery-a"], IDS["discovery-c"]), ("DISCA", "DISCK"), IDS["wbd"], "WBD", "MERGER_SUCCESSOR", EVIDENCE["wbd"][2]),
)


def _key(symbol: str, security: str | None, on_date: str | None) -> str:
    ticker, name = symbol.upper(), (security or "").casefold()
    if ticker in {"CDAY", "DAY"}: return "dayforce"
    if ticker in {"DISCA", "DISCB"}: return "discovery-a"
    if ticker == "DISCK": return "discovery-c"
    if ticker == "WBD": return "wbd"
    if ticker == "APTV" or (ticker == "DLPH" and ("automotive" in name or (not name and (on_date or "") < "2017-12-05"))): return "aptiv"
    if ticker == "DLPH" and ("technologies" in name or (not name and (on_date or "") >= "2017-12-05")): return "delphi-technologies"
    if ticker in {"JOYG", "JOY"}: return "joy-global"
    if ticker in {"KORS", "CPRI"}: return "capri"
    if ticker == "Q" and ("qwest" in name or (not name and (on_date or "") < "2017-08-29")): return "qwest"
    if ticker in {"Q", "IQV"} and (ticker == "IQV" or "quintiles" in name or (on_date or "") >= "2017-08-29"): return "iqvia"
    if ticker in {"RE", "EG"}: return "everest"
    if ticker in {"WLTW", "WTW"}: return "wtw"
    if ticker in {"FB", "META"}: return "meta"
    if ticker in {"ANTM", "ELV"}: return "elevance"
    if ticker in {"VIAC", "PARA"}: return "paramount-b"
    if ticker == "HFC": return "hollyfrontier"
    if ticker == "DINO": return "hf-sinclair"
    if ticker in {"FLT", "CPAY"}: return "corpay"
    if ticker == "UAA" or (ticker == "UA" and "class c" not in name): return "under-armour-a"
    if ticker == "UA" and "class c" in name: return "under-armour-c"
    if ticker == "TT" or (ticker == "IR" and "ingersoll-rand" in name): return "ingersoll-rand-legacy"
    if ticker == "IR" and "ingersoll rand" in name: return "ingersoll-rand-2020"
    return "symbol:" + ticker


def logical_identity(symbol: str, security: str | None = None, on_date: str | None = None) -> str:
    key = _key(symbol, security, on_date)
    return IDS.get(key, stable_id(key))


def market_symbol(logical_security_id: str, on_date: str) -> str:
    for key, segments in TIMELINES.items():
        if IDS[key] == logical_security_id:
            for start, end, symbol, _ in segments:
                if start <= on_date < end:
                    return symbol
    if logical_security_id == IDS["delphi-technologies"]: return "DLPH"
    if logical_security_id == IDS["wbd"]: return "WBD"
    raise KeyError(f"no date-effective market symbol for {logical_security_id} at {on_date}")


def transition_mappings() -> list[SecurityIdentityMapping]:
    result = []
    for key, segments in TIMELINES.items():
        evidence_date, kind, url = EVIDENCE[key]
        for index, (start, end, symbol, name) in enumerate(segments):
            result.append(SecurityIdentityMapping(IDS[key], symbol, name, symbol, start, end, kind if index else "SOURCE_SYMBOL_DIRECT", None if index == 0 else segments[index-1][2], None if index + 1 == len(segments) else segments[index+1][2], url, evidence_date, None, "HIGH", "RESOLVED"))
    result.append(SecurityIdentityMapping(IDS["delphi-technologies"], "DLPH", "Delphi Technologies", "DLPH", "2017-12-05", END, "TICKER_REUSE_NEW_SECURITY", "DLPH/Delphi Automotive", None, EVIDENCE["aptiv"][2], "2017-12-05", None, "HIGH", "RESOLVED"))
    for key, symbol, name in (("discovery-a", "DISCA", "Discovery Class A"), ("discovery-c", "DISCK", "Discovery Class C"), ("wbd", "WBD", "Warner Bros. Discovery")):
        start, end = ("1900-01-01", "2022-04-11") if key != "wbd" else ("2022-04-11", END)
        result.append(SecurityIdentityMapping(IDS[key], symbol, name, symbol, start, end, "MERGER_SUCCESSOR", None if key == "wbd" else IDS["wbd"], IDS["wbd"] if key != "wbd" else None, EVIDENCE["wbd"][2], "2022-04-11", None, "HIGH", "RESOLVED"))
    return result


def provider_symbol(source_symbol: str) -> str:
    return {"BRK.B": "BRK-B", "BF.B": "BF-B"}.get(source_symbol, source_symbol)
