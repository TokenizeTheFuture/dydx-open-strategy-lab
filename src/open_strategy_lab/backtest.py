from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

from .risk import RiskConfig
from .strategies.base import Strategy


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_equity: float = 10_000.0
    fee_bps: float = 5.0
    slippage_bps: float = 2.0
    target_leverage: float = 1.0

    def validate(self) -> None:
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        if self.fee_bps < 0 or self.slippage_bps < 0:
            raise ValueError("fee and slippage must be non-negative")
        if self.target_leverage <= 0:
            raise ValueError("target_leverage must be positive")


@dataclass(frozen=True, slots=True)
class BacktestResult:
    ledger: pd.DataFrame
    summary: dict[str, float]


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def _annualized_sharpe(returns: pd.Series) -> float:
    clean = returns.replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 2:
        return 0.0
    std = clean.std(ddof=1)
    if std == 0:
        return 0.0
    return float(clean.mean() / std * math.sqrt(24 * 365))


def run_backtest_with_signals(
    frame: pd.DataFrame,
    signals: pd.Series,
    config: BacktestConfig | None = None,
    risk: RiskConfig | None = None,
) -> BacktestResult:
    config = config or BacktestConfig()
    risk = risk or RiskConfig()
    config.validate()
    risk.validate()

    if config.target_leverage > risk.max_leverage:
        raise ValueError("target_leverage exceeds risk.max_leverage")

    required = {"close", "funding_rate"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if len(frame) < 2:
        raise ValueError("at least 2 rows are required")

    data = frame.sort_index().copy()
    data["signal"] = signals.reindex(data.index).fillna(0.0).astype(float).clip(-1.0, 1.0)

    equity = float(config.initial_equity)
    qty = 0.0
    previous_price = float(data["close"].iloc[0])
    peak_equity = equity
    rows: list[dict[str, float]] = []
    friction_rate = (config.fee_bps + config.slippage_bps) / 10_000.0

    for timestamp, row in data.iterrows():
        price = float(row["close"])
        funding_rate = float(row["funding_rate"])
        signal = float(row["signal"])

        mark_pnl = qty * (price - previous_price)
        funding_pnl = -(qty * price) * funding_rate
        equity += mark_pnl + funding_pnl

        if equity < risk.min_equity:
            signal = 0.0

        target_notional = equity * config.target_leverage * signal
        target_qty = 0.0 if price <= 0 else target_notional / price

        turnover = abs(target_qty - qty) * price
        trading_cost = turnover * friction_rate
        equity -= trading_cost
        qty = target_qty

        peak_equity = max(peak_equity, equity)
        drawdown = 0.0 if peak_equity == 0 else equity / peak_equity - 1.0

        rows.append(
            {
                "timestamp": timestamp,
                "close": price,
                "funding_rate": funding_rate,
                "signal": signal,
                "position_qty": qty,
                "position_notional": qty * price,
                "mark_pnl": mark_pnl,
                "funding_pnl": funding_pnl,
                "trading_cost": trading_cost,
                "equity": equity,
                "drawdown": drawdown,
            }
        )
        previous_price = price

    ledger = pd.DataFrame(rows).set_index("timestamp")
    returns = ledger["equity"].pct_change()
    total_return = ledger["equity"].iloc[-1] / config.initial_equity - 1.0

    summary = {
        "initial_equity": float(config.initial_equity),
        "final_equity": float(ledger["equity"].iloc[-1]),
        "total_return": float(total_return),
        "max_drawdown": _max_drawdown(ledger["equity"]),
        "sharpe": _annualized_sharpe(returns),
        "funding_pnl": float(ledger["funding_pnl"].sum()),
        "mark_pnl": float(ledger["mark_pnl"].sum()),
        "trading_cost": float(ledger["trading_cost"].sum()),
        "turnover_events": float((ledger["position_qty"].diff().abs() > 1e-12).sum()),
    }
    return BacktestResult(ledger=ledger, summary=summary)


def run_backtest(
    frame: pd.DataFrame,
    strategy: Strategy,
    config: BacktestConfig | None = None,
    risk: RiskConfig | None = None,
) -> BacktestResult:
    if len(frame) < 3:
        raise ValueError("at least 3 rows are required")
    return run_backtest_with_signals(
        frame,
        strategy.signals(frame),
        config=config,
        risk=risk,
    )
