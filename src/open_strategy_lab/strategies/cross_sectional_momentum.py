from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from .portfolio_base import PortfolioStrategy


@dataclass(frozen=True, slots=True)
class CrossSectionalMomentumConfig:
    lookback_hours: int = 24
    volatility_window: int = 48
    rebalance_hours: int = 4
    long_count: int = 2
    short_count: int = 2
    gross_exposure: float = 1.0
    max_market_weight: float = 0.35
    min_markets: int = 4

    def validate(self) -> None:
        if self.lookback_hours < 2: raise ValueError("lookback_hours must be >= 2")
        if self.volatility_window < 2: raise ValueError("volatility_window must be >= 2")
        if self.rebalance_hours < 1: raise ValueError("rebalance_hours must be >= 1")
        if self.long_count < 1 or self.short_count < 1: raise ValueError("long_count and short_count must be positive")
        if self.gross_exposure <= 0: raise ValueError("gross_exposure must be positive")
        if not 0 < self.max_market_weight <= 1: raise ValueError("max_market_weight must be in (0, 1]")
        if self.min_markets < self.long_count + self.short_count: raise ValueError("min_markets is too small for requested long/short count")


class CrossSectionalMomentumStrategy(PortfolioStrategy):
    def __init__(self, config: CrossSectionalMomentumConfig | None = None) -> None:
        self.config=config or CrossSectionalMomentumConfig(); self.config.validate()

    def weights(self, prices: pd.DataFrame, funding: pd.DataFrame | None = None) -> pd.DataFrame:
        if prices.empty: return prices.copy()
        if prices.shape[1] < self.config.min_markets: raise ValueError(f"strategy requires at least {self.config.min_markets} markets")
        prices=prices.astype(float).sort_index(); log_prices=np.log(prices); momentum=log_prices.diff(self.config.lookback_hours); hourly_returns=log_prices.diff()
        realized_vol=hourly_returns.rolling(self.config.volatility_window,min_periods=self.config.volatility_window).std(); score=momentum/realized_vol.replace(0.0,np.nan)
        result=pd.DataFrame(0.0,index=prices.index,columns=prices.columns); current=pd.Series(0.0,index=prices.columns)
        for i,timestamp in enumerate(prices.index):
            if i % self.config.rebalance_hours != 0:
                result.loc[timestamp]=current; continue
            row=score.loc[timestamp].dropna()
            if len(row) < self.config.min_markets:
                current=pd.Series(0.0,index=prices.columns); result.loc[timestamp]=current; continue
            longs=row.nlargest(self.config.long_count).index; shorts=row.nsmallest(self.config.short_count).index
            long_budget=self.config.gross_exposure/2.0; short_budget=self.config.gross_exposure/2.0
            long_weight=min(long_budget/len(longs),self.config.max_market_weight); short_weight=min(short_budget/len(shorts),self.config.max_market_weight)
            current=pd.Series(0.0,index=prices.columns); current.loc[longs]=long_weight; current.loc[shorts]=-short_weight
            long_sum=current.clip(lower=0).sum(); short_sum=-current.clip(upper=0).sum(); balanced=min(long_sum,short_sum)
            if balanced > 0:
                if long_sum > 0: current.loc[current>0]*=balanced/long_sum
                if short_sum > 0: current.loc[current<0]*=balanced/short_sum
            result.loc[timestamp]=current
        return result.shift(1).fillna(0.0)
