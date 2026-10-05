import numpy as np

from open_strategy_lab.data.synthetic import make_portfolio_demo_data
from open_strategy_lab.strategies.cross_sectional_momentum import CrossSectionalMomentumConfig, CrossSectionalMomentumStrategy


def test_market_neutral_weights_obey_limits():
    prices, funding = make_portfolio_demo_data(periods=400, markets=8)
    strategy = CrossSectionalMomentumStrategy(CrossSectionalMomentumConfig(long_count=2, short_count=2, gross_exposure=1.0, max_market_weight=0.30, min_markets=6))
    weights = strategy.weights(prices, funding)
    active = weights.abs().sum(axis=1) > 0
    assert (weights.abs().max(axis=1) <= 0.30 + 1e-12).all()
    assert (weights.abs().sum(axis=1) <= 1.0 + 1e-12).all()
    assert np.allclose(weights.loc[active].sum(axis=1), 0.0, atol=1e-12)


def test_portfolio_signal_is_delayed():
    prices, funding = make_portfolio_demo_data(periods=300, markets=8)
    strategy = CrossSectionalMomentumStrategy()
    weights = strategy.weights(prices, funding)
    assert (weights.iloc[0] == 0.0).all()
