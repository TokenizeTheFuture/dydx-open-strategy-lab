from __future__ import annotations

from pprint import pprint

from open_strategy_lab.backtest import BacktestConfig
from open_strategy_lab.data.synthetic import make_demo_data
from open_strategy_lab.risk import RiskConfig
from open_strategy_lab.strategies.funding_aware import FundingAwareConfig, FundingAwareStrategy
from open_strategy_lab.walkforward import WalkForwardConfig, run_walk_forward


def make_strategy(params):
    return FundingAwareStrategy(FundingAwareConfig(**params))


def main() -> None:
    data = make_demo_data(periods=1_500, seed=17)
    result = run_walk_forward(
        data,
        strategy_factory=make_strategy,
        parameter_grid={
            "funding_window": [6, 12],
            "momentum_window": [6, 12],
            "volatility_window": [24, 48],
            "min_abs_hourly_funding": [0.00003, 0.00005],
            "max_annualized_vol": [1.0],
        },
        walk_config=WalkForwardConfig(
            train_bars=24 * 20,
            test_bars=24 * 5,
            warmup_bars=72,
            objective="sharpe",
        ),
        backtest_config=BacktestConfig(
            initial_equity=10_000,
            fee_bps=5,
            slippage_bps=2,
            target_leverage=0.75,
        ),
        risk=RiskConfig(max_leverage=1.0, min_equity=500),
    )
    pprint(result.summary)
    print()
    print(result.folds.to_string(index=False))


if __name__ == "__main__":
    main()
