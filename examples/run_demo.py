from __future__ import annotations

from pprint import pprint
from open_strategy_lab.backtest import BacktestConfig, run_backtest
from open_strategy_lab.data.synthetic import make_demo_data
from open_strategy_lab.risk import RiskConfig
from open_strategy_lab.strategies.funding_aware import FundingAwareConfig, FundingAwareStrategy


def main() -> None:
    data = make_demo_data()
    strategy = FundingAwareStrategy(FundingAwareConfig(funding_window=8,momentum_window=12,volatility_window=24,min_abs_hourly_funding=0.00004,max_annualized_vol=1.20))
    result = run_backtest(data,strategy,BacktestConfig(initial_equity=10_000,fee_bps=5,slippage_bps=2,target_leverage=0.75),RiskConfig(max_leverage=1.0,max_annualized_vol=1.20,min_equity=500))
    pprint(result.summary); print(); print(result.ledger.tail(8).to_string())


if __name__ == "__main__":
    main()
