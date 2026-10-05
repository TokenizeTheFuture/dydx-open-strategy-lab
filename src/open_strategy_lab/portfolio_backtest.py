from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

from .strategies.portfolio_base import PortfolioStrategy

@dataclass(frozen=True, slots=True)
class PortfolioBacktestConfig:
    initial_equity: float=10_000.0
    fee_bps: float=5.0
    slippage_bps: float=2.0
    max_gross_exposure: float=1.0
    max_market_weight: float=0.35
    def validate(self)->None:
        if self.initial_equity<=0: raise ValueError("initial_equity must be positive")
        if self.fee_bps<0 or self.slippage_bps<0: raise ValueError("fee and slippage must be non-negative")
        if self.max_gross_exposure<=0: raise ValueError("max_gross_exposure must be positive")
        if not 0<self.max_market_weight<=1: raise ValueError("max_market_weight must be in (0, 1]")

@dataclass(frozen=True, slots=True)
class PortfolioBacktestResult:
    ledger: pd.DataFrame
    weights: pd.DataFrame
    summary: dict[str,float]

def _align_frames(prices: pd.DataFrame,funding: pd.DataFrame|None)->tuple[pd.DataFrame,pd.DataFrame]:
    prices=prices.astype(float).sort_index().dropna(how="all").ffill().dropna()
    if funding is None: funding=pd.DataFrame(0.0,index=prices.index,columns=prices.columns)
    else: funding=funding.astype(float).reindex(index=prices.index,columns=prices.columns).ffill().fillna(0.0)
    return prices,funding

def _sharpe(hourly_returns: pd.Series)->float:
    clean=hourly_returns.replace([np.inf,-np.inf],np.nan).dropna()
    if len(clean)<2: return 0.0
    sd=clean.std(ddof=1)
    if sd==0: return 0.0
    return float(clean.mean()/sd*math.sqrt(24*365))

def run_portfolio_backtest(prices: pd.DataFrame,funding: pd.DataFrame|None,strategy: PortfolioStrategy,config: PortfolioBacktestConfig|None=None)->PortfolioBacktestResult:
    config=config or PortfolioBacktestConfig(); config.validate(); prices,funding=_align_frames(prices,funding)
    if len(prices)<3: raise ValueError("at least 3 aligned rows are required")
    if prices.shape[1]<2: raise ValueError("at least two markets are required")
    weights=strategy.weights(prices,funding).reindex_like(prices).fillna(0.0)
    if (weights.abs()>config.max_market_weight+1e-12).any().any(): raise ValueError("strategy produced a market weight above max_market_weight")
    gross=weights.abs().sum(axis=1)
    if (gross>config.max_gross_exposure+1e-12).any(): raise ValueError("strategy produced gross exposure above configured maximum")
    equity=float(config.initial_equity); previous_weights=pd.Series(0.0,index=prices.columns); rows=[]; friction=(config.fee_bps+config.slippage_bps)/10_000.0; simple_returns=prices.pct_change().fillna(0.0)
    for timestamp in prices.index:
        target=weights.loc[timestamp]; market_return=simple_returns.loc[timestamp]; funding_row=funding.loc[timestamp]
        mark_return=float((previous_weights*market_return).sum()); funding_return=float((-previous_weights*funding_row).sum()); turnover=float((target-previous_weights).abs().sum()); trading_cost_return=turnover*friction
        portfolio_return=mark_return+funding_return-trading_cost_return; equity*=1.0+portfolio_return
        rows.append({"timestamp":timestamp,"equity":equity,"portfolio_return":portfolio_return,"mark_return":mark_return,"funding_return":funding_return,"trading_cost_return":trading_cost_return,"turnover":turnover,"gross_exposure":float(target.abs().sum()),"net_exposure":float(target.sum()),"active_markets":float((target.abs()>1e-12).sum())}); previous_weights=target
    ledger=pd.DataFrame(rows).set_index("timestamp"); peak=ledger["equity"].cummax(); drawdown=ledger["equity"]/peak-1.0; ledger["drawdown"]=drawdown
    summary={"initial_equity":config.initial_equity,"final_equity":float(ledger["equity"].iloc[-1]),"total_return":float(ledger["equity"].iloc[-1]/config.initial_equity-1.0),"max_drawdown":float(drawdown.min()),"sharpe":_sharpe(ledger["portfolio_return"]),"mark_return_sum":float(ledger["mark_return"].sum()),"funding_return_sum":float(ledger["funding_return"].sum()),"trading_cost_return_sum":float(ledger["trading_cost_return"].sum()),"turnover_sum":float(ledger["turnover"].sum()),"average_gross_exposure":float(ledger["gross_exposure"].mean()),"average_abs_net_exposure":float(ledger["net_exposure"].abs().mean())}
    return PortfolioBacktestResult(ledger=ledger,weights=weights,summary=summary)
