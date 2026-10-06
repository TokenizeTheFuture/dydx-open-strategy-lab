from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .backtest import BacktestConfig, run_backtest
from .data.synthetic import make_demo_data, make_portfolio_demo_data
from .paper import run_paper_replay
from .portfolio_backtest import PortfolioBacktestConfig, run_portfolio_backtest
from .risk import RiskConfig
from .strategies.cross_sectional_momentum import (
    CrossSectionalMomentumConfig,
    CrossSectionalMomentumStrategy,
)
from .strategies.funding_aware import (
    FundingAwareConfig,
    FundingAwareStrategy,
)
from .strategies.volatility_regime import (
    VolatilityRegimeConfig,
    VolatilityRegimeStrategy,
)
from .walkforward import WalkForwardConfig, run_walk_forward


def _round_summary(summary: dict[str, float]) -> dict[str, float]:
    return {key: round(float(value), 8) for key, value in summary.items()}


def run_grant_demo(output_dir: str | Path = "artifacts/grant-demo") -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    single_market = make_demo_data(periods=1_500, seed=101)
    backtest_config = BacktestConfig(
        initial_equity=10_000,
        fee_bps=5,
        slippage_bps=2,
        target_leverage=0.75,
    )
    risk = RiskConfig(
        max_leverage=1.0,
        min_equity=500,
    )

    funding_strategy = FundingAwareStrategy(
        FundingAwareConfig(
            funding_window=8,
            momentum_window=12,
            volatility_window=24,
            min_abs_hourly_funding=0.00004,
            max_annualized_vol=1.20,
        )
    )
    funding_result = run_backtest(
        single_market,
        funding_strategy,
        config=backtest_config,
        risk=risk,
    )

    regime_strategy = VolatilityRegimeStrategy(
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
    regime_result = run_backtest(
        single_market,
        regime_strategy,
        config=BacktestConfig(
            initial_equity=10_000,
            fee_bps=5,
            slippage_bps=2,
            target_leverage=1.0,
        ),
        risk=risk,
    )

    paper_result = run_paper_replay(
        single_market,
        regime_strategy.signals(single_market),
        config=BacktestConfig(
            initial_equity=10_000,
            fee_bps=5,
            slippage_bps=2,
            target_leverage=1.0,
        ),
        risk=risk,
    )

    prices, funding = make_portfolio_demo_data(
        periods=1_000,
        markets=8,
        seed=202,
    )
    portfolio_strategy = CrossSectionalMomentumStrategy(
        CrossSectionalMomentumConfig(
            lookback_hours=24,
            volatility_window=48,
            rebalance_hours=4,
            long_count=2,
            short_count=2,
            gross_exposure=1.0,
            max_market_weight=0.30,
            min_markets=6,
        )
    )
    portfolio_result = run_portfolio_backtest(
        prices,
        funding,
        portfolio_strategy,
        PortfolioBacktestConfig(
            initial_equity=10_000,
            fee_bps=5,
            slippage_bps=2,
            max_gross_exposure=1.0,
            max_market_weight=0.30,
        ),
    )

    def strategy_factory(params: dict[str, Any]) -> FundingAwareStrategy:
        return FundingAwareStrategy(FundingAwareConfig(**params))

    walk_forward = run_walk_forward(
        single_market,
        strategy_factory=strategy_factory,
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
        backtest_config=backtest_config,
        risk=risk,
    )

    accounting_delta = abs(
        paper_result.summary["final_equity"]
        - regime_result.summary["final_equity"]
    )

    report = {
        "demo_type": "deterministic_offline_research_demo",
        "network_required": False,
        "profitability_claim": False,
        "funding_aware_backtest": _round_summary(funding_result.summary),
        "volatility_regime_backtest": _round_summary(regime_result.summary),
        "market_neutral_portfolio": _round_summary(portfolio_result.summary),
        "walk_forward": _round_summary(walk_forward.summary),
        "paper_replay": _round_summary(paper_result.summary),
        "paper_vs_batch_final_equity_delta": round(accounting_delta, 12),
    }

    summary_path = output / "summary.json"
    summary_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    walk_forward.folds.to_csv(
        output / "walk_forward_folds.csv",
        index=False,
    )
    paper_result.fills.to_csv(
        output / "paper_fills.csv",
    )

    markdown = [
        "# Open Strategy Lab — Grant Demo",
        "",
        "Deterministic offline demonstration of the research framework.",
        "",
        "- No network connection is required.",
        "- No wallet, private key, signing or live order placement is used.",
        "- Results are simulated research outputs, not profitability claims.",
        "",
        "## Components exercised",
        "",
        "1. Funding-aware single-market backtest",
        "2. Volatility-regime adaptive backtest",
        "3. Cross-sectional market-neutral portfolio backtest",
        "4. Walk-forward out-of-sample validation",
        "5. Stateful paper replay",
        "",
        "## Consistency check",
        "",
        (
            "Paper replay vs. batch backtest final-equity delta: "
            f"{accounting_delta:.12f}"
        ),
        "",
        "Machine-readable outputs:",
        "",
        "- summary.json",
        "- walk_forward_folds.csv",
        "- paper_fills.csv",
        "",
    ]
    (output / "README.md").write_text(
        "\n".join(markdown),
        encoding="utf-8",
    )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the deterministic Open Strategy Lab grant demo."
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/grant-demo",
        help="Directory for generated demo artifacts.",
    )
    args = parser.parse_args()

    report = run_grant_demo(args.output_dir)
    output = Path(args.output_dir)

    print("Open Strategy Lab grant demo completed.")
    print(f"Artifacts: {output.resolve()}")
    print(
        "Paper/batch final-equity delta: "
        f"{report['paper_vs_batch_final_equity_delta']:.12f}"
    )
    print(
        "Walk-forward folds: "
        f"{int(report['walk_forward']['folds'])}"
    )


if __name__ == "__main__":
    main()
