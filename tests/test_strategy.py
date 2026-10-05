import pandas as pd

from open_strategy_lab.data.synthetic import make_demo_data
from open_strategy_lab.strategies.funding_aware import FundingAwareConfig, FundingAwareStrategy


def test_signal_shape_and_domain():
    data = make_demo_data(periods=300)
    strategy = FundingAwareStrategy(FundingAwareConfig(min_abs_hourly_funding=0.00003))
    signal = strategy.signals(data)
    assert signal.index.equals(data.index)
    assert set(signal.unique()).issubset({-1.0, 0.0, 1.0})


def test_signal_is_delayed_one_bar():
    index = pd.date_range("2026-01-01", periods=60, freq="h", tz="UTC")
    data = pd.DataFrame({"close": [100.0] * 60, "funding_rate": [0.001] * 60}, index=index)
    strategy = FundingAwareStrategy(FundingAwareConfig(funding_window=2,momentum_window=2,volatility_window=2,min_abs_hourly_funding=0.0001,max_annualized_vol=2.0))
    signal = strategy.signals(data)
    assert signal.iloc[0] == 0
    assert signal.iloc[1] == 0
