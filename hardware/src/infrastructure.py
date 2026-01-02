import json
import logging

class AWSCloudPublisher:
    def __init__(self, mqtt_client):
        """
        Wrapper around the AWS IoT MQTT Client.
        """
        self.client = mqtt_client

    def publish_telemetry(self, payload: dict):
        """
        Publishes telemetry data to the vehicle-specific topic.
        Topic format: vehicle/{VIN}/telemetry
        """
        if not self.client:
            logging.warning("⚠️ MQTT Client not initialized, skipping publish.")
            return

        try:
            # 1. Topic meghatározása a VIN alapján
            vin = payload.get('vin', 'UNKNOWN_VIN')
            topic = f"vehicle/{vin}/telemetry"
            
            # 2. JSON sorosítás
            message_json = json.dumps(payload)
            
            # 3. Küldés (QoS 1 - At least once delivery)
            # A library publish metódusa: topic, payload, QoS
            self.client.publish(topic, message_json, 1)
            
            logging.debug(f"📡 MQTT Sent to {topic}: {len(message_json)} bytes")
            
        except Exception as e:
            logging.error(f"❌ Failed to publish MQTT message: {e}")

    def publish_event(self, vin: str, event_type: str, details: str):
        """
        Opcionális: Riasztások küldése (pl. Vampire Drain Alert)
        Topic format: vehicle/{VIN}/alerts
        """
        if not self.client: return

        topic = f"vehicle/{vin}/alerts"
        payload = {
            "vin": vin,
            "type": event_type,
            "details": details,
            "timestamp": None # Ide jöhetne datetime.now().isoformat()
        }
        self.client.publish(topic, json.dumps(payload), 1)
