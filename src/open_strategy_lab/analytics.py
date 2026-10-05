from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import pandas as pd


def summary_frame(summary: Mapping[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"metric": key, "value": float(value)} for key, value in summary.items()]
    )


def write_summary_json(summary: Mapping[str, float], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(summary), indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_markdown_report(summary: Mapping[str, float], path: str | Path, title: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    percent_metrics = {"total_return","max_drawdown","mark_return_sum","funding_return_sum","trading_cost_return_sum","average_gross_exposure","average_abs_net_exposure"}
    rows=[]
    for key,value in summary.items():
        if key in percent_metrics: rendered=f"{value:.2%}"
        elif key in {"initial_equity","final_equity"}: rendered=f"${value:,.2f}"
        else: rendered=f"{value:,.4f}"
        rows.append(f"| {key} | {rendered} |")
    body="\n".join([f"# {title}","","Generated from the local backtest output.","","| Metric | Value |","| --- | ---: |",*rows,"","> Research software only. Historical or simulated results do not guarantee future performance.",""])
    path.write_text(body,encoding="utf-8")
    return path
