from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .cache import CsvCache
from .dydx import DydxIndexer


_RESOLUTION_DELTA = {
    "1MIN": pd.Timedelta(minutes=1),
    "5MINS": pd.Timedelta(minutes=5),
    "15MINS": pd.Timedelta(minutes=15),
    "30MINS": pd.Timedelta(minutes=30),
    "1HOUR": pd.Timedelta(hours=1),
    "4HOURS": pd.Timedelta(hours=4),
    "1DAY": pd.Timedelta(days=1),
}


def _utc(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


@dataclass(slots=True)
class DydxHistoricalData:
    indexer: DydxIndexer
    cache: CsvCache | None = None

    def candles(
        self,
        ticker: str,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp,
        resolution: str = "1HOUR",
        page_limit: int = 100,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        if resolution not in _RESOLUTION_DELTA:
            raise ValueError(f"unsupported resolution: {resolution}")
        if page_limit < 2:
            raise ValueError("page_limit must be >= 2")

        start_ts = _utc(start)
        end_ts = _utc(end)
        if end_ts <= start_ts:
            raise ValueError("end must be after start")

        cache_key = (
            f"candles_{ticker}_{resolution}_"
            f"{start_ts.isoformat()}_{end_ts.isoformat()}"
        )
        if use_cache and self.cache:
            cached = self.cache.load(cache_key)
            if cached is not None:
                return cached

        bar = _RESOLUTION_DELTA[resolution]
        window = bar * (page_limit - 1)
        cursor = start_ts
        parts: list[pd.DataFrame] = []

        while cursor <= end_ts:
            window_end = min(cursor + window, end_ts)
            part = self.indexer.candles(
                ticker,
                resolution=resolution,
                limit=page_limit,
                from_iso=cursor.isoformat(),
                to_iso=window_end.isoformat(),
            )
            if not part.empty:
                parts.append(part)

            if window_end >= end_ts:
                break
            cursor = window_end + bar

        result = self._combine(parts, "close", start_ts, end_ts)
        if use_cache and self.cache and not result.empty:
            self.cache.save(cache_key, result)
        return result

    def funding(
        self,
        ticker: str,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp,
        page_limit: int = 100,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        if page_limit < 2:
            raise ValueError("page_limit must be >= 2")

        start_ts = _utc(start)
        end_ts = _utc(end)
        if end_ts <= start_ts:
            raise ValueError("end must be after start")

        cache_key = (
            f"funding_{ticker}_{start_ts.isoformat()}_{end_ts.isoformat()}"
        )
        if use_cache and self.cache:
            cached = self.cache.load(cache_key)
            if cached is not None:
                return cached

        cursor = end_ts
        parts: list[pd.DataFrame] = []

        while cursor >= start_ts:
            part = self.indexer.historical_funding(
                ticker,
                limit=page_limit,
                effective_before_or_at=cursor.isoformat(),
            )
            if part.empty:
                break

            parts.append(part)
            oldest = part.index.min()

            if oldest <= start_ts or len(part) < page_limit:
                break

            next_cursor = oldest - pd.Timedelta(microseconds=1)
            if next_cursor >= cursor:
                raise RuntimeError("funding pagination did not advance")
            cursor = next_cursor

        result = self._combine(parts, "funding_rate", start_ts, end_ts)
        if use_cache and self.cache and not result.empty:
            self.cache.save(cache_key, result)
        return result

    def research_frame(
        self,
        ticker: str,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp,
        resolution: str = "1HOUR",
        page_limit: int = 100,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        candles = self.candles(
            ticker,
            start,
            end,
            resolution=resolution,
            page_limit=page_limit,
            use_cache=use_cache,
        )
        funding = self.funding(
            ticker,
            start,
            end,
            page_limit=page_limit,
            use_cache=use_cache,
        )

        if candles.empty or funding.empty:
            return pd.DataFrame(columns=["close", "funding_rate"])

        return pd.merge_asof(
            candles.sort_index(),
            funding.sort_index(),
            left_index=True,
            right_index=True,
            direction="backward",
        ).dropna()

    @staticmethod
    def _combine(
        parts: list[pd.DataFrame],
        column: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        if not parts:
            return pd.DataFrame(columns=[column])

        result = pd.concat(parts).sort_index()
        result = result[~result.index.duplicated(keep="last")]
        return result.loc[(result.index >= start) & (result.index <= end)]
