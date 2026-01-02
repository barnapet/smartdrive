from abc import ABC, abstractmethod
from typing import Optional, List

class ITemperatureProvider(ABC):
    @abstractmethod
    def get_temperature(self, payload: dict) -> Optional[float]:
        pass

class IInsightRepository(ABC):
    @abstractmethod
    def save_insight(self, insight: dict):
        pass
    
    @abstractmethod
    def get_last_insights(self, vin: str, limit: int) -> List[dict]:
        pass
