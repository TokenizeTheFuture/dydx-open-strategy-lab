import numpy as np
import pandas as pd

from open_strategy_lab.strategies.volatility_regime import (
    VolatilityRegimeConfig,
    VolatilityRegimeStrategy,
)


def _regime_data(periods=900, seed=31):
    rng = np.random.default_rng(seed)
    index = pd.date_range("2026-01-01", periods=periods, freq="h", tz="UTC")

    sigma = np.concatenate(
        [
            np.full(periods // 3, 0.001),
            np.full(periods // 3, 0.003),
            np.full(periods - 2 * (periods // 3), 0.010),
        ]
    )
    returns = 0.0002 + rng.normal(0.0, sigma)
    close = 100.0 * np.exp(np.cumsum(returns))

    return pd.DataFrame(
        {
            "close": close,
            "funding_rate": np.zeros(periods),
        },
        index=index,
    )


def test_signal_domain_and_fractional_exposure():
    frame = _regime_data()
    strategy = VolatilityRegimeStrategy(
        VolatilityRegimeConfig(
            momentum_window=12,
            volatility_window=24,
            regime_lookback=120,
            low_vol_exposure=1.0,
            normal_vol_exposure=0.6,
            high_vol_exposure=0.2,
            min_momentum=0.0,
        )
    )

    signal = strategy.signals(frame)

    assert signal.abs().max() <= 1.0
    assert set(signal.abs().round(6).unique()).issubset({0.0, 0.2, 0.6, 1.0})


def test_high_volatility_reduces_exposure():
    frame = _regime_data()
    strategy = VolatilityRegimeStrategy(
        VolatilityRegimeConfig(
            momentum_window=12,
            volatility_window=24,
            regime_lookback=120,
            low_vol_exposure=1.0,
            normal_vol_exposure=0.6,
            high_vol_exposure=0.2,
            min_momentum=0.0,
        )
    )

    regimes = strategy.regimes(frame)
    signal = strategy.signals(frame)

    shifted_regime = regimes.shift(1)
    high = signal.loc[shifted_regime == strategy.HIGH].abs()
    low = signal.loc[shifted_regime == strategy.LOW].abs()

    assert not high.empty
    assert not low.empty
    assert high.max() <= 0.2 + 1e-12
    assert low.max() >= 0.6


def test_signal_has_one_bar_delay():
    frame = _regime_data(periods=500)
    strategy = VolatilityRegimeStrategy(
        VolatilityRegimeConfig(
            momentum_window=2,
            volatility_window=2,
            regime_lookback=10,
            min_momentum=0.0,
        )
    )

    signal = strategy.signals(frame)

    assert signal.iloc[0] == 0.0


def test_future_price_change_does_not_alter_prior_signals():
    frame = _regime_data(periods=600)
    strategy = VolatilityRegimeStrategy(
        VolatilityRegimeConfig(
            momentum_window=12,
            volatility_window=24,
            regime_lookback=100,
        )
    )

    original = strategy.signals(frame)
    changed = frame.copy()
    changed.iloc[-1, changed.columns.get_loc("close")] *= 3.0
    revised = strategy.signals(changed)

    pd.testing.assert_series_equal(
        original.iloc[:-1],
        revised.iloc[:-1],
    )
