from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import httpx
import pandas as pd


@dataclass(slots=True)
class DydxIndexer:
    base_url: str = "https://indexer.dydx.trade"
    timeout: float = 15.0

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url=f"{self.base_url.rstrip('/')}{path}"; clean_params={k:v for k,v in (params or {}).items() if v is not None}
        with httpx.Client(timeout=self.timeout) as client:
            response=client.get(url,params=clean_params); response.raise_for_status(); return response.json()

    def perpetual_markets(self, ticker: str | None = None) -> dict[str, Any]:
        return self._get("/v4/perpetualMarkets",{"ticker":ticker}).get("markets",{})

    def candles(self,ticker:str,resolution:str="1HOUR",limit:int=100,from_iso:str|None=None,to_iso:str|None=None)->pd.DataFrame:
        payload=self._get(f"/v4/candles/perpetualMarkets/{ticker}",{"resolution":resolution,"fromISO":from_iso,"toISO":to_iso,"limit":limit}); rows=payload.get("candles",[])
        if not rows: return pd.DataFrame(columns=["close"])
        frame=pd.DataFrame(rows); time_col="startedAt" if "startedAt" in frame.columns else "updatedAt"; frame[time_col]=pd.to_datetime(frame[time_col],utc=True); frame["close"]=pd.to_numeric(frame["close"],errors="raise"); return frame.set_index(time_col).sort_index()[["close"]]

    def historical_funding(self,ticker:str,limit:int=100,effective_before_or_at:str|None=None)->pd.DataFrame:
        payload=self._get(f"/v4/historicalFunding/{ticker}",{"limit":limit,"effectiveBeforeOrAt":effective_before_or_at}); rows=payload.get("historicalFunding",[])
        if not rows: return pd.DataFrame(columns=["funding_rate"])
        frame=pd.DataFrame(rows); time_col="effectiveAt" if "effectiveAt" in frame.columns else "createdAt"; rate_col="rate" if "rate" in frame.columns else "fundingRate"; frame[time_col]=pd.to_datetime(frame[time_col],utc=True); frame["funding_rate"]=pd.to_numeric(frame[rate_col],errors="raise"); return frame.set_index(time_col).sort_index()[["funding_rate"]]

    def research_frame(self,ticker:str,resolution:str="1HOUR",limit:int=100)->pd.DataFrame:
        candles=self.candles(ticker,resolution=resolution,limit=limit); funding=self.historical_funding(ticker,limit=limit)
        if candles.empty or funding.empty: return pd.DataFrame(columns=["close","funding_rate"])
        return pd.merge_asof(candles.sort_index(),funding.sort_index(),left_index=True,right_index=True,direction="backward").dropna()

    def market_panel(self,tickers:Iterable[str],resolution:str="1HOUR",limit:int=100)->tuple[pd.DataFrame,pd.DataFrame]:
        price_series=[]; funding_series=[]
        for ticker in tickers:
            research=self.research_frame(ticker,resolution=resolution,limit=limit)
            if research.empty: continue
            price_series.append(research["close"].rename(ticker)); funding_series.append(research["funding_rate"].rename(ticker))
        if not price_series: return pd.DataFrame(),pd.DataFrame()
        prices=pd.concat(price_series,axis=1).sort_index(); funding=pd.concat(funding_series,axis=1).sort_index(); common_index=prices.dropna().index.intersection(funding.dropna().index); return prices.loc[common_index],funding.loc[common_index]
