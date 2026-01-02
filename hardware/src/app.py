import time
import logging
from datetime import datetime
from .providers.real import RealOBDProvider
from .domain import TelemetryData

class SmartDriveApp:
    # --- CONSTANTS ---
    V_VAMPIRE_THRESHOLD = 11.5
    V_RESUME_THRESHOLD = 13.0
    CRANKING_RPM_LIMIT = 600
    
    INTERVAL_CRANKING = 0.1
    INTERVAL_STEADY = 5.0
    INTERVAL_SLEEP = 1800.0

    def __init__(self, vin: str, port: str = None, publisher=None):
        self.vin = vin
        self.provider = RealOBDProvider(vin=vin, port=port)
        self.publisher = publisher
        
        self.current_interval = self.INTERVAL_STEADY
        self.power_saving_active = False
        logging.info("🚀 SmartDrive Gateway v1.3 initialized.")

    def run(self):
        while True:
            # Újracsatlakozási logika
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
                    
                    if not self.power_saving_active:
                        self._ingest_to_cloud(data)

                    time.sleep(self.current_interval)

            except Exception as e:
                logging.error(f"❌ Runtime error: {e}")
                time.sleep(1)

    def _process_adaptive_logic(self, data: TelemetryData):
        # 1. Vampire Drain Protection
        if data.rpm == 0 and data.voltage < self.V_VAMPIRE_THRESHOLD:
            if not self.power_saving_active:
                logging.warning(f"⚠️ Power Saving Active: {data.voltage}V < {self.V_VAMPIRE_THRESHOLD}V")
                self.power_saving_active = True
            self.current_interval = self.INTERVAL_SLEEP

        # 2. Resumption
        elif self.power_saving_active and data.voltage >= self.V_RESUME_THRESHOLD:
            logging.info(f"🟢 Power Saving Deactivated: {data.voltage}V")
            self.power_saving_active = False
            self.current_interval = self.INTERVAL_STEADY

        # 3. Cranking Phase
        elif data.rpm < self.CRANKING_RPM_LIMIT and not self.power_saving_active:
            self.current_interval = self.INTERVAL_CRANKING

        # 4. Steady State
        elif data.rpm >= self.CRANKING_RPM_LIMIT:
            self.current_interval = self.INTERVAL_STEADY

    def _ingest_to_cloud(self, data: TelemetryData):
        """Forward data to AWS IoT Core via MQTT."""
        logging.info(f"📊 Ingesting: {data.voltage}V | {data.rpm} RPM | Interval: {self.current_interval}s")
        
        if self.publisher:
            # JAVÍTÁS: Időbélyeg konverzió (int -> datetime -> isoformat)
            ts = data.timestamp
            if isinstance(ts, (int, float)):
                ts_str = datetime.fromtimestamp(ts).isoformat()
            else:
                # Ha már datetime objektum
                ts_str = ts.isoformat()

            payload = {
                "vin": self.vin,
                "timestamp": ts_str,
                "rpm": data.rpm,
                "voltage": data.voltage,
                "pids": [
                    {"pid_code": "RPM", "value": data.rpm, "timestamp": ts_str},
                    {"pid_code": "BATTERY_VOLTAGE", "value": data.voltage, "timestamp": ts_str}
                ]
            }
            self.publisher.publish_telemetry(payload)
