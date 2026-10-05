from __future__ import annotations

from open_strategy_lab.data.dydx import DydxIndexer


def main() -> None:
    indexer = DydxIndexer()
    prices, funding = indexer.market_panel(["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"], limit=100)
    print("prices"); print(prices.tail().to_string()); print(); print("funding"); print(funding.tail().to_string())


if __name__ == "__main__":
    main()
