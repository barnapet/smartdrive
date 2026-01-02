import os
from config import ProcessorConfig
from repository import S3Repository
from service import ETLService

# Globális inicializálás (Warm Start optimalizáció)
config = ProcessorConfig()
silver_bucket_name = os.environ.get('SILVER_BUCKET_NAME')
repo = S3Repository(silver_bucket=silver_bucket_name)
etl_service = ETLService(repo, config)

def lambda_handler(event, context):
    processed_count = 0
    
    for record in event['Records']:
        try:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            etl_service.process_file(bucket, key)
            processed_count += 1
            
        except Exception as e:
            # Itt később DLQ (Dead Letter Queue) kezelés ajánlott
            print(f"CRITICAL ERROR processing {record['s3']['object']['key']}: {str(e)}")
            
    return {"processed_count": processed_count}
