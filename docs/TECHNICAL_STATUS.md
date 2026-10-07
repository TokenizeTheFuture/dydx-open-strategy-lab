# Technical Status

## Implemented

### Market data
- dYdX public REST adapter
- explicit historical candle ranges
- historical funding pagination
- local compressed CSV cache
- public candle WebSocket parsing
- public market WebSocket parsing

### Research
- single-market strategy interface
- portfolio strategy interface
- funding-aware reference strategy
- cross-sectional market-neutral momentum strategy
- volatility-regime adaptive strategy

### Simulation
- event-driven single-market backtester
- portfolio backtester
- funding, fees and slippage accounting
- stateful paper broker
- fill and account snapshot history

### Validation
- walk-forward parameter selection
- out-of-sample evaluation
- future-data leakage tests
- paper/backtest accounting equivalence
- Python 3.11 / 3.12 CI
- public WebSocket channel and payload shapes checked against the maintained dYdX v4 client source

## Integration validation status

The REST and WebSocket adapters are covered by deterministic unit tests and are
implemented against the maintained dYdX v4 client schemas.

The current CI environment does **not** perform an end-to-end mainnet WebSocket
connection test. A real-network smoke test is therefore still required before
the public stream is described as production-validated.

Likewise, the repository currently contains no live order execution path.

## Intentionally not implemented yet

- wallet or mnemonic handling
- transaction signing
- private account WebSocket streams
- live order placement
- cross-exchange hedge execution

## Recommended grant milestones

### Milestone 1 — Research core hardening
- longer reproducible dYdX datasets
- dataset integrity checks
- richer performance attribution
- parameter-stability reports

### Milestone 2 — Paper-trading session
- mainnet public-stream smoke tests
- candle-close event handling
- public stream to strategy bridge
- confirmed funding settlement synchronization
- persistent paper-session state

### Milestone 3 — Execution adapter
- maintained dYdX Chain client integration
- order state machine
- position reconciliation
- kill switch and execution risk controls

### Milestone 4 — Release and documentation
- end-to-end examples
- strategy authoring guide
- API documentation
- reproducible experiment reports
