import time
import random
import logging
from .interfaces import OBDProvider
from .domain import TelemetryData

class SimulatedOBDProvider(OBDProvider):
    def __init__(self, vin: str):
        self.vin = vin

    def connect(self) -> bool:
        logging.info("🎮 Simulated OBD Provider initialized.")
        return True

    def fetch_data(self) -> TelemetryData:
        return TelemetryData(
            vin=self.vin,
            timestamp=int(time.time()),
            speed=random.uniform(40, 60),
            rpm=random.uniform(2000, 2500),
            voltage=random.uniform(12.5, 14.2)
        )

class RealOBDProvider(OBDProvider):
    def __init__(self, vin: str):
        self.vin = vin

    def connect(self) -> bool:
        logging.warning("🔍 Real OBD search not yet implemented.")
        return False

    def fetch_data(self) -> TelemetryData:
        raise NotImplementedError
