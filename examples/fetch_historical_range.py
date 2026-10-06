from __future__ import annotations

from open_strategy_lab.data import CsvCache, DydxHistoricalData, DydxIndexer


def main() -> None:
    loader = DydxHistoricalData(
        DydxIndexer(),
        cache=CsvCache(".cache/open_strategy_lab"),
    )

    frame = loader.research_frame(
        "BTC-USD",
        "2026-09-01T00:00:00Z",
        "2026-09-07T00:00:00Z",
        resolution="1HOUR",
    )
    print(frame.tail(20).to_string())


if __name__ == "__main__":
    main()
