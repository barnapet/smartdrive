import boto3
import json

class TelemetryRepository:
    def __init__(self):
        self.s3 = boto3.client('s3')

    def get_telemetry(self, bucket, key):
        response = self.s3.get_object(Bucket=bucket, Key=key)
        return json.loads(response['Body'].read().decode('utf-8'))

    def save_telemetry(self, bucket, key, data):
        self.s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data)
        )
