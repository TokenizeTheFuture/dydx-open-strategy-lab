from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class Strategy(ABC):
    @abstractmethod
    def signals(self, frame: pd.DataFrame) -> pd.Series:
        """Return target direction in {-1, 0, 1}, indexed like frame."""
        raise NotImplementedError
