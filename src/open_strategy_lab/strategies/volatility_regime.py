from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import Strategy


@dataclass(frozen=True, slots=True)
class VolatilityRegimeConfig:
    momentum_window: int = 24
    volatility_window: int = 24
    regime_lookback: int = 24 * 14
    low_quantile: float = 0.35
    high_quantile: float = 0.70
    low_vol_exposure: float = 1.0
    normal_vol_exposure: float = 0.60
    high_vol_exposure: float = 0.25
    min_momentum: float = 0.002

    def validate(self) -> None:
        if self.momentum_window < 2:
            raise ValueError("momentum_window must be >= 2")
        if self.volatility_window < 2:
            raise ValueError("volatility_window must be >= 2")
        if self.regime_lookback < self.volatility_window:
            raise ValueError("regime_lookback must be >= volatility_window")
        if not 0 < self.low_quantile < self.high_quantile < 1:
            raise ValueError("quantiles must satisfy 0 < low < high < 1")
        for name in (
            "low_vol_exposure",
            "normal_vol_exposure",
            "high_vol_exposure",
        ):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.min_momentum < 0:
            raise ValueError("min_momentum must be non-negative")


class VolatilityRegimeStrategy(Strategy):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

    def __init__(self, config: VolatilityRegimeConfig | None = None) -> None:
        self.config = config or VolatilityRegimeConfig()
        self.config.validate()

    def regimes(self, frame: pd.DataFrame) -> pd.Series:
        if "close" not in frame:
            raise ValueError("missing columns: ['close']")

        close = frame["close"].astype(float)
        log_return = np.log(close).diff()
        realized_vol = (
            log_return.rolling(
                self.config.volatility_window,
                min_periods=self.config.volatility_window,
            ).std()
            * np.sqrt(24 * 365)
        )

        low_threshold = realized_vol.rolling(
            self.config.regime_lookback,
            min_periods=self.config.regime_lookback,
        ).quantile(self.config.low_quantile)
        high_threshold = realized_vol.rolling(
            self.config.regime_lookback,
            min_periods=self.config.regime_lookback,
        ).quantile(self.config.high_quantile)

        regime = pd.Series(
            self.NORMAL,
            index=frame.index,
            dtype="object",
            name="volatility_regime",
        )
        regime.loc[realized_vol <= low_threshold] = self.LOW
        regime.loc[realized_vol >= high_threshold] = self.HIGH
        regime.loc[realized_vol.isna() | low_threshold.isna() | high_threshold.isna()] = self.NORMAL
        return regime

    def signals(self, frame: pd.DataFrame) -> pd.Series:
        if "close" not in frame:
            raise ValueError("missing columns: ['close']")

        close = frame["close"].astype(float)
        momentum = close.pct_change(self.config.momentum_window)
        regime = self.regimes(frame)

        exposure = pd.Series(
            self.config.normal_vol_exposure,
            index=frame.index,
            dtype=float,
        )
        exposure.loc[regime == self.LOW] = self.config.low_vol_exposure
        exposure.loc[regime == self.HIGH] = self.config.high_vol_exposure

        direction = pd.Series(0.0, index=frame.index)
        direction.loc[momentum >= self.config.min_momentum] = 1.0
        direction.loc[momentum <= -self.config.min_momentum] = -1.0

        target = direction * exposure

        # Trade only on information known at the previous bar.
        return target.shift(1).fillna(0.0).rename("signal")
