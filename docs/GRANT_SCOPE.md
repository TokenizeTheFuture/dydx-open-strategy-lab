# Grant Scope

## dYdX Open Strategy Lab

**Proposed duration:** 10 weeks  
**Proposed funding request:** $24,000  
**Project type:** Open-source research, strategy tooling and paper-trading infrastructure

## Current prototype

The repository already contains a working research prototype rather than only a
project concept.

Implemented today:

- dYdX public REST market-data adapter
- explicit historical candle and funding ranges
- local research-data cache
- event-driven single-market backtesting
- multi-market portfolio backtesting
- fee, slippage and funding accounting
- walk-forward parameter selection
- out-of-sample evaluation
- stateful paper broker
- public dYdX WebSocket market-data parsing
- Python 3.11 and 3.12 CI
- three reference strategies

The grant would therefore fund hardening, execution-quality improvements and
public developer usability rather than initial proof-of-concept work.

## Reference strategies

### Funding-Aware Directional Strategy

Tests whether persistent funding conditions remain attractive after momentum,
volatility, fees, slippage and funding cash flows are included.

### Cross-Sectional Market-Neutral Momentum

Ranks dYdX perpetual markets by volatility-adjusted momentum and constructs
balanced long/short exposure with gross and per-market limits.

### Volatility-Regime Adaptive Strategy

Changes target exposure according to rolling low, normal and high volatility
regimes instead of using a fixed risk level.

These strategies are examples for the framework and are not presented as
guaranteed profitable systems.

## Milestone 1 — Research Core Hardening

**Weeks 1–2 — $4,000**

Deliverables:

- reproducible historical dYdX research datasets
- dataset integrity and continuity checks
- richer performance attribution
- improved experiment configuration
- benchmark reports for included strategies

## Milestone 2 — Strategy Validation Framework

**Weeks 3–4 — $6,000**

Deliverables:

- expanded walk-forward validation
- parameter-stability analysis
- strategy comparison reports
- drawdown, turnover, funding and fee attribution
- reproducible experiment output

## Milestone 3 — Paper Trading and Public Streaming

**Weeks 5–7 — $7,000**

Deliverables:

- public market-stream to strategy bridge
- candle-close processing
- persistent paper-session state
- confirmed funding-settlement synchronization
- paper fills and account-state reporting
- failure/reconnect handling

No private keys or live order placement are required for this milestone.

## Milestone 4 — Execution-Ready Interfaces and Release

**Weeks 8–10 — $7,000**

Deliverables:

- isolated execution interface
- maintained dYdX client adapter design
- order and position state-machine tests
- execution risk controls and kill-switch interfaces
- strategy-authoring guide
- API documentation
- end-to-end examples
- public open-source release

Live capital deployment is not required to complete the grant.

## Budget

| Milestone | Amount |
| --- | ---: |
| Research Core Hardening | $4,000 |
| Strategy Validation Framework | $6,000 |
| Paper Trading and Public Streaming | $7,000 |
| Execution-Ready Interfaces and Release | $7,000 |
| **Total** | **$24,000** |

## Why this is different from a single trading bot

Open Strategy Lab is not a grant request for one fixed grid, TWAP, market-making
or arbitrage bot.

The core deliverable is a reusable framework that separates:

- market data
- strategy logic
- validation
- portfolio/risk controls
- paper execution
- future live execution adapters

New strategies can be evaluated through the same accounting and validation
pipeline instead of each strategy requiring a separate one-off codebase.

## Success criteria

A successful grant should leave dYdX developers and traders with:

- a public reusable Python framework;
- reproducible strategy experiments;
- realistic fee, funding and slippage accounting;
- out-of-sample validation tools;
- a public-data-driven paper trading workflow;
- documented interfaces for future execution integration;
- three maintained reference strategies.

The project should be judged primarily on reproducibility, correctness,
developer usability and delivery of the open-source tooling, not on a promise
of trading profitability or a guaranteed volume target.
