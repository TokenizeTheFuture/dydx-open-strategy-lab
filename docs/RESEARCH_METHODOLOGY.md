# Research Methodology

The framework is designed to make weak strategies fail visibly rather than make
historical results look attractive.

## No same-bar execution

Reference strategies delay target signals by one bar. Information observed on a
bar is not used to trade that same bar in the backtester.

## Trading friction

Backtests and paper replay include configurable:

- trading fees
- slippage
- funding cash flows

Headline gross returns are therefore not treated as sufficient evidence.

## Exposure controls

Single-market strategies produce target exposure in `[-1, 1]`.

Portfolio strategies enforce:

- maximum gross exposure
- maximum per-market exposure
- long/short balance where applicable

## Walk-forward validation

Parameter search and evaluation are separated.

For each fold:

1. choose parameters on the training window;
2. lock the chosen configuration;
3. evaluate it on the next unseen test window;
4. roll forward;
5. aggregate only out-of-sample results.

This does not eliminate overfitting, but it makes simple in-sample curve fitting
harder to hide.

## Leakage tests

Tests currently verify that changing future price observations does not alter
earlier volatility-regime signals.

## Paper/backtest consistency

The stateful paper broker is regression-tested against the batch backtester. The
same data and signal stream must produce matching:

- final equity
- mark PnL
- funding PnL
- transaction costs

## Interpretation

The included strategies are reference implementations used to validate the
framework.

A strategy producing negative results is not considered a framework failure.
It may instead demonstrate that realistic fees, funding, turnover or
out-of-sample testing invalidate the trading idea.
