import logging
import time
import obd
from ..interfaces import OBDProvider
from ..domain import TelemetryData

class RealOBDProvider(OBDProvider):
    """PRODUCTION VERSION: Real Bluetooth/ELM327 handshake."""
    
    def __init__(self, vin: str):
        self.vin = vin
        self.connection = None

    def connect(self) -> bool:
        logging.info("🔍 [REAL] Searching for OBD-II adapter...")
        ports = obd.scan_serial()

        if not ports:
            logging.error("❌ [REAL] ELM327 device not found!")
            return False

        for port in ports:
            logging.info(f"🔄 [REAL] Attempting connection on: {port}...")
            conn = obd.OBD(port)
            if conn.status() == obd.OBDStatus.CAR_CONNECTED:
                self.connection = conn
                logging.info(f"✅ [REAL] Successful handshake: {port}")
                return True
        return False

    def fetch_data(self) -> TelemetryData:
        if not self.connection:
            raise ConnectionError("No active OBD connection.")

        v = self.connection.query(obd.commands.ELM_VOLTAGE).value
        s = self.connection.query(obd.commands.SPEED).value
        r = self.connection.query(obd.commands.RPM).value

        return TelemetryData(
            vin=self.vin,
            timestamp=int(time.time()),
            speed=float(s.magnitude) if s else 0.0,
            rpm=float(r.magnitude) if r else 0.0,
            voltage=float(v.magnitude) if v else 0.0
        )
