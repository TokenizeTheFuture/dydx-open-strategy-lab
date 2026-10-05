from __future__ import annotations

from open_strategy_lab.data.dydx import DydxIndexer


def main() -> None:
    indexer = DydxIndexer()
    frame = indexer.research_frame("BTC-USD", limit=100)
    print(frame.tail(10).to_string())


if __name__ == "__main__":
    main()
