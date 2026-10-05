from open_strategy_lab.data.synthetic import make_portfolio_demo_data
from open_strategy_lab.portfolio_backtest import PortfolioBacktestConfig, run_portfolio_backtest
from open_strategy_lab.strategies.cross_sectional_momentum import CrossSectionalMomentumConfig, CrossSectionalMomentumStrategy


def _strategy():
    return CrossSectionalMomentumStrategy(CrossSectionalMomentumConfig(long_count=2, short_count=2, gross_exposure=1.0, max_market_weight=0.30, min_markets=6))


def test_portfolio_backtest_runs():
    prices, funding = make_portfolio_demo_data(periods=400, markets=8)
    result = run_portfolio_backtest(prices, funding, _strategy(), PortfolioBacktestConfig(max_market_weight=0.30))
    assert len(result.ledger) == len(prices)
    assert result.summary["final_equity"] > 0
    assert result.summary["max_drawdown"] <= 0
    assert result.summary["average_abs_net_exposure"] < 1e-9


def test_costs_are_non_negative():
    prices, funding = make_portfolio_demo_data(periods=400, markets=8)
    result = run_portfolio_backtest(prices, funding, _strategy(), PortfolioBacktestConfig(max_market_weight=0.30))
    assert result.summary["trading_cost_return_sum"] >= 0
    assert result.summary["turnover_sum"] >= 0
