from __future__ import annotations

import numpy as np
import pandas as pd


def make_demo_data(periods: int = 500, seed: int = 7) -> pd.DataFrame:
    if periods < 100:
        raise ValueError("periods must be >= 100")
    rng = np.random.default_rng(seed)
    index = pd.date_range("2026-01-01", periods=periods, freq="h", tz="UTC")
    regime = np.sin(np.linspace(0, 8 * np.pi, periods))
    noise = rng.normal(0.0, 0.0035, periods)
    drift = np.where(regime > 0.25, 0.00015, np.where(regime < -0.25, -0.00015, 0.0))
    returns = drift + noise
    close = 100_000.0 * np.exp(np.cumsum(returns))
    funding_noise = rng.normal(0.0, 0.000015, periods)
    funding_rate = np.where(regime > 0.25, 0.00008, np.where(regime < -0.25, -0.00008, 0.0)) + funding_noise
    return pd.DataFrame({"close": close, "funding_rate": funding_rate}, index=index)


def make_portfolio_demo_data(periods: int = 800, markets: int = 8, seed: int = 11) -> tuple[pd.DataFrame, pd.DataFrame]:
    if periods < 200:
        raise ValueError("periods must be >= 200")
    if markets < 4:
        raise ValueError("markets must be >= 4")
    rng = np.random.default_rng(seed)
    index = pd.date_range("2026-01-01", periods=periods, freq="h", tz="UTC")
    columns = [f"MKT{i + 1}-USD" for i in range(markets)]
    common = rng.normal(0.0, 0.0025, periods)
    trend = np.sin(np.linspace(0, 12 * np.pi, periods))
    prices = {}; funding = {}
    for i, market in enumerate(columns):
        beta = 0.6 + 0.1 * (i % 4)
        idio = rng.normal(0.0, 0.002 + i * 0.00015, periods)
        tilt = ((i - (markets - 1) / 2) / markets) * 0.00045 * trend
        returns = beta * common + idio + tilt
        base = 50.0 + i * 25.0
        prices[market] = base * np.exp(np.cumsum(returns))
        funding[market] = np.sign(tilt) * 0.000025 + rng.normal(0.0, 0.00001, periods)
    return pd.DataFrame(prices, index=index), pd.DataFrame(funding, index=index)
