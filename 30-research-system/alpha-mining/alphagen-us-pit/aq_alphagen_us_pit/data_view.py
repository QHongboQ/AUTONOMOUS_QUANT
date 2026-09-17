"""AQ's thin, read-only view of the existing Qlib US PIT provider."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import torch
from qlib.config import REG_US
from qlib.data import D

from alphagen_qlib.stock_data import FeatureType


PROVIDER_URI = Path("/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data")
BUILD_REPORT = Path(
    "/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/reports/build-report.json"
)
BUILD_REPORT_SHA256 = "eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142"
SEALED_OOS_START = pd.Timestamp("2026-09-14")
MARKET = "p2_pit"

FEATURE_FIELDS = (
    (FeatureType.OPEN, "$open"),
    (FeatureType.CLOSE, "$close"),
    (FeatureType.HIGH, "$high"),
    (FeatureType.LOW, "$low"),
    (FeatureType.VOLUME, "$volume"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _initialize_provider(provider_uri: Path) -> None:
    import qlib

    qlib.init(provider_uri=str(provider_uri), region=REG_US)


def _validate_authority(build_report: Path, build_report_sha256: str) -> None:
    if _sha256(build_report) != build_report_sha256:
        raise ValueError("P2 ragged-panel build authority hash mismatch")


def _validate_time_bounds(start: pd.Timestamp, end: pd.Timestamp) -> None:
    if start > end:
        raise ValueError("Evaluation start must not follow evaluation end")
    if end >= SEALED_OOS_START:
        raise ValueError("Evaluation interval reaches sealed OOS")


def _covers_interval(
    intervals: Sequence[tuple[pd.Timestamp, pd.Timestamp]],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> bool:
    return any(pd.Timestamp(left) <= start and pd.Timestamp(right) >= end for left, right in intervals)


def membership_covering_instruments(
    start_time: str | pd.Timestamp,
    end_time: str | pd.Timestamp,
    *,
    provider_uri: Path = PROVIDER_URI,
    market: str = MARKET,
) -> list[str]:
    """Return identities whose accepted PIT membership covers the whole interval."""
    start, end = pd.Timestamp(start_time), pd.Timestamp(end_time)
    _validate_time_bounds(start, end)
    _initialize_provider(provider_uri)
    membership = D.list_instruments(
        D.instruments(market), start_time=start, end_time=end, as_list=False
    )
    return sorted(
        instrument
        for instrument, intervals in membership.items()
        if _covers_interval(intervals, start, end)
    )


@dataclass(frozen=True)
class USPitDataView:
    """The exact five-channel tensor surface consumed by AlphaGen expressions."""

    data: torch.Tensor
    dates: pd.DatetimeIndex
    stock_ids: pd.Index
    max_backtrack_days: int
    max_future_days: int
    evaluation_start: pd.Timestamp
    evaluation_end: pd.Timestamp

    @property
    def n_days(self) -> int:
        return self.data.shape[0] - self.max_backtrack_days - self.max_future_days

    @property
    def n_stocks(self) -> int:
        return self.data.shape[-1]


def load_us_pit_view(
    *,
    instruments: Sequence[str],
    start_time: str | pd.Timestamp,
    end_time: str | pd.Timestamp,
    max_backtrack_days: int,
    max_future_days: int,
    device: torch.device,
    provider_uri: Path = PROVIDER_URI,
    build_report: Path = BUILD_REPORT,
    build_report_sha256: str = BUILD_REPORT_SHA256,
    market: str = MARKET,
) -> USPitDataView:
    """Load OHLCV only, preserving the provider's authoritative ragged NaNs."""
    start, end = pd.Timestamp(start_time), pd.Timestamp(end_time)
    _validate_authority(build_report, build_report_sha256)
    _validate_time_bounds(start, end)
    if not instruments:
        raise ValueError("At least one instrument is required")
    if len(set(instruments)) != len(instruments):
        raise ValueError("Instrument identities must be unique")
    if max_backtrack_days < 0 or max_future_days < 0:
        raise ValueError("AlphaGen buffer sizes must be non-negative")

    _initialize_provider(provider_uri)
    calendar = pd.DatetimeIndex(D.calendar(freq="day"))
    start_index = int(calendar.searchsorted(start))
    end_index = int(calendar.searchsorted(end, side="right") - 1)
    if (
        start_index >= len(calendar)
        or end_index < 0
        or calendar[start_index] != start
        or calendar[end_index] != end
    ):
        raise ValueError("Evaluation boundaries must be exact Qlib sessions")
    load_start_index = start_index - max_backtrack_days
    load_end_index = end_index + max_future_days
    if load_start_index < 0 or load_end_index >= len(calendar):
        raise ValueError("Insufficient authoritative history for AlphaGen buffers")
    loaded_dates = calendar[load_start_index : load_end_index + 1]
    if loaded_dates[-1] >= SEALED_OOS_START:
        raise ValueError("AlphaGen future buffer reaches sealed OOS")

    membership = D.list_instruments(
        D.instruments(market), start_time=start, end_time=end, as_list=False
    )
    uncovered = [
        instrument
        for instrument in instruments
        if instrument not in membership
        or not _covers_interval(membership[instrument], start, end)
    ]
    if uncovered:
        raise ValueError(
            "Requested identities lack continuous accepted PIT membership: "
            + ", ".join(uncovered)
        )

    fields = [field for _, field in FEATURE_FIELDS]
    frame = D.features(
        list(instruments),
        fields,
        start_time=loaded_dates[0],
        end_time=loaded_dates[-1],
        freq="day",
    )
    channels: list[np.ndarray] = []
    for expected_index, (feature, field) in enumerate(FEATURE_FIELDS):
        if int(feature) != expected_index:
            raise ValueError("AlphaGen feature indices 0-4 do not match AQ channel order")
        wide = frame[field].unstack(level="instrument")
        wide = wide.reindex(index=loaded_dates, columns=list(instruments))
        channels.append(wide.to_numpy(dtype=np.float32))
    tensor = torch.as_tensor(np.stack(channels, axis=1), device=device)
    return USPitDataView(
        data=tensor,
        dates=loaded_dates,
        stock_ids=pd.Index(instruments),
        max_backtrack_days=max_backtrack_days,
        max_future_days=max_future_days,
        evaluation_start=start,
        evaluation_end=end,
    )
