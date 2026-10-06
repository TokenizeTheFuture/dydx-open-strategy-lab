from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Iterable, Mapping, Any

import numpy as np
import pandas as pd

from .backtest import BacktestConfig, run_backtest, run_backtest_with_signals
from .risk import RiskConfig
from .strategies.base import Strategy


@dataclass(frozen=True, slots=True)
class WalkForwardConfig:
    train_bars: int = 24 * 30
    test_bars: int = 24 * 7
    step_bars: int | None = None
    warmup_bars: int = 72
    objective: str = "sharpe"

    def validate(self) -> None:
        if self.train_bars < 10:
            raise ValueError("train_bars must be >= 10")
        if self.test_bars < 2:
            raise ValueError("test_bars must be >= 2")
        if self.step_bars is not None and self.step_bars < 1:
            raise ValueError("step_bars must be positive")
        if self.warmup_bars < 1:
            raise ValueError("warmup_bars must be positive")
        if self.objective not in {"sharpe", "total_return"}:
            raise ValueError("objective must be 'sharpe' or 'total_return'")


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    folds: pd.DataFrame
    summary: dict[str, float]


def expand_grid(grid: Mapping[str, Iterable[Any]]) -> list[dict[str, Any]]:
    keys = list(grid)
    values = [list(grid[key]) for key in keys]
    if not keys or any(len(items) == 0 for items in values):
        raise ValueError("parameter grid cannot be empty")
    return [dict(zip(keys, combo)) for combo in product(*values)]


def run_walk_forward(
    frame: pd.DataFrame,
    strategy_factory: Callable[[dict[str, Any]], Strategy],
    parameter_grid: Mapping[str, Iterable[Any]],
    walk_config: WalkForwardConfig | None = None,
    backtest_config: BacktestConfig | None = None,
    risk: RiskConfig | None = None,
) -> WalkForwardResult:
    walk_config = walk_config or WalkForwardConfig()
    backtest_config = backtest_config or BacktestConfig()
    risk = risk or RiskConfig()

    walk_config.validate()
    data = frame.sort_index().copy()
    if len(data) < walk_config.train_bars + walk_config.test_bars:
        raise ValueError("not enough rows for one walk-forward fold")

    candidates = expand_grid(parameter_grid)
    step = walk_config.step_bars or walk_config.test_bars
    rows: list[dict[str, Any]] = []

    train_start = 0
    fold_id = 0

    while True:
        train_end = train_start + walk_config.train_bars
        test_end = train_end + walk_config.test_bars
        if test_end > len(data):
            break

        train = data.iloc[train_start:train_end]
        test = data.iloc[train_end:test_end]

        scored: list[tuple[float, dict[str, Any]]] = []
        for params in candidates:
            strategy = strategy_factory(params)
            result = run_backtest(
                train,
                strategy,
                config=backtest_config,
                risk=risk,
            )
            score = float(result.summary[walk_config.objective])
            if np.isnan(score):
                score = -np.inf
            scored.append((score, params))

        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, best_params = scored[0]

        warmup_start = max(0, train_end - walk_config.warmup_bars)
        signal_frame = data.iloc[warmup_start:test_end]
        best_strategy = strategy_factory(best_params)
        signals = best_strategy.signals(signal_frame).reindex(test.index).fillna(0.0)

        out_of_sample = run_backtest_with_signals(
            test,
            signals,
            config=backtest_config,
            risk=risk,
        )

        rows.append(
            {
                "fold": fold_id,
                "train_start": train.index[0],
                "train_end": train.index[-1],
                "test_start": test.index[0],
                "test_end": test.index[-1],
                "train_score": best_score,
                "test_total_return": out_of_sample.summary["total_return"],
                "test_sharpe": out_of_sample.summary["sharpe"],
                "test_max_drawdown": out_of_sample.summary["max_drawdown"],
                "test_trading_cost": out_of_sample.summary["trading_cost"],
                "selected_params": best_params,
            }
        )

        fold_id += 1
        train_start += step

    folds = pd.DataFrame(rows)
    if folds.empty:
        raise RuntimeError("walk-forward produced no folds")

    chained_return = float(np.prod(1.0 + folds["test_total_return"]) - 1.0)
    summary = {
        "folds": float(len(folds)),
        "chained_out_of_sample_return": chained_return,
        "average_test_return": float(folds["test_total_return"].mean()),
        "median_test_return": float(folds["test_total_return"].median()),
        "average_test_sharpe": float(folds["test_sharpe"].mean()),
        "worst_test_drawdown": float(folds["test_max_drawdown"].min()),
        "positive_fold_ratio": float((folds["test_total_return"] > 0).mean()),
        "total_test_trading_cost": float(folds["test_trading_cost"].sum()),
    }
    return WalkForwardResult(folds=folds, summary=summary)
