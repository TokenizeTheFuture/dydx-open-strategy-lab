import json

import pandas as pd

from open_strategy_lab.stream import (
    CandleEvent,
    MarketEvent,
    candle_subscription,
    markets_subscription,
    parse_candle_events,
    parse_market_events,
)


def test_candle_subscription_matches_dydx_channel_shape():
    payload = candle_subscription("BTC-USD", "1HOUR")

    assert payload == {
        "type": "subscribe",
        "channel": "v4_candles",
        "id": "BTC-USD/1HOUR",
        "batched": True,
    }


def test_markets_subscription_matches_dydx_channel_shape():
    assert markets_subscription() == {
        "type": "subscribe",
        "channel": "v4_markets",
        "batched": True,
    }


def test_parse_candle_batch():
    message = {
        "type": "channel_batch_data",
        "channel": "v4_candles",
        "contents": [
            {
                "startedAt": "2026-10-06T10:00:00Z",
                "ticker": "BTC-USD",
                "resolution": "1HOUR",
                "close": "123456.7",
            }
        ],
    }

    events = parse_candle_events(message)

    assert events == [
        CandleEvent(
            timestamp=pd.Timestamp("2026-10-06T10:00:00Z"),
            ticker="BTC-USD",
            resolution="1HOUR",
            close=123456.7,
        )
    ]


def test_parse_market_batch():
    message = {
        "type": "channel_batch_data",
        "channel": "v4_markets",
        "contents": [
            {
                "trading": {
                    "BTC-USD": {
                        "nextFundingRate": "0.000125",
                    }
                },
                "oraclePrices": {
                    "BTC-USD": {
                        "oraclePrice": "123400.5",
                        "effectiveAt": "2026-10-06T10:01:00Z",
                    }
                },
            }
        ],
    }

    events = parse_market_events(message)

    assert events == [
        MarketEvent(
            ticker="BTC-USD",
            next_funding_rate=0.000125,
            oracle_price=123400.5,
            oracle_effective_at=pd.Timestamp("2026-10-06T10:01:00Z"),
        )
    ]


def test_non_matching_messages_are_ignored():
    connected = {"type": "connected"}

    assert parse_candle_events(connected) == []
    assert parse_market_events(connected) == []
