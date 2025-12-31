import logging
import os
import sys
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from .providers.simulated import SimulatedOBDProvider
from .providers.real import RealOBDProvider
from .app import SmartDriveMonitor
from .infrastructure import AWSCloudPublisher

def create_aws_iot_client(vin: str):
    """
    Configures the AWS IoT MQTT client with certificates and security settings.
    """
    client = AWSIoTMQTTClient(vin)
    # Endpoint from System Design v1.2
    client.configureEndpoint("a3de8eyv1wr96p-ats.iot.eu-central-1.amazonaws.com", 8883)
    
    # Path to certificates as defined in the project structure
    cert_dir = "hardware/certs"
    client.configureCredentials(
        f"{cert_dir}/AmazonRootCA1.pem",
        f"{cert_dir}/private.pem.key",
        f"{cert_dir}/certificate.pem.crt"
    )

    # Connection resilience settings
    client.configureAutoReconnectBackoffTime(1, 32, 20)
    client.configureOfflinePublishQueueing(-1)  # Infinite queuing for NFR4 (Offline Mode)
    client.configureDrainingFrequency(2)
    client.configureConnectDisconnectTimeout(10)
    client.configureMQTTOperationTimeout(5)
    return client

def main():
    # Set up centralized logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    logging.info("Starting SmartDrive Edge Gateway...")

    # Configuration from environment or defaults
    VIN = os.getenv("SMARTDRIVE_VIN", "TESTVIN123456789")
    MODE = os.getenv("SMARTDRIVE_MODE", "SIMULATED")
    PORT = os.getenv("SMARTDRIVE_PORT", None) # e.g., /dev/rfcomm0

    # 1. Initialize AWS Connectivity
    aws_client = create_aws_iot_client(VIN)
    publisher = AWSCloudPublisher(aws_client)
    
    try:
        if aws_client.connect():
            logging.info(f"✅ Successfully connected to AWS IoT Core for VIN: {VIN}")
        else:
            logging.error("❌ Failed to connect to AWS IoT Core. Check credentials and network.")
            sys.exit(1)

        # 2. Initialize Data Provider (FR1)
        if MODE == "REAL":
            logging.info(f"🚗 Initializing REAL OBD-II Provider on port: {PORT or 'Auto-discovery'}")
            provider = RealOBDProvider(VIN, port=PORT)
        else:
            logging.info("🎮 Initializing SIMULATED OBD-II Provider")
            provider = SimulatedOBDProvider(VIN)

        # 3. Start the Monitoring Engine (Adaptive Polling & Protection)
        monitor = SmartDriveMonitor(provider, publisher)
        monitor.start()

    except Exception as e:
        logging.critical(f"💥 Critical system failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
