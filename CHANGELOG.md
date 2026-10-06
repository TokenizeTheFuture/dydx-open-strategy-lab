# Changelog

## 0.6.0

- Added public dYdX WebSocket stream layer
- Added v4_candles subscription and parser
- Added v4_markets subscription and parser
- Added candle, oracle-price and next-funding-rate event models
- Added maintained mainnet WebSocket endpoint
- Added websocket-client dependency
- Explicitly kept nextFundingRate separate from confirmed funding settlement

## 0.5.0

- Added stateful paper broker for incremental market updates
- Added fill ledger and account snapshots
- Added mark-to-market, funding, fee and slippage accounting
- Added fractional target exposure support in paper mode
- Added replay-vs-backtest accounting regression test
- Added paper replay demo
- Kept wallet, signing and live-order handling out of scope

## 0.4.0

- Added volatility-regime adaptive reference strategy
- Added fractional target exposure support for single-market strategies
- Added rolling volatility regime classification
- Added configurable low/normal/high risk scaling
- Added future-data leakage and exposure behavior tests
- Added volatility-regime demo
- Generalized CI to all v0 development branches

## 0.3.1

- Added dedicated dYdX historical range loader
- Added forward candle pagination with explicit date windows
- Added backward historical funding pagination
- Added duplicate and boundary protection across API pages
- Added cached merged research frames with prior-known funding alignment
- Enabled CI for the v0.3 development branch

## 0.3.0

- Added local compressed CSV cache for research datasets
- Added walk-forward parameter selection and out-of-sample evaluation
- Added reusable backtesting from precomputed signals
- Added chained out-of-sample performance summary
- Added cache and walk-forward test coverage

## 0.2.1

- Fixed dYdX adapter tests for the slotted Indexer client
- Added historical funding response parsing coverage
- Re-ran the full offline test suite successfully

## 0.2.0

- Added multi-market dYdX data adapter helpers
- Added cross-sectional market-neutral momentum reference strategy
- Added portfolio backtester with funding, fees, slippage and turnover accounting
- Added portfolio exposure controls
- Added machine-readable and Markdown performance reports
- Added GitHub Actions test workflow
- Added MIT license and security guidance
- Expanded deterministic test coverage

## 0.1.0

- Initial research framework
- Public dYdX Indexer adapter
- Funding-aware reference strategy
- Event-driven single-market backtester with funding, fees and slippage
- Basic risk limits
- Synthetic demo and tests
