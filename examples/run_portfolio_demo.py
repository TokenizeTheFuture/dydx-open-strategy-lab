from __future__ import annotations

from pprint import pprint
from open_strategy_lab.analytics import write_markdown_report, write_summary_json
from open_strategy_lab.data.synthetic import make_portfolio_demo_data
from open_strategy_lab.portfolio_backtest import PortfolioBacktestConfig, run_portfolio_backtest
from open_strategy_lab.strategies.cross_sectional_momentum import CrossSectionalMomentumConfig, CrossSectionalMomentumStrategy


def main() -> None:
    prices, funding = make_portfolio_demo_data()
    strategy = CrossSectionalMomentumStrategy(CrossSectionalMomentumConfig(lookback_hours=24,volatility_window=48,rebalance_hours=4,long_count=2,short_count=2,gross_exposure=1.0,max_market_weight=0.30,min_markets=6))
    result = run_portfolio_backtest(prices,funding,strategy,PortfolioBacktestConfig(initial_equity=10_000,fee_bps=5,slippage_bps=2,max_gross_exposure=1.0,max_market_weight=0.30))
    pprint(result.summary)
    write_summary_json(result.summary,"artifacts/portfolio-demo-summary.json")
    write_markdown_report(result.summary,"artifacts/portfolio-demo-report.md","Cross-Sectional Momentum Demo")


if __name__ == "__main__":
    main()
