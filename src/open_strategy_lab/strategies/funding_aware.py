from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from .base import Strategy


@dataclass(frozen=True, slots=True)
class FundingAwareConfig:
    funding_window: int = 8
    momentum_window: int = 12
    volatility_window: int = 24
    min_abs_hourly_funding: float = 0.00005
    max_annualized_vol: float = 1.20

    def validate(self) -> None:
        for name in ("funding_window", "momentum_window", "volatility_window"):
            if getattr(self, name) < 2:
                raise ValueError(f"{name} must be >= 2")
        if self.min_abs_hourly_funding < 0: raise ValueError("min_abs_hourly_funding must be >= 0")
        if self.max_annualized_vol <= 0: raise ValueError("max_annualized_vol must be positive")


class FundingAwareStrategy(Strategy):
    def __init__(self, config: FundingAwareConfig | None = None) -> None:
        self.config=config or FundingAwareConfig(); self.config.validate()

    def signals(self, frame: pd.DataFrame) -> pd.Series:
        required={"close","funding_rate"}; missing=required.difference(frame.columns)
        if missing: raise ValueError(f"missing columns: {sorted(missing)}")
        close=frame["close"].astype(float); funding=frame["funding_rate"].astype(float)
        mean_funding=funding.rolling(self.config.funding_window,min_periods=self.config.funding_window).mean()
        momentum=close.pct_change(self.config.momentum_window)
        log_return=np.log(close).diff()
        annualized_vol=log_return.rolling(self.config.volatility_window,min_periods=self.config.volatility_window).std()*np.sqrt(24*365)
        tradable=annualized_vol<=self.config.max_annualized_vol
        short_setup=(mean_funding>=self.config.min_abs_hourly_funding)&(momentum<=0)&tradable
        long_setup=(mean_funding<=-self.config.min_abs_hourly_funding)&(momentum>=0)&tradable
        signal=pd.Series(0.0,index=frame.index,name="signal"); signal.loc[long_setup]=1.0; signal.loc[short_setup]=-1.0
        return signal.shift(1).fillna(0.0)
