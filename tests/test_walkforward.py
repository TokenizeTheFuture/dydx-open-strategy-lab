from open_strategy_lab.backtest import BacktestConfig
from open_strategy_lab.data.synthetic import make_demo_data
from open_strategy_lab.risk import RiskConfig
from open_strategy_lab.strategies.funding_aware import FundingAwareConfig, FundingAwareStrategy
from open_strategy_lab.walkforward import WalkForwardConfig, expand_grid, run_walk_forward


def test_expand_grid():
    grid = expand_grid({"a": [1, 2], "b": ["x", "y"]})
    assert len(grid) == 4
    assert {"a": 1, "b": "x"} in grid


def test_walk_forward_produces_out_of_sample_folds():
    data = make_demo_data(periods=700, seed=21)

    def factory(params):
        return FundingAwareStrategy(FundingAwareConfig(**params))

    result = run_walk_forward(
        data,
        strategy_factory=factory,
        parameter_grid={
            "funding_window": [6, 12],
            "momentum_window": [6],
            "volatility_window": [24],
            "min_abs_hourly_funding": [0.00003, 0.00005],
            "max_annualized_vol": [1.2],
        },
        walk_config=WalkForwardConfig(
            train_bars=240,
            test_bars=96,
            warmup_bars=72,
        ),
        backtest_config=BacktestConfig(target_leverage=0.5),
        risk=RiskConfig(max_leverage=1.0),
    )

    assert len(result.folds) >= 3
    assert result.summary["folds"] == float(len(result.folds))
    assert 0.0 <= result.summary["positive_fold_ratio"] <= 1.0
    assert result.folds["selected_params"].map(bool).all()
