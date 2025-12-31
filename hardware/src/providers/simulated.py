import time
import random
import logging
from ..interfaces import OBDProvider
from ..domain import TelemetryData

class SimulatedOBDProvider(OBDProvider):
    """
    Simulates vehicle telemetry data for testing and development.
    Supports the updated TelemetryData schema (v1.2).
    """
    def __init__(self, vin: str):
        self.vin = vin
        # Initial states for more realistic simulation trends
        self.current_temp = 20.0
        self.is_engine_running = True

    def connect(self) -> bool:
        """Simulates a successful connection to an ELM327 adapter."""
        logging.info("🎮 [SIMULATOR] Connecting to virtual OBD-II adapter...")
        return True

    def fetch_data(self) -> TelemetryData:
        """
        Generates simulated telemetry data.
        Includes voltage fluctuations and temperature shifts.
        """
        # Simulate slight engine warming or cooling
        self.current_temp += random.uniform(-0.1, 0.5) if self.is_engine_running else -0.2
        
        # Simulate voltage behavior
        # Typical: 13.5V-14.4V (Running), 12.1V-12.8V (Stopped)
        base_voltage = 13.8 if self.is_engine_running else 12.4
        simulated_voltage = round(base_voltage + random.uniform(-0.3, 0.3), 2)

        return TelemetryData(
            vin=self.vin,
            timestamp=int(time.time()),
            speed=float(random.randint(45, 110) if self.is_engine_running else 0),
            rpm=float(random.randint(2000, 3500) if self.is_engine_running else 0),
            voltage=simulated_voltage,
            coolant_temp=round(self.current_temp, 1)
        )

    def get_voltage(self) -> float:
        """
        Direct access to voltage for the Vampire Drain Protection check.
        Matches the interface requirements used in app.py.
        """
        return 13.8 if self.is_engine_running else 12.4
