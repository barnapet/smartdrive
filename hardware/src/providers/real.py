import logging
import time
import obd
from ..interfaces import OBDProvider
from ..domain import TelemetryData

class RealOBDProvider(OBDProvider):
    """
    Physical OBD-II provider using the ELM327 adapter.
    Optimized for high-frequency sampling (10Hz) and battery monitoring.
    """
    def __init__(self, vin: str, port: str = None):
        self.vin = vin
        self.port = port 
        self.connection = None

    def connect(self) -> bool:
        """
        Establishes a connection to the ELM327 adapter.
        Uses 'fast' mode to support high-frequency polling requirements.
        """
        if self.port:
            logging.info(f"🔍 [REAL] Connecting on direct port: {self.port}...")
            return self._attempt_connection(self.port)

        logging.info("🔍 [REAL] Scanning serial ports for OBD-II devices...")
        ports = obd.scan_serial()
        if not ports:
            logging.error("❌ No paired OBD-II devices found. Please check Bluetooth settings.")
            return False

        for port in ports:
            if self._attempt_connection(port):
                return True
        
        return False

    def _attempt_connection(self, port_name: str) -> bool:
        """Internal helper to initialize the OBD connection with performance tuning."""
        try:
            # 'fast=True' is critical for reaching near 10Hz sampling rates
            conn = obd.OBD(port_name, fast=True)
            time.sleep(1.5)
            status = conn.status()

            if status == obd.OBDStatus.CAR_CONNECTED:
                self.connection = conn
                logging.info(f"✅ Connection successful on {port_name}")
                return True
            
            elif status == obd.OBDStatus.ELM_CONNECTED:
                logging.warning(f"⚠️ Adapter found on {port_name}, but ignition is OFF.")
            else:
                logging.error(f"❌ Adapter on {port_name} is not responding.")
                
            return False
        except Exception as e:
            logging.error(f"❌ Connection error on {port_name}: {e}")
            return False

    def fetch_data(self) -> TelemetryData:
        """
        Fetches current vehicle telemetry.
        Includes voltage and RPM for adaptive sampling and protection logic.
        """
        if not self.connection or self.connection.status() != obd.OBDStatus.CAR_CONNECTED:
            # Attempting a quick health check before failing
            if not self.connection:
                return None
            logging.error("‼️ Connection to ECU lost.")
            return None
        
        def get_value(cmd):
            """Helper to extract numeric magnitude from OBD responses."""
            response = self.connection.query(cmd)
            if not response.is_null() and hasattr(response.value, 'magnitude'):
                return float(response.value.magnitude)
            return 0.0

        # Capturing all required fields for logic and analytics
        return TelemetryData(
            vin=self.vin,
            timestamp=int(time.time()),
            speed=get_value(obd.commands.SPEED),
            rpm=get_value(obd.commands.RPM),
            voltage=get_value(obd.commands.ELM_VOLTAGE),
            coolant_temp=get_value(obd.commands.COOLANT_TEMP)
        )
