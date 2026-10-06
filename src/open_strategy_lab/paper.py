from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd

from .backtest import BacktestConfig
from .risk import RiskConfig


@dataclass(frozen=True, slots=True)
class PaperFill:
    timestamp: pd.Timestamp
    price: float
    quantity_delta: float
    notional: float
    trading_cost: float


@dataclass(frozen=True, slots=True)
class PaperSnapshot:
    timestamp: pd.Timestamp
    close: float
    funding_rate: float
    signal: float
    position_qty: float
    position_notional: float
    mark_pnl: float
    funding_pnl: float
    trading_cost: float
    equity: float
    drawdown: float


@dataclass(slots=True)
class PaperBroker:
    config: BacktestConfig = field(default_factory=BacktestConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    equity: float = field(init=False)
    position_qty: float = field(init=False, default=0.0)
    previous_price: float | None = field(init=False, default=None)
    peak_equity: float = field(init=False)
    fills: list[PaperFill] = field(init=False, default_factory=list)
    snapshots: list[PaperSnapshot] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.config.validate()
        self.risk.validate()

        if self.config.target_leverage > self.risk.max_leverage:
            raise ValueError("target_leverage exceeds risk.max_leverage")

        self.equity = float(self.config.initial_equity)
        self.peak_equity = self.equity

    @property
    def friction_rate(self) -> float:
        return (self.config.fee_bps + self.config.slippage_bps) / 10_000.0

    def step(
        self,
        timestamp: pd.Timestamp,
        price: float,
        funding_rate: float,
        target_exposure: float,
    ) -> PaperSnapshot:
        price = float(price)
        funding_rate = float(funding_rate)
        target_exposure = float(np.clip(target_exposure, -1.0, 1.0))

        if price <= 0:
            raise ValueError("price must be positive")

        mark_pnl = 0.0
        if self.previous_price is not None:
            mark_pnl = self.position_qty * (price - self.previous_price)

        funding_pnl = -(self.position_qty * price) * funding_rate
        self.equity += mark_pnl + funding_pnl

        if self.equity < self.risk.min_equity:
            target_exposure = 0.0

        target_notional = (
            self.equity
            * self.config.target_leverage
            * target_exposure
        )
        target_qty = target_notional / price
        quantity_delta = target_qty - self.position_qty
        turnover = abs(quantity_delta) * price
        trading_cost = turnover * self.friction_rate
        self.equity -= trading_cost

        if abs(quantity_delta) > 1e-12:
            self.fills.append(
                PaperFill(
                    timestamp=pd.Timestamp(timestamp),
                    price=price,
                    quantity_delta=quantity_delta,
                    notional=turnover,
                    trading_cost=trading_cost,
                )
            )

        self.position_qty = target_qty
        self.previous_price = price

        self.peak_equity = max(self.peak_equity, self.equity)
        drawdown = (
            0.0
            if self.peak_equity == 0
            else self.equity / self.peak_equity - 1.0
        )

        snapshot = PaperSnapshot(
            timestamp=pd.Timestamp(timestamp),
            close=price,
            funding_rate=funding_rate,
            signal=target_exposure,
            position_qty=self.position_qty,
            position_notional=self.position_qty * price,
            mark_pnl=mark_pnl,
            funding_pnl=funding_pnl,
            trading_cost=trading_cost,
            equity=self.equity,
            drawdown=drawdown,
        )
        self.snapshots.append(snapshot)
        return snapshot

    def ledger(self) -> pd.DataFrame:
        if not self.snapshots:
            return pd.DataFrame()

        frame = pd.DataFrame(
            [
                {
                    "timestamp": item.timestamp,
                    "close": item.close,
                    "funding_rate": item.funding_rate,
                    "signal": item.signal,
                    "position_qty": item.position_qty,
                    "position_notional": item.position_notional,
                    "mark_pnl": item.mark_pnl,
                    "funding_pnl": item.funding_pnl,
                    "trading_cost": item.trading_cost,
                    "equity": item.equity,
                    "drawdown": item.drawdown,
                }
                for item in self.snapshots
            ]
        )
        return frame.set_index("timestamp")

    def fills_frame(self) -> pd.DataFrame:
        if not self.fills:
            return pd.DataFrame(
                columns=[
                    "price",
                    "quantity_delta",
                    "notional",
                    "trading_cost",
                ]
            )

        frame = pd.DataFrame(
            [
                {
                    "timestamp": item.timestamp,
                    "price": item.price,
                    "quantity_delta": item.quantity_delta,
                    "notional": item.notional,
                    "trading_cost": item.trading_cost,
                }
                for item in self.fills
            ]
        )
        return frame.set_index("timestamp")


@dataclass(frozen=True, slots=True)
class PaperReplayResult:
    ledger: pd.DataFrame
    fills: pd.DataFrame
    summary: dict[str, float]


def run_paper_replay(
    frame: pd.DataFrame,
    signals: pd.Series,
    config: BacktestConfig | None = None,
    risk: RiskConfig | None = None,
) -> PaperReplayResult:
    required = {"close", "funding_rate"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if len(frame) < 2:
        raise ValueError("at least 2 rows are required")

    broker = PaperBroker(
        config=config or BacktestConfig(),
        risk=risk or RiskConfig(),
    )

    data = frame.sort_index()
    aligned_signals = (
        signals.reindex(data.index)
        .fillna(0.0)
        .astype(float)
        .clip(-1.0, 1.0)
    )

    for timestamp, row in data.iterrows():
        broker.step(
            timestamp=timestamp,
            price=float(row["close"]),
            funding_rate=float(row["funding_rate"]),
            target_exposure=float(aligned_signals.loc[timestamp]),
        )

    ledger = broker.ledger()
    returns = ledger["equity"].pct_change()
    clean = returns.replace([np.inf, -np.inf], np.nan).dropna()

    sharpe = 0.0
    if len(clean) >= 2:
        std = clean.std(ddof=1)
        if std != 0:
            sharpe = float(
                clean.mean()
                / std
                * np.sqrt(24 * 365)
            )

    summary = {
        "initial_equity": float(broker.config.initial_equity),
        "final_equity": float(ledger["equity"].iloc[-1]),
        "total_return": float(
            ledger["equity"].iloc[-1]
            / broker.config.initial_equity
            - 1.0
        ),
        "max_drawdown": float(ledger["drawdown"].min()),
        "sharpe": sharpe,
        "funding_pnl": float(ledger["funding_pnl"].sum()),
        "mark_pnl": float(ledger["mark_pnl"].sum()),
        "trading_cost": float(ledger["trading_cost"].sum()),
        "fills": float(len(broker.fills)),
    }

    return PaperReplayResult(
        ledger=ledger,
        fills=broker.fills_frame(),
        summary=summary,
    )
