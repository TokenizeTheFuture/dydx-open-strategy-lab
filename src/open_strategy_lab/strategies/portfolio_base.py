from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class PortfolioStrategy(ABC):
    @abstractmethod
    def weights(self, prices: pd.DataFrame, funding: pd.DataFrame | None = None) -> pd.DataFrame:
        """Return target notional weights for every timestamp and market."""
        raise NotImplementedError
