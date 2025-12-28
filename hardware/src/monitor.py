import time
import json
import os
import logging
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder

# Logging configuration in accordance with the DevOps plan
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartDriveEdge")

# Dynamic path determination
# The file is located in hardware/src, so BASE_DIR will be the hardware/ folder
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR) 
CERTS_DIR = os.path.join(BASE_DIR, 'certs')

class SmartDriveMonitor:
    def __init__(self, vin, endpoint):
        self.vin = vin
        self.endpoint = endpoint
        self.topic = f"vehicle/{self.vin}/telemetry" # Topic structure according to the SDD
        self.mqtt_connection = self._build_connection()

    def _build_connection(self):
        """Establishing a secure mTLS connection based on the DevOps plan"""
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

        # Checking certificate file paths
        cert_path = os.path.join(CERTS_DIR, 'certificate.pem.crt')
        key_path = os.path.join(CERTS_DIR, 'private.pem.key')
        ca_path = os.path.join(CERTS_DIR, 'AmazonRootCA1.pem')

        if not all(os.path.exists(p) for p in [cert_path, key_path, ca_path]):
            logger.error(f"Missing certificates in the {CERTS_DIR} directory!")
            raise FileNotFoundError("Missing mTLS files.")

        return mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=cert_path,
            pri_key_filepath=key_path,
            ca_filepath=ca_path,
            client_bootstrap=client_bootstrap,
            client_id=self.vin,
            clean_session=False,
            keep_alive_secs=30
        )

    def get_obd_data(self):
        """Retrieving OBD-II data according to SRS requirements"""
        # Initially using simulated data as per Section 3 of the Testing Plan
        return {
            "vin": self.vin,
            "timestamp": int(time.time()),
            "speed": 50,
            "rpm": 2100,
            "voltage": 12.4 # Critical value for battery analysis
        }

    def run(self):
        logger.info(f"🚀 SmartDrive Edge started for: {self.vin}")
        connect_future = self.mqtt_connection.connect()
        connect_future.result()
        logger.info("✅ Connected to AWS IoT Core")

        try:
            while True:
                data = self.get_obd_data()
                # Publishing to the MQTT topic described in the SDD
                self.mqtt_connection.publish(
                    topic=self.topic,
                    payload=json.dumps(data),
                    qos=mqtt.QoS.AT_LEAST_ONCE
                )
                logger.info(f"📡 Data published: {data}")
                time.sleep(5) # 5s sampling interval
        except KeyboardInterrupt:
            logger.info("🛑 Stopping monitor...")
        finally:
            self.mqtt_connection.disconnect().result()

if __name__ == "__main__":
    # The endpoint must be copied from the AWS IoT Core Console
    monitor = SmartDriveMonitor(
        vin="TESTVIN123456789",
        endpoint="a3de8eyv1wr96p-ats.iot.eu-central-1.amazonaws.com"
    )
    monitor.run()
