import numpy as np
import pandas as pd

from open_strategy_lab.backtest import (
    BacktestConfig,
    run_backtest_with_signals,
)
from open_strategy_lab.data.synthetic import make_demo_data
from open_strategy_lab.paper import PaperBroker, run_paper_replay
from open_strategy_lab.risk import RiskConfig
from open_strategy_lab.strategies.funding_aware import (
    FundingAwareStrategy,
)


def test_paper_replay_matches_batch_backtest():
    frame = make_demo_data(periods=400, seed=51)
    signals = FundingAwareStrategy().signals(frame)
    config = BacktestConfig(
        initial_equity=10_000,
        fee_bps=5,
        slippage_bps=2,
        target_leverage=0.75,
    )
    risk = RiskConfig(max_leverage=1.0, min_equity=500)

    batch = run_backtest_with_signals(
        frame,
        signals,
        config=config,
        risk=risk,
    )
    replay = run_paper_replay(
        frame,
        signals,
        config=config,
        risk=risk,
    )

    assert replay.summary["final_equity"] == batch.summary["final_equity"]
    assert replay.summary["funding_pnl"] == batch.summary["funding_pnl"]
    assert replay.summary["mark_pnl"] == batch.summary["mark_pnl"]
    assert replay.summary["trading_cost"] == batch.summary["trading_cost"]

    pd.testing.assert_series_equal(
        replay.ledger["equity"],
        batch.ledger["equity"],
    )


def test_broker_records_fill_when_target_changes():
    broker = PaperBroker(
        BacktestConfig(target_leverage=1.0),
        RiskConfig(max_leverage=1.0),
    )

    t0 = pd.Timestamp("2026-01-01T00:00:00Z")
    broker.step(t0, 100.0, 0.0, 0.0)
    broker.step(t0 + pd.Timedelta(hours=1), 101.0, 0.0, 0.5)

    assert len(broker.fills) == 1
    assert broker.fills[0].quantity_delta > 0
    assert broker.fills[0].trading_cost > 0


def test_target_exposure_is_clipped():
    broker = PaperBroker(
        BacktestConfig(target_leverage=1.0),
        RiskConfig(max_leverage=1.0),
    )

    snapshot = broker.step(
        pd.Timestamp("2026-01-01T00:00:00Z"),
        100.0,
        0.0,
        5.0,
    )

    assert snapshot.signal == 1.0
    assert abs(snapshot.position_notional) <= 10_000.0 + 1e-9


def test_invalid_price_is_rejected():
    broker = PaperBroker()

    try:
        broker.step(
            pd.Timestamp("2026-01-01T00:00:00Z"),
            0.0,
            0.0,
            0.0,
        )
    except ValueError as exc:
        assert "price must be positive" in str(exc)
    else:
        raise AssertionError("expected non-positive price to fail")
