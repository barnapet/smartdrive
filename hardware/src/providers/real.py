import logging
import time
import obd
from ..interfaces import OBDProvider
from ..domain import TelemetryData

class RealOBDProvider(OBDProvider):
    def __init__(self, vin: str, port: str = None):
        self.vin = vin
        self.port = port 
        self.connection = None

    def connect(self) -> bool:
        if self.port:
            logging.info(f"🔍 [REAL] Connecting on direct port: {self.port}...")
            return self._attempt_connection(self.port)

        ports = obd.scan_serial()
        if not ports:
            logging.error("❌ No paired OBD-II devices found.")
            return False

        for port in ports:
            if self._attempt_connection(port):
                return True
        return False

    def _attempt_connection(self, port_name: str) -> bool:
        try:
            conn = obd.OBD(port_name, fast=True)
            time.sleep(1.5)
            status = conn.status()

            if status == obd.OBDStatus.CAR_CONNECTED:
                self.connection = conn
                logging.info(f"✅ Connection successful on {port_name}")
                return True
            
            return False
        except Exception as e:
            logging.error(f"❌ Connection error on {port_name}: {e}")
            return False

    def fetch_raw_voltage(self) -> float:
        """
        A lehető leggyorsabb feszültséglekérés direkt AT RV paranccsal.
        Kikerüli az ECU lekérdezést, csak az adaptert kérdezi.
        """
        if not self.connection or not self.connection.interface:
            return 0.0
        
        try:
            # Direkt parancsküldés az ELM327-nek
            raw_response = self.connection.interface.send_and_receive(b"AT RV\r")
            
            # Tisztítás: pl. b'12.6V\r>' -> 12.6
            clean_val = raw_response.replace(b"V", b"").replace(b"\r", b"").replace(b">", b"").strip()
            return float(clean_val)
        except Exception as e:
            logging.debug(f"⚠️ Raw voltage error: {e}")
            return 0.0

    def fetch_data(self) -> TelemetryData:
        if not self.connection or self.connection.status() != obd.OBDStatus.CAR_CONNECTED:
            return None
        
        def get_value(cmd):
            response = self.connection.query(cmd)
            if not response.is_null() and hasattr(response.value, 'magnitude'):
                return float(response.value.magnitude)
            return 0.0

        return TelemetryData(
            vin=self.vin,
            timestamp=int(time.time()),
            speed=get_value(obd.commands.SPEED),
            rpm=get_value(obd.commands.RPM),
            voltage=get_value(obd.commands.ELM_VOLTAGE),
            coolant_temp=get_value(obd.commands.COOLANT_TEMP)
        )
