import os
import logging
from .repository import TelemetryRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)
repo = TelemetryRepository()

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    try:
        raw_data = repo.get_telemetry(bucket, key)
        
        processed_data = {
            "vin": raw_data.get("vin", "UNKNOWN"),
            "timestamp": raw_data.get("timestamp"),
            "speed": raw_data.get("speed", 0),
            "rpm": raw_data.get("rpm", 0),
            "voltage": float(raw_data.get("voltage", 0.0)),
            "ingested_at": raw_data.get("arrival_time")
        }
        
        dest_bucket = os.environ['SILVER_BUCKET']
        dest_key = key.replace("raw/", "processed/")
        
        repo.save_telemetry(dest_bucket, dest_key, processed_data)
        
        logger.info(f"Feldolgozás sikeres: {key} -> {dest_key}")
        
    except Exception as e:
        logger.error(f"Feldolgozási hiba ({key}): {str(e)}")
        raise e
