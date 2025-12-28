import json
import logging
import time
from dataclasses import asdict
from .interfaces import OBDProvider

class SmartDriveMonitor:
    def __init__(self, provider: OBDProvider, cloud_client):
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
        """Sending data to the AWS IoT Core."""
        payload = json.dumps(asdict(data))
        topic = f"vehicle/{data.vin}/telemetry"
        
        try:
            if self.cloud_client:
                self.cloud_client.publish(topic, payload, 1)
                logging.info(f"📡 Cloud: Data sent to {topic} -> {payload}")
            else:
                logging.warning(f"⚠️ Offline mode: {payload}")
        except Exception as e:
            logging.error(f"❌ Failed to publish to AWS: {e}")
