# dYdX Open Strategy Lab

Research-to-backtest and paper-trading tooling for systematic strategies on dYdX.

The project is deliberately research-first. v0.6.0 contains no wallet handling,
order signing or live-order code.

## Current reference strategies

### 1. Funding-Aware Directional Strategy

Uses persistent funding, momentum confirmation and realized volatility to decide
whether a carry-biased directional setup is tradable.

This is **not** presented as delta-neutral because there is no external hedge leg.

### 2. Cross-Sectional Market-Neutral Momentum

Ranks a basket of dYdX perpetual markets by volatility-adjusted momentum, holds
the strongest names long and the weakest names short, and keeps portfolio net
exposure close to zero.

### 3. Volatility-Regime Adaptive Strategy

Classifies realized volatility into low, normal and high regimes and scales
target exposure accordingly.

## Data layer

The public REST adapter follows the maintained dYdX Indexer endpoints used by
the official v4 clients:

- `GET /v4/perpetualMarkets`
- `GET /v4/candles/perpetualMarkets/{market}`
- `GET /v4/historicalFunding/{market}`

The public WebSocket layer follows:

- `v4_candles`
- `v4_markets`

Mainnet public WebSocket endpoint:

`wss://indexer.dydx.trade/v4/ws`

## Repository layout

```text
src/open_strategy_lab/
├── analytics.py
├── backtest.py
├── paper.py
├── portfolio_backtest.py
├── risk.py
├── stream.py
├── walkforward.py
├── data/
│   ├── cache.py
│   ├── dydx.py
│   ├── historical.py
│   └── synthetic.py
└── strategies/
    ├── base.py
    ├── portfolio_base.py
    ├── funding_aware.py
    ├── cross_sectional_momentum.py
    └── volatility_regime.py
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests

```bash
pytest -q
```

## Historical dYdX datasets

The historical loader pages explicit date ranges and can cache compressed CSV
datasets locally. Funding is aligned backward to candles so future funding
observations are never applied to prior candles.

## Walk-forward validation

Parameter selection occurs on a training window. The chosen configuration is
then evaluated on the next unseen window, and only out-of-sample results are
aggregated.

```bash
python examples/run_walk_forward_demo.py
```

## Stateful paper trading

The paper broker processes market observations incrementally and maintains
equity, open position, funding cash flow, transaction costs and fill history.

The paper accounting model is regression-tested against the batch backtester.

```bash
python examples/run_paper_demo.py
```

## Public market stream

The WebSocket layer can subscribe to candle and market updates without private
account access.

```python
from open_strategy_lab import PublicMarketStream

stream = PublicMarketStream(
    on_candle=print,
    on_market=print,
)

stream.add_candles("BTC-USD", "1HOUR")
stream.add_markets()
stream.run_forever()
```

The `v4_markets` feed may expose `nextFundingRate`. This is a forward-looking
market value and is **not treated as a confirmed funding payment** by the paper
broker. Confirmed funding settlement must come from an appropriate historical or
settlement data source before being booked into PnL.

## Scope

v0.6.0 is suitable for research, paper-trading experiments and grant-prototype
review. It is not production trading software and makes no claim that the
included strategies are profitable.

Wallet handling, signing and live order placement remain intentionally out of
scope.
