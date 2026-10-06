from __future__ import annotations

from open_strategy_lab import PublicMarketStream


def main() -> None:
    stream = PublicMarketStream(
        on_candle=lambda event: print("candle", event),
        on_market=lambda event: print("market", event),
    )
    stream.add_candles("BTC-USD", "1HOUR")
    stream.add_markets()
    stream.run_forever()


if __name__ == "__main__":
    main()
