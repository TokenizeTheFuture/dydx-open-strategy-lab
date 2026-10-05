from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MarketBar:
    timestamp: datetime
    market: str
    close: float
    funding_rate: float
