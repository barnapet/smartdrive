import logging
from .interfaces import CloudPublisher

class AWSCloudPublisher(CloudPublisher):
    def __init__(self, aws_client):
        self.client = aws_client

    def publish(self, topic: str, payload: str) -> bool:
        try:
            self.client.publish(topic, payload, 1)
            return True
        except Exception as e:
            logging.error(f"AWS publikálási hiba: {e}")
            return False
