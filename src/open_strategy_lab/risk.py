from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskConfig:
    max_leverage: float = 1.0
    max_annualized_vol: float = 1.20
    min_equity: float = 100.0

    def validate(self) -> None:
        if self.max_leverage <= 0:
            raise ValueError("max_leverage must be positive")
        if self.max_annualized_vol <= 0:
            raise ValueError("max_annualized_vol must be positive")
        if self.min_equity <= 0:
            raise ValueError("min_equity must be positive")
