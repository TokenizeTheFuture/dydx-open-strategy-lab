from __future__ import annotations

from pprint import pprint

from open_strategy_lab.backtest import BacktestConfig
from open_strategy_lab.data.synthetic import make_demo_data
from open_strategy_lab.paper import run_paper_replay
from open_strategy_lab.risk import RiskConfig
from open_strategy_lab.strategies.volatility_regime import (
    VolatilityRegimeStrategy,
)


def main() -> None:
    frame = make_demo_data(periods=1_000, seed=61)
    strategy = VolatilityRegimeStrategy()
    signals = strategy.signals(frame)

    result = run_paper_replay(
        frame,
        signals,
        BacktestConfig(
            initial_equity=10_000,
            fee_bps=5,
            slippage_bps=2,
            target_leverage=1.0,
        ),
        RiskConfig(max_leverage=1.0, min_equity=500),
    )

    pprint(result.summary)
    print()
    print(result.fills.tail(10).to_string())


if __name__ == "__main__":
    main()
