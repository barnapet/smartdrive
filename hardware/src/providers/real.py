import logging
import time
import obd
from ..interfaces import OBDProvider
from ..domain import TelemetryData

class RealOBDProvider(OBDProvider):
    def __init__(self, vin: str, port: str = None):
        """
        :param vin: Vehicle Identification Number
        :param port: Optional serial port (e.g., '/dev/rfcomm0'). 
                     If None, performs automatic discovery.
        """
        self.vin = vin
        self.port = port 
        self.connection = None

    def connect(self) -> bool:
        # 1. If a manual port is provided, try it first
        if self.port:
            logging.info(f"🔍 [REAL] Connecting on direct port: {self.port}...")
            return self._attempt_connection(self.port)

        # 2. Otherwise, fall back to automatic discovery
        logging.info("🔍 [REAL] Starting automatic OBD-II discovery...")
        ports = obd.scan_serial()
        if not ports:
            logging.error("❌ ERROR: No paired OBD-II devices found!")
            return False

        for port in ports:
            if self._attempt_connection(port):
                return True
        
        return False

    def _attempt_connection(self, port_name: str) -> bool:
        """Internal method to establish connection on a specific port."""
        try:
            logging.info(f"🔄 Connection attempt: {port_name}...")
            conn = obd.OBD(port_name, fast=False)
            
            # Brief delay to allow the adapter to initialize
            time.sleep(1.5)
            status = conn.status()

            if status == obd.OBDStatus.CAR_CONNECTED:
                self.connection = conn
                logging.info(f"✅ SUCCESS: Connected to vehicle! ({port_name})")
                return True
            
            elif status == obd.OBDStatus.ELM_CONNECTED:
                logging.warning(f"⚠️ PARTIAL SUCCESS: Adapter found ({port_name}), but ignition is OFF.")
            else:
                logging.error(f"❌ ERROR: Adapter not responding on {port_name}.")
                
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error while opening port ({port_name}): {e}")
            return False

    def fetch_data(self) -> TelemetryData:
        if not self.connection or self.connection.status() != obd.OBDStatus.CAR_CONNECTED:
            logging.error("‼️ Connection to ECU lost!")
            return None
        
        def get_value(cmd):
            res = self.connection.query(cmd)
            # Safe extraction: return 0.0 if value is missing or lacks magnitude
            if res.value is not None and hasattr(res.value, 'magnitude'):
                return float(res.value.magnitude)
            return 0.0

        return TelemetryData(
            vin=self.vin,
            timestamp=int(time.time()),
            speed=get_value(obd.commands.SPEED),
            rpm=get_value(obd.commands.RPM),
            voltage=get_value(obd.commands.ELM_VOLTAGE)
        )
