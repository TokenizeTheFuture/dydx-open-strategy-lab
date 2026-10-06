from __future__ import annotations

from pprint import pprint

from open_strategy_lab.backtest import BacktestConfig, run_backtest
from open_strategy_lab.data.synthetic import make_demo_data
from open_strategy_lab.risk import RiskConfig
from open_strategy_lab.strategies.volatility_regime import (
    VolatilityRegimeConfig,
    VolatilityRegimeStrategy,
)


def main() -> None:
    data = make_demo_data(periods=1_200, seed=41)

    strategy = VolatilityRegimeStrategy(
        VolatilityRegimeConfig(
            momentum_window=24,
            volatility_window=24,
            regime_lookback=24 * 14,
            low_quantile=0.35,
            high_quantile=0.70,
            low_vol_exposure=1.0,
            normal_vol_exposure=0.60,
            high_vol_exposure=0.25,
            min_momentum=0.002,
        )
    )

    result = run_backtest(
        data,
        strategy,
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
    print(strategy.regimes(data).value_counts().to_string())


if __name__ == "__main__":
    main()
