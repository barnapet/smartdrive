import time
import random
import logging
from ..interfaces import OBDProvider
from ..domain import TelemetryData

class SimulatedOBDProvider(OBDProvider):
    def __init__(self, vin: str):
        self.vin = vin

    def connect(self) -> bool:
        logging.info("🎮 [SIMULATOR] Simulating connection...")
        return True

    def fetch_data(self) -> TelemetryData:
        return TelemetryData(
            vin=self.vin,
            timestamp=int(time.time()),
            speed=float(random.randint(45, 55)),
            rpm=float(random.randint(2100, 2400)),
            voltage=round(random.uniform(13.2, 14.2), 2)
        )
