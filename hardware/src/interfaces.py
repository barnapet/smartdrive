import abc
from .domain import TelemetryData

class OBDProvider(abc.ABC):
    @abc.abstractmethod
    def connect(self) -> bool:
        pass

    @abc.abstractmethod
    def fetch_data(self) -> TelemetryData:
        pass
