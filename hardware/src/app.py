import time
import json
import logging
from dataclasses import asdict
from .interfaces import OBDProvider

class SmartDriveMonitor:
    def __init__(self, provider: OBDProvider, cloud_client=None):
        self.provider = provider
        self.cloud_client = cloud_client
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
                self._publish(data)
                time.sleep(5)
        except KeyboardInterrupt:
            logging.info("🛑 Shutting down...")

    def _publish(self, data):
        payload = json.dumps(asdict(data))
        logging.info(f"📡 Data published: {payload}")
