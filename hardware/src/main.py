import logging
import os
import sys
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from .providers.simulated import SimulatedOBDProvider
from .providers.real import RealOBDProvider
# JAVÍTÁS 1: A helyes osztály importálása
from .app import SmartDriveApp
from .infrastructure import AWSCloudPublisher

def create_aws_iot_client(vin: str):
    """
    Configures the AWS IoT MQTT client.
    """
    client = AWSIoTMQTTClient(vin)
    # Endpoint a te régiódhoz (Frankfurt)
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
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Környezeti változók kezelése
    VIN = os.getenv("SMARTDRIVE_VIN", "TESTVIN123456789")
    MODE = os.getenv("SMARTDRIVE_MODE", "SIMULATED")
    # JAVÍTÁS 2: OBD_PORT használata, hogy kompatibilis legyen a paranccsal
    PORT = os.getenv("OBD_PORT", "/dev/ttyUSB0") 

    logging.info(f"🚀 Starting SmartDrive Edge Gateway in [{MODE}] mode...")

    # 1. AWS Kapcsolat felépítése
    try:
        aws_client = create_aws_iot_client(VIN)
        if aws_client.connect():
            logging.info(f"✅ AWS Cloud Connected (VIN: {VIN})")
        else:
            logging.error("❌ AWS Connection Failed")
            # Éles tesztnél nem lépünk ki, hogy a logokat lássuk, de a felhő nem fog menni
    except Exception as e:
        logging.error(f"⚠️ Cloud Connection Error: {e}")
        aws_client = None

    publisher = AWSCloudPublisher(aws_client) if aws_client else None

    # 2. App indítása
    try:
        # JAVÍTÁS 3: Dependency Injection
        # Átadjuk a VIN-t, Portot és a Publishert az App-nak
        app = SmartDriveApp(vin=VIN, port=PORT, publisher=publisher)
        app.run()

    except Exception as e:
        logging.critical(f"💥 Critical system failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
