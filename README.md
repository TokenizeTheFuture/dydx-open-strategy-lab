# dYdX Open Strategy Lab

Open Strategy Lab is a Python research, validation and paper-trading framework
for systematic strategies on dYdX.

The repository is intentionally research-first. It currently contains no
mnemonic handling, private-key storage, transaction signing or live order
placement.

## Reviewer quick start

A deterministic offline demonstration is included so the core framework can be
reviewed without an exchange account, wallet or network connection.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
osl-grant-demo
```

The demo writes reviewer artifacts to:

```text
artifacts/grant-demo/
├── README.md
├── summary.json
├── walk_forward_folds.csv
└── paper_fills.csv
```

Run the complete test suite with:

```bash
pytest -q
```

CI validates the repository on Python 3.11 and 3.12.

## What the demo exercises

The single command runs five independent parts of the framework:

1. funding-aware single-market backtesting;
2. volatility-regime adaptive backtesting;
3. cross-sectional market-neutral portfolio backtesting;
4. walk-forward out-of-sample validation;
5. stateful paper replay.

The paper replay and batch backtest are also compared as an accounting
consistency check.

The generated numbers are simulated research outputs. They are not presented as
profitability claims.

## Why this project exists

Many strategy repositories combine data access, strategy logic, parameter
selection and execution in one implementation. That makes it difficult to
identify overfitting, accounting errors or execution assumptions.

Open Strategy Lab separates:

```text
dYdX market data
      ↓
research datasets
      ↓
strategy logic
      ↓
validation / walk-forward testing
      ↓
backtest or paper execution
      ↓
analytics and reproducible outputs
```

The goal is a reusable framework rather than a single fixed trading bot.

## Current capabilities

### Market data

Public dYdX Indexer support includes:

- perpetual-market metadata;
- candles;
- historical funding;
- explicit historical date ranges;
- compressed local research cache;
- public `v4_candles` WebSocket parsing;
- public `v4_markets` WebSocket parsing.

The maintained mainnet public WebSocket endpoint is:

`wss://indexer.dydx.trade/v4/ws`

### Validation

The research layer includes:

- one-bar signal delay;
- fees and slippage;
- funding cash-flow accounting;
- leverage and exposure limits;
- walk-forward parameter selection;
- out-of-sample evaluation;
- future-data leakage regression tests;
- paper-vs-batch accounting equivalence tests.

### Paper trading

The stateful paper broker processes observations incrementally and maintains:

- open position;
- mark-to-market PnL;
- confirmed funding input;
- transaction costs;
- equity and drawdown;
- fill history.

The public market feed may expose `nextFundingRate`. This is forward-looking
market information and is not booked directly as a confirmed funding payment.

## Reference strategies

The repository includes three reference strategies used to exercise different
parts of the framework.

### Funding-Aware Directional Strategy

Uses persistent funding, momentum confirmation and realized volatility.

### Cross-Sectional Market-Neutral Momentum

Ranks a basket of perpetual markets by volatility-adjusted momentum and builds
balanced long/short exposure with gross and per-market risk limits.

### Volatility-Regime Adaptive Strategy

Uses rolling volatility regimes to scale target exposure instead of applying a
fixed position size.

These strategies are framework examples, not guaranteed profitable systems.

## Repository layout

```text
src/open_strategy_lab/
├── analytics.py
├── backtest.py
├── demo.py
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

## Network examples

Historical public data:

```bash
python examples/fetch_historical_range.py
```

Public WebSocket stream:

```bash
python examples/run_public_stream.py
```

Network examples are separate from the deterministic reviewer demo and unit
tests.

## Technical documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Research methodology](docs/RESEARCH_METHODOLOGY.md)
- [Technical status and milestones](docs/TECHNICAL_STATUS.md)
- [Proposed grant scope](docs/GRANT_SCOPE.md)

## Scope and safety boundary

v0.6.1 is a research and paper-trading prototype. Wallet handling, signing and
live order placement remain intentionally outside the current package.

A future execution adapter should remain isolated from the research layer and
use maintained dYdX clients with runtime-managed signing material.

## License

MIT.
