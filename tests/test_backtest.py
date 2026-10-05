from open_strategy_lab.backtest import BacktestConfig, run_backtest
from open_strategy_lab.data.synthetic import make_demo_data
from open_strategy_lab.risk import RiskConfig
from open_strategy_lab.strategies.funding_aware import FundingAwareStrategy


def test_backtest_produces_ledger_and_summary():
    data = make_demo_data(periods=300)
    result = run_backtest(data, FundingAwareStrategy(), BacktestConfig(target_leverage=0.5), RiskConfig(max_leverage=1.0))
    assert len(result.ledger) == len(data)
    assert result.summary["final_equity"] > 0
    assert result.summary["max_drawdown"] <= 0


def test_leverage_limit_is_enforced():
    data = make_demo_data(periods=300)
    try:
        run_backtest(data, FundingAwareStrategy(), BacktestConfig(target_leverage=2.0), RiskConfig(max_leverage=1.0))
    except ValueError as exc:
        assert "exceeds" in str(exc)
    else:
        raise AssertionError("expected leverage validation error")
