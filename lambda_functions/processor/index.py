import json
import os
import boto3
import requests
from datetime import datetime
from repository import GoldLayerRepository

# AWS Clients
s3 = boto3.client('s3')
secrets = boto3.client('secretsmanager')

class SmartDriveProcessor:
    def __init__(self):
        self.repo = GoldLayerRepository()
        self.weather_api_key = self._get_secret("OpenWeatherMapKey")

    def _get_secret(self, secret_name):
        """Retrieves API keys from AWS Secrets Manager (Security Requirement NFR5)."""
        #
        try:
            response = secrets.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except Exception:
            return os.getenv(secret_name)

    def get_ambient_temperature(self, lat=47.5, lon=19.0):
        """Fetches external temperature for SOH compensation (FR5)."""
        #
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.weather_api_key}&units=metric"
        try:
            res = requests.get(url, timeout=2).json()
            return res['main']['temp']
        except Exception:
            return 21.0  # Default to standard temp if API fails

    def calculate_battery_health(self, v_min, ambient_temp):
        """
        Implements Temperature-Compensated Dynamic Threshold logic (FR5).
        Returns 'CRITICAL', 'WARNING', or 'GOOD'.
        """
        #
        if ambient_temp >= 21:
            v_crit = 9.6
        elif 10 <= ambient_temp < 21:
            v_crit = 9.4
        elif 0 <= ambient_temp < 10:
            v_crit = 9.1
        else: # T < 0 (Winter Survival Pack Logic)
            v_crit = 8.5
        
        if v_min < v_crit:
            return "CRITICAL"
        elif v_min < (v_crit + 0.5):
            return "WARNING"
        return "GOOD"

    def process_telemetry(self, event):
        """Main entry point for S3-triggered data processing."""
        for record in event['Records']:
            # 1. Extract Bronze Data
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            raw_data = json.loads(s3.get_object(Bucket=bucket, Key=key)['Body'].read())
            
            vin = raw_data['vin']
            voltage = raw_data['voltage']
            rpm = raw_data['rpm']
            
            # 2. Battery SOH Analysis (Cranking Phase)
            # System detects cranking if RPM is low but active
            if 0 < rpm < 600:
                ambient_t = self.get_ambient_temperature()
                health_status = self.calculate_battery_health(voltage, ambient_t)
                
                # Update Gold Layer with Battery Insight
                self.repo.update_vehicle_insight(vin, {
                    "battery_health": health_status,
                    "last_cranking_v": voltage,
                    "analysis_temp": ambient_t,
                    "updated_at": datetime.now().isoformat()
                })

            # 3. Vampire Drain Tracking
            #
            if voltage < 12.1:
                self.repo.log_event(vin, "LOW_VOLTAGE_ALERT", f"Battery at {voltage}V")

def lambda_handler(event, context):
    processor = SmartDriveProcessor()
    processor.process_telemetry(event)
    return {"statusCode": 200, "body": "Processing Complete"}
