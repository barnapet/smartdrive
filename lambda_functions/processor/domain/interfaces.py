from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from config import ProcessorConfig

class ISignalProcessor(ABC):
    """
    Interface for cranking signal analysis.
    Ensures that different analysis strategies can be swapped seamlessly.
    """
    @abstractmethod
    def process(self, points: List[Tuple[float, float]], config: ProcessorConfig) -> Optional[float]:
        """Processes raw voltage points to return a validated health indicator[cite: 142]."""
        pass
