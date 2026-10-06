import pandas as pd

from open_strategy_lab.data.dydx import DydxIndexer
from open_strategy_lab.data.historical import DydxHistoricalData


def test_candles_pages_forward(monkeypatch):
    calls = []

    def fake_candles(
        self,
        ticker,
        resolution="1HOUR",
        limit=100,
        from_iso=None,
        to_iso=None,
    ):
        calls.append((from_iso, to_iso))
        start = pd.Timestamp(from_iso)
        end = pd.Timestamp(to_iso)
        index = pd.date_range(start, end, freq="h")
        return pd.DataFrame(
            {"close": [100.0 + i for i in range(len(index))]},
            index=index,
        )

    monkeypatch.setattr(DydxIndexer, "candles", fake_candles)

    loader = DydxHistoricalData(DydxIndexer())
    frame = loader.candles(
        "BTC-USD",
        "2026-01-01T00:00:00Z",
        "2026-01-01T10:00:00Z",
        page_limit=4,
        use_cache=False,
    )

    assert len(calls) > 1
    assert frame.index.min() == pd.Timestamp("2026-01-01T00:00:00Z")
    assert frame.index.max() == pd.Timestamp("2026-01-01T10:00:00Z")
    assert frame.index.is_unique
    assert len(frame) == 11


def test_funding_pages_backward(monkeypatch):
    index = pd.date_range(
        "2026-01-01T00:00:00Z",
        periods=12,
        freq="h",
    )
    source = pd.DataFrame(
        {"funding_rate": [0.0001] * len(index)},
        index=index,
    )

    def fake_historical(
        self,
        ticker,
        limit=100,
        effective_before_or_at=None,
    ):
        cursor = pd.Timestamp(effective_before_or_at)
        eligible = source.loc[source.index <= cursor]
        return eligible.tail(limit)

    monkeypatch.setattr(
        DydxIndexer,
        "historical_funding",
        fake_historical,
    )

    loader = DydxHistoricalData(DydxIndexer())
    frame = loader.funding(
        "BTC-USD",
        "2026-01-01T02:00:00Z",
        "2026-01-01T10:00:00Z",
        page_limit=3,
        use_cache=False,
    )

    assert frame.index.min() == pd.Timestamp("2026-01-01T02:00:00Z")
    assert frame.index.max() == pd.Timestamp("2026-01-01T10:00:00Z")
    assert frame.index.is_unique
    assert len(frame) == 9


def test_research_frame_uses_prior_funding(monkeypatch):
    candle_index = pd.date_range(
        "2026-01-01T00:30:00Z",
        periods=3,
        freq="h",
    )
    funding_index = pd.date_range(
        "2026-01-01T00:00:00Z",
        periods=3,
        freq="h",
    )

    loader = DydxHistoricalData(DydxIndexer())

    monkeypatch.setattr(
        DydxHistoricalData,
        "candles",
        lambda self, *args, **kwargs: pd.DataFrame(
            {"close": [100.0, 101.0, 102.0]},
            index=candle_index,
        ),
    )
    monkeypatch.setattr(
        DydxHistoricalData,
        "funding",
        lambda self, *args, **kwargs: pd.DataFrame(
            {"funding_rate": [0.001, 0.002, 0.003]},
            index=funding_index,
        ),
    )

    frame = loader.research_frame(
        "BTC-USD",
        candle_index[0],
        candle_index[-1],
        use_cache=False,
    )

    assert list(frame["funding_rate"]) == [0.001, 0.002, 0.003]


def test_invalid_ranges_are_rejected():
    loader = DydxHistoricalData(DydxIndexer())

    for method in (loader.candles, loader.funding):
        try:
            method(
                "BTC-USD",
                "2026-01-02T00:00:00Z",
                "2026-01-01T00:00:00Z",
                use_cache=False,
            )
        except ValueError as exc:
            assert "end must be after start" in str(exc)
        else:
            raise AssertionError("expected invalid range to fail")
