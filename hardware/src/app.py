import json
import logging
import time
from dataclasses import asdict
from .interfaces import OBDProvider, CloudPublisher

class SmartDriveMonitor:
    def __init__(self, provider: OBDProvider, publisher: CloudPublisher):
        self.provider = provider
        self.publisher = publisher
        self.is_running = False

    def start(self):
        if self.provider.connect():
            self.is_running = True
            self._main_loop()

    def _main_loop(self):
        logging.info("🚀 Telemetry streaming started...")
        try:
            while self.is_running:
                data = self.provider.fetch_data()
                if data:
                    self._publish(data)
                time.sleep(5)
        except KeyboardInterrupt:
            logging.info("🛑 Shutting down...")

    def _publish(self, data):
        """Adatküldés a publisher interfészen keresztül."""
        payload = json.dumps(asdict(data))
        topic = f"vehicle/{data.vin}/telemetry"
        if self.publisher.publish(topic, payload):
            logging.info(f"📡 Adat elküldve: {topic}")
        else:
            logging.warning(f"⚠️ Sikertelen küldés: {payload}")
