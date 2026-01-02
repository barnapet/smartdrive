import boto3
import pandas as pd
import awswrangler as wr
import json
from typing import Optional

class S3Repository:
    def __init__(self, silver_bucket: str):
        self.s3_client = boto3.client('s3')
        self.silver_bucket = silver_bucket

    def fetch_json_as_df(self, bucket: str, key: str) -> pd.DataFrame:
        """
        Letölti a JSON-t és 'kilapítja' (flatten) a pids listát táblázattá.
        """
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        
        try:
            data = json.loads(file_content)
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in {key}")
            return pd.DataFrame()

        # DETEKTÁLÁS: Ez egy SmartDrive v1.3 nested JSON (pids lista)?
        if isinstance(data, dict) and 'pids' in data and isinstance(data['pids'], list):
            # A 'pids' lista elemeit sorokká alakítjuk
            # A 'meta' paraméterrel örökítjük a 'vin'-t minden sorra a fejrészből
            df = pd.json_normalize(
                data, 
                record_path=['pids'], 
                meta=['vin'] 
            )
        else:
            # Fallback: Ha lapos a JSON (pl. régi verzió), vagy más formátum
            df = pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)

        # IDŐBÉLYEG KONVERZIÓ
        # A normalize stringként hagyja a dátumot, ezt át kell váltanunk datetime-ra
        # a service.py matek moduljához.
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        return df

    def save_dataframe_to_parquet(self, df: pd.DataFrame, prefix: str, compression: str = "snappy"):
        """
        Elmenti a DataFrame-et Parquet formátumban a Silver bucketbe.
        """
        path = f"s3://{self.silver_bucket}/{prefix}/"
        
        # Ha üres a DF, ne írjunk
        if df.empty:
            return

        wr.s3.to_parquet(
            df=df,
            path=path,
            dataset=True,
            partition_cols=['vin', 'date'],
            mode="append",
            compression=compression
        )
