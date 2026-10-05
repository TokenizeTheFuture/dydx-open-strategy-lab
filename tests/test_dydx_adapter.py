from open_strategy_lab.data.dydx import DydxIndexer


def test_perpetual_markets_parses_market_map(monkeypatch):
    def fake_get(self, path, params=None):
        assert path == "/v4/perpetualMarkets"
        return {"markets": {"BTC-USD": {"ticker": "BTC-USD"}}}
    monkeypatch.setattr(DydxIndexer, "_get", fake_get)
    markets = DydxIndexer().perpetual_markets()
    assert "BTC-USD" in markets


def test_candles_parse(monkeypatch):
    def fake_get(self, path, params=None):
        assert path == "/v4/candles/perpetualMarkets/BTC-USD"
        return {"candles": [{"startedAt": "2026-01-01T01:00:00Z", "close": "101.5"}, {"startedAt": "2026-01-01T00:00:00Z", "close": "100.0"}]}
    monkeypatch.setattr(DydxIndexer, "_get", fake_get)
    frame = DydxIndexer().candles("BTC-USD")
    assert list(frame["close"]) == [100.0, 101.5]


def test_historical_funding_parse(monkeypatch):
    def fake_get(self, path, params=None):
        assert path == "/v4/historicalFunding/BTC-USD"
        return {"historicalFunding": [{"effectiveAt": "2026-01-01T01:00:00Z", "rate": "0.0001"}, {"effectiveAt": "2026-01-01T00:00:00Z", "rate": "-0.0002"}]}
    monkeypatch.setattr(DydxIndexer, "_get", fake_get)
    frame = DydxIndexer().historical_funding("BTC-USD")
    assert list(frame["funding_rate"]) == [-0.0002, 0.0001]
