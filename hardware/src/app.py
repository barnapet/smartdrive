import time
import logging
import os
from .providers.real import RealOBDProvider
from .domain import TelemetryData

class SmartDriveApp:
    # --- CONSTANTS BASED ON V1.3 SPECIFICATION ---
    V_VAMPIRE_THRESHOLD = 11.5  # Protection threshold (Battery safety)
    V_RESUME_THRESHOLD = 13.0   # Resumption threshold (Charging detected)
    CRANKING_RPM_LIMIT = 600    # Cranking/Idle RPM threshold
    
    # Sampling intervals (in seconds)
    INTERVAL_CRANKING = 0.1     # 10Hz (Target for high-resolution start)
    INTERVAL_STEADY = 5.0       # 0.2Hz (Normal operation)
    INTERVAL_SLEEP = 1800.0     # 30 minutes (Deep power save)

    def __init__(self, vin: str, port: str = None):
        self.provider = RealOBDProvider(vin=vin, port=port)
        self.current_interval = self.INTERVAL_STEADY
        self.power_saving_active = False
        logging.info("🚀 SmartDrive Gateway v1.3 initialized.")

    def run(self):
        """Main execution loop with adaptive sampling logic."""
        while True:
            if not self.provider.connect():
                logging.warning("⏳ Reconnecting to OBD...")
                time.sleep(5)
                continue

            try:
                while True:
                    data = self.provider.fetch_data()
                    if not data:
                        break

                    self._process_adaptive_logic(data)
                    
                    # Data transmission (Simulated cloud/logging)
                    if not self.power_saving_active:
                        self._ingest_to_cloud(data)

                    time.sleep(self.current_interval)

            except Exception as e:
                logging.error(f"❌ Runtime error: {e}")
                time.sleep(1)

    def _process_adaptive_logic(self, data: TelemetryData):
        """
        Logic for adaptive sampling rates and battery protection.
        """
        # 1. VAMPIRE DRAIN PROTECTION (RPM=0 and low voltage)
        if data.rpm == 0 and data.voltage < self.V_VAMPIRE_THRESHOLD:
            if not self.power_saving_active:
                logging.warning(f"⚠️ Power Saving Active: {data.voltage}V < {self.V_VAMPIRE_THRESHOLD}V")
                self.power_saving_active = True
            self.current_interval = self.INTERVAL_SLEEP

        # 2. RESUMPTION (Alternator charging detected)
        elif self.power_saving_active and data.voltage >= self.V_RESUME_THRESHOLD:
            logging.info(f"🟢 Power Saving Deactivated: {data.voltage}V (Alternator Active)")
            self.power_saving_active = False
            self.current_interval = self.INTERVAL_STEADY

        # 3. READY / CRANK PHASE (Ignition ON or engine cranking)
        elif data.rpm < self.CRANKING_RPM_LIMIT and not self.power_saving_active:
            # Switch to 10Hz when ignition is ON (RPM=0 but voltage is healthy)
            self.current_interval = self.INTERVAL_CRANKING

        # 4. STEADY STATE (Normal engine operation)
        elif data.rpm >= self.CRANKING_RPM_LIMIT:
            self.current_interval = self.INTERVAL_STEADY

    def _ingest_to_cloud(self, data: TelemetryData):
        """Forward data to AWS IoT Core via MQTT."""
        # MQTT publishing logic goes here
        logging.info(f"📊 Ingesting: {data.voltage}V | {data.rpm} RPM | Interval: {self.current_interval}s")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = SmartDriveApp(vin="PROD-VIN-2026", port="/dev/rfcomm0")
    app.run()
