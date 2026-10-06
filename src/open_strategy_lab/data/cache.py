from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(slots=True)
class CsvCache:
    root: Path | str = Path(".cache/open_strategy_lab")

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    def path_for(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(":", "_")
        return self.root / f"{safe}.csv.gz"

    def load(self, key: str) -> pd.DataFrame | None:
        path = self.path_for(key)
        if not path.exists():
            return None

        frame = pd.read_csv(path, index_col=0, parse_dates=[0])
        frame.index = pd.DatetimeIndex(frame.index)
        if frame.index.tz is None:
            frame.index = frame.index.tz_localize("UTC")
        else:
            frame.index = frame.index.tz_convert("UTC")
        return frame.sort_index()

    def save(self, key: str, frame: pd.DataFrame) -> Path:
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.sort_index().to_csv(path, compression="gzip")
        return path
