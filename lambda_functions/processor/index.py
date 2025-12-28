import json
import boto3
import os
import logging

# Configure logging for CloudWatch observability
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # 1. Extract event data from the S3 Trigger
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    try:
        # 2. Retrieve raw JSON from the Bronze layer (Cold Path)
        response = s3.get_object(Bucket=bucket, Key=key)
        raw_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # 3. Cleaning and Validation
        processed_data = {
            "vin": raw_data.get("vin", "UNKNOWN"),
            "timestamp": raw_data.get("timestamp"),
            "speed": raw_data.get("speed", 0),
            "rpm": raw_data.get("rpm", 0),
            "voltage": float(raw_data.get("voltage", 0.0)),
            "ingested_at": raw_data.get("arrival_time")
        }
        
        # 4. Save to the Silver layer
        dest_bucket = os.environ['SILVER_BUCKET']
        dest_key = key.replace("raw/", "processed/")
        
        s3.put_object(
            Bucket=dest_bucket,
            Key=dest_key,
            Body=json.dumps(processed_data)
        )
        
        logger.info(f"Processing Successful: {key} -> {dest_key}")
        
    except Exception as e:
        logger.error(f"Processing Error ({key}): {str(e)}")
        raise e
