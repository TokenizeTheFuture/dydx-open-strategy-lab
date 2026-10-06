from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable

import pandas as pd
import websocket


MAINNET_WS_URL = "wss://indexer.dydx.trade/v4/ws"


@dataclass(frozen=True, slots=True)
class CandleEvent:
    timestamp: pd.Timestamp
    ticker: str
    resolution: str
    close: float


@dataclass(frozen=True, slots=True)
class MarketEvent:
    ticker: str
    next_funding_rate: float | None = None
    oracle_price: float | None = None
    oracle_effective_at: pd.Timestamp | None = None


def candle_subscription(
    ticker: str,
    resolution: str,
    *,
    batched: bool = True,
) -> dict[str, Any]:
    return {
        "type": "subscribe",
        "channel": "v4_candles",
        "id": f"{ticker}/{resolution}",
        "batched": batched,
    }


def markets_subscription(*, batched: bool = True) -> dict[str, Any]:
    return {
        "type": "subscribe",
        "channel": "v4_markets",
        "batched": batched,
    }


def parse_candle_events(message: dict[str, Any]) -> list[CandleEvent]:
    if message.get("type") not in {"channel_data", "channel_batch_data"}:
        return []
    if message.get("channel") != "v4_candles":
        return []

    events: list[CandleEvent] = []
    for item in message.get("contents", []):
        if not isinstance(item, dict):
            continue

        started_at = item.get("startedAt")
        ticker = item.get("ticker")
        resolution = item.get("resolution")
        close = item.get("close")

        if (
            started_at is None
            or ticker is None
            or resolution is None
            or close is None
        ):
            continue

        events.append(
            CandleEvent(
                timestamp=pd.Timestamp(started_at),
                ticker=str(ticker),
                resolution=str(resolution),
                close=float(close),
            )
        )

    return events


def parse_market_events(message: dict[str, Any]) -> list[MarketEvent]:
    if message.get("type") not in {"channel_data", "channel_batch_data"}:
        return []
    if message.get("channel") != "v4_markets":
        return []

    merged: dict[str, dict[str, Any]] = {}

    for item in message.get("contents", []):
        if not isinstance(item, dict):
            continue

        trading = item.get("trading") or {}
        for ticker, market in trading.items():
            if not isinstance(market, dict):
                continue
            state = merged.setdefault(str(ticker), {})
            rate = market.get("nextFundingRate")
            if rate is not None:
                state["next_funding_rate"] = float(rate)

        oracle_prices = item.get("oraclePrices") or {}
        for ticker, oracle in oracle_prices.items():
            if not isinstance(oracle, dict):
                continue
            state = merged.setdefault(str(ticker), {})
            price = oracle.get("oraclePrice")
            effective_at = oracle.get("effectiveAt")
            if price is not None:
                state["oracle_price"] = float(price)
            if effective_at is not None:
                state["oracle_effective_at"] = pd.Timestamp(effective_at)

    return [
        MarketEvent(
            ticker=ticker,
            next_funding_rate=values.get("next_funding_rate"),
            oracle_price=values.get("oracle_price"),
            oracle_effective_at=values.get("oracle_effective_at"),
        )
        for ticker, values in merged.items()
    ]


class PublicMarketStream:
    def __init__(
        self,
        *,
        url: str = MAINNET_WS_URL,
        on_candle: Callable[[CandleEvent], None] | None = None,
        on_market: Callable[[MarketEvent], None] | None = None,
    ) -> None:
        self.url = url
        self.on_candle = on_candle
        self.on_market = on_market
        self._subscriptions: list[dict[str, Any]] = []

    def add_candles(
        self,
        ticker: str,
        resolution: str,
        *,
        batched: bool = True,
    ) -> None:
        self._subscriptions.append(
            candle_subscription(
                ticker,
                resolution,
                batched=batched,
            )
        )

    def add_markets(self, *, batched: bool = True) -> None:
        self._subscriptions.append(
            markets_subscription(batched=batched)
        )

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        for subscription in self._subscriptions:
            ws.send(json.dumps(subscription))

    def _on_message(
        self,
        ws: websocket.WebSocketApp,
        raw_message: str,
    ) -> None:
        message = json.loads(raw_message)

        if self.on_candle is not None:
            for event in parse_candle_events(message):
                self.on_candle(event)

        if self.on_market is not None:
            for event in parse_market_events(message):
                self.on_market(event)

    def run_forever(self, **kwargs: Any) -> None:
        app = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
        )
        app.run_forever(**kwargs)
