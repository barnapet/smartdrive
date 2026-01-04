import time
import random
import logging
from ..interfaces import OBDProvider
from ..domain import TelemetryData

class SimulatedOBDProvider(OBDProvider):
    """
    Simulates vehicle telemetry data with scenario-based timelines (v1.5).
    Supports testing of Vmin calculations and Smart Guard sentinel mode.
    """
    def __init__(self, vin: str, scenario: str = "NORMAL_START"):
        self.vin = vin
        self.scenario = scenario
        self.start_time = time.time()
        self.current_temp = 20.0
        logging.info(f"🎮 [SIMULATOR] Initialized with scenario: {self.scenario}")

    def connect(self) -> bool:
        """Simulates a successful connection to an ELM327 adapter."""
        logging.info("🎮 [SIMULATOR] Connected to virtual OBD-II adapter.")
        return True

    def fetch_data(self) -> TelemetryData:
        """
        Generates telemetry based on the active scenario and elapsed time.
        """
        elapsed = time.time() - self.start_time
        
        # Alapértelmezett értékek (Parkoló autó)
        voltage = 12.6
        rpm = 0.0
        speed = 0.0

        if self.scenario == "CRANK_FAIL":
            # 0-2s: Parkolt állapot
            if elapsed < 2:
                voltage, rpm = 12.4, 0
            # 2-4s: Indítózás (Cranking) - itt kell a 10Hz!
            elif 2 <= elapsed <= 4:
                # Szimulálunk egy inrush tüskét (7.5V) majd egy gyenge plateau-t (8.2V)
                voltage = 7.5 if (elapsed - 2) < 0.1 else 8.2
                rpm = 200
            # 4s után: Beindul a motor
            else:
                voltage, rpm, speed = 14.2, 850, 0

        elif self.scenario == "VAMPIRE_DRAIN":
            # 0-5s: Alacsony feszültség, de még a küszöb felett
            if elapsed < 5:
                voltage = 11.7
            # 5s után: Beüt a Vampire Drain (11.5V alá esik)
            else:
                voltage = 11.4
            rpm = 0

        else: # NORMAL_START
            if elapsed < 2: voltage, rpm = 12.6, 0
            elif 2 <= elapsed <= 4: voltage, rpm = 9.5, 250 # Egészséges indítás
            else: voltage, rpm, speed = 14.4, 1200, 50

        return TelemetryData(
            vin=self.vin,
            timestamp=int(time.time()),
            speed=float(speed),
            rpm=float(rpm),
            voltage=voltage,
            coolant_temp=round(self.current_temp, 1)
        )

    def fetch_raw_voltage(self) -> float:
        """
        High-speed voltage access for 10Hz cranking capture.
        """
        data = self.fetch_data()
        return data.voltage

    def get_voltage(self) -> float:
        """Legacy support for older app logic."""
        return self.fetch_raw_voltage()
