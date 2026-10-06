from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class Strategy(ABC):
    @abstractmethod
    def signals(self, frame: pd.DataFrame) -> pd.Series:
        """Return target exposure in [-1, 1], indexed like frame."""
        raise NotImplementedError
