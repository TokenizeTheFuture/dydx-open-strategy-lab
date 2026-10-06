# dYdX Open Strategy Lab

Research-to-backtest tooling for systematic strategies on dYdX.

The project is deliberately research-first. v0.4.0 contains no wallet handling,
order signing or live-order code.

## Current reference strategies

### 1. Funding-Aware Directional Strategy

Uses persistent funding, momentum confirmation and realized volatility to decide
whether a carry-biased directional setup is tradable.

This is **not** presented as delta-neutral because v0.2 has no external hedge leg.

### 2. Cross-Sectional Market-Neutral Momentum

Ranks a basket of dYdX perpetual markets by volatility-adjusted momentum, holds
the strongest names long and the weakest names short, and keeps portfolio net
exposure close to zero.

The implementation includes:

- fixed rebalance intervals
- volatility-adjusted rankings
- per-market weight caps
- gross exposure limits
- one-bar signal delay
- trading fees and slippage
- hourly funding cash flows
- turnover tracking

## Data layer

The public adapter follows the maintained dYdX Indexer endpoints used by the
official v4 clients:

- `GET /v4/perpetualMarkets`
- `GET /v4/candles/perpetualMarkets/{market}`
- `GET /v4/historicalFunding/{market}`

The Indexer is a read-only data layer. Any future live execution adapter should
use a maintained dYdX Chain client and keep signing material outside this package.

## Repository layout

```text
src/open_strategy_lab/
├── analytics.py
├── backtest.py
├── portfolio_backtest.py
├── risk.py
├── data/
│   ├── dydx.py
│   └── synthetic.py
└── strategies/
    ├── base.py
    ├── portfolio_base.py
    ├── funding_aware.py
    ├── cross_sectional_momentum.py\n    └── volatility_regime.py
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

## Single-market demo

```bash
python examples/run_demo.py
```

## Multi-market portfolio demo

```bash
python examples/run_portfolio_demo.py
```

The portfolio demo writes a JSON summary and a Markdown report under `artifacts/`.

## Public dYdX data example

```bash
python examples/fetch_multi_market.py
```

Network access is only required for the public-data examples. Unit tests and
synthetic demos are deterministic and work offline.

## Scope

v0.4.0 is suitable for research and grant-prototype review. It is not production
trading software and makes no claim that the included strategies are profitable.

Future milestones are expected to add longer historical-data collection,
walk-forward validation, paper trading and a separate
execution adapter.


## Historical dYdX datasets

The historical loader collects explicit date ranges rather than relying on a
single API response. Candle requests page forward using `fromISO` and `toISO`.
Historical funding pages backward using `effectiveBeforeOrAt`.

```python
from open_strategy_lab.data import CsvCache, DydxHistoricalData, DydxIndexer

loader = DydxHistoricalData(
    DydxIndexer(),
    cache=CsvCache(".cache/open_strategy_lab"),
)

frame = loader.research_frame(
    "BTC-USD",
    "2026-09-01T00:00:00Z",
    "2026-09-07T00:00:00Z",
)
```

Funding values are aligned backward to candles so a candle never receives a
funding observation from the future.

## Walk-forward validation

The framework can select strategy parameters on a training window and then
evaluate the chosen configuration on the next unseen test window. The process
rolls forward and aggregates out-of-sample results only.

```bash
python examples/run_walk_forward_demo.py
```

This is intended to make overfitting easier to detect before a strategy reaches
paper or live trading.


## Volatility-regime adaptive strategy

The third reference strategy changes target exposure rather than using a fixed
position size. It classifies realized volatility into low, normal and high
regimes using rolling quantiles, then scales a momentum signal accordingly.

Typical defaults:

- low volatility: 1.00x target exposure
- normal volatility: 0.60x
- high volatility: 0.25x

The signal remains delayed by one bar, and tests include a future-data leakage
check.

```bash
python examples/run_volatility_regime_demo.py
```
