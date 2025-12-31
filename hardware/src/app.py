import json
import logging
import time
from dataclasses import asdict
from .interfaces import OBDProvider, CloudPublisher

class SmartDriveMonitor:
    """
    Main monitoring logic for the SmartDrive platform.
    Implements adaptive sampling and battery protection.
    """
    # Thresholds based on System Design v1.2
    V_VAMPIRE_CUTOFF = 12.1  # Polling stops below this value
    V_VAMPIRE_RESUME = 13.0  # Polling resumes when alternator is active
    
    # Sampling Intervals
    INTERVAL_CRANKING = 0.1     # 10Hz
    INTERVAL_STEADY = 5.0       # 0.2Hz
    INTERVAL_POST_DRIVE = 60.0  # 1 minute
    INTERVAL_SLEEP = 1800.0     # 30 minutes

    def __init__(self, provider: OBDProvider, publisher: CloudPublisher):
        self.provider = provider
        self.publisher = publisher
        self.is_running = False
        self.power_saving_active = False
        self.current_interval = self.INTERVAL_STEADY

    def start(self):
        if self.provider.connect():
            self.is_running = True
            self._main_loop()

    def _main_loop(self):
        logging.info("🚀 SmartDrive monitoring loop initiated...")
        try:
            while self.is_running:
                # 1. Fetch data from provider
                data = self.provider.fetch_data()
                
                if data:
                    # 2. Check for battery protection (FR11)
                    self._handle_battery_protection(data.voltage)
                    
                    if not self.power_saving_active:
                        # 3. Adjust sampling rate based on vehicle state (FR4)
                        self._adjust_sampling_rate(data.rpm)
                        self._publish_telemetry(data)
                
                # 4. Adaptive wait based on current state
                time.sleep(self.current_interval)
                
        except KeyboardInterrupt:
            logging.info("🛑 Monitoring stopped by user.")

    def _handle_battery_protection(self, voltage: float):
        """
        Suspends polling if battery voltage is too low to prevent discharge.
        """
        if not self.power_saving_active and voltage < self.V_VAMPIRE_CUTOFF:
            self.power_saving_active = True
            self.current_interval = self.INTERVAL_SLEEP
            self._notify_status("Power Saving Mode: Monitoring paused to protect battery.") #
            logging.warning(f"⚠️ Vampire Drain Protection triggered at {voltage}V.")
        
        elif self.power_saving_active and voltage >= self.V_VAMPIRE_RESUME:
            self.power_saving_active = False
            self.current_interval = self.INTERVAL_STEADY
            logging.info(f"⚡ Voltage recovered ({voltage}V). Resuming normal operation.")

    def _adjust_sampling_rate(self, rpm: float):
        """
        Adaptive Sampling Logic (FR4):
        - 10Hz during Cranking Phase
        - 0.2Hz during Steady State (Running)
        - 1-minute interval for Post-Drive
        """
        if 0 < rpm < 600:
            # Cranking Phase detected
            self.current_interval = self.INTERVAL_CRANKING
        elif rpm >= 600:
            # Engine is running (Steady State)
            self.current_interval = self.INTERVAL_STEADY
        else:
            # Engine is OFF (Post-Drive/Sleep)
            self.current_interval = self.INTERVAL_POST_DRIVE

    def _notify_status(self, message: str):
        """Sends operational status alerts to the cloud."""
        alert_payload = {
            "type": "STATUS_ALERT",
            "message": message,
            "timestamp": int(time.time())
        }
        self.publisher.publish("vehicle/status/alerts", json.dumps(alert_payload))

    def _publish_telemetry(self, data):
        """Serializes and sends telemetry data."""
        payload = json.dumps(asdict(data))
        topic = f"vehicle/{data.vin}/telemetry"
        if self.publisher.publish(topic, payload):
            logging.info(f"📡 Telemetry sent (Rate: {1/self.current_interval:.1f}Hz)")
