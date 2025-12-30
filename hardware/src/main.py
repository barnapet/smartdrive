import logging
import os
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from .providers import SimulatedOBDProvider, RealOBDProvider
from .app import SmartDriveMonitor
from .infrastructure import AWSCloudPublisher

def create_aws_client(vin):
    client = AWSIoTMQTTClient(vin)
    client.configureEndpoint("a3de8eyv1wr96p-ats.iot.eu-central-1.amazonaws.com", 8883)
    cert_dir = "hardware/certs"
    client.configureCredentials(
        f"{cert_dir}/AmazonRootCA1.pem",
        f"{cert_dir}/private.pem.key",
        f"{cert_dir}/certificate.pem.crt"
    )

    client.configureAutoReconnectBackoffTime(1, 32, 20)
    client.configureOfflinePublishQueueing(-1)
    client.configureDrainingFrequency(2)
    client.configureConnectDisconnectTimeout(10)
    client.configureMQTTOperationTimeout(5)
    return client

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    VIN = "TESTVIN123456789"
    MODE = os.getenv("SMARTDRIVE_MODE", "SIMULATED")
    aws_client = create_aws_client(VIN)
    publisher = AWSCloudPublisher(aws_client)
    if aws_client.connect():
        logging.info("✅ Connected to AWS IoT Core")
    provider = RealOBDProvider(VIN) if MODE == "REAL" else SimulatedOBDProvider(VIN)
    monitor = SmartDriveMonitor(provider, publisher)
    monitor.start()

if __name__ == "__main__":
    main()
