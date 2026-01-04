import boto3
import time
import json
from decimal import Decimal
from domain.interfaces import IInsightRepository

class DynamoDBInsightRepository(IInsightRepository):
    def __init__(self, table_name: str):
        self.table = boto3.resource('dynamodb').Table(table_name)

    def save_insight(self, insight: dict):
        item = json.loads(json.dumps(insight), parse_float=Decimal)
        self.table.put_item(Item=item)

    def get_last_insights(self, vin: str, limit: int):
        response = self.table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('vin').eq(vin),
            ScanIndexForward=False,
            Limit=limit
        )
        return response.get('Items', [])

class WeatherCacheRepository:
    def __init__(self, table_name: str):
        self.table = boto3.resource('dynamodb').Table(table_name)
        self.ttl_seconds = 3600

    def get_cached_weather(self, lat: float, lon: float):
        geo_key = f"{round(lat, 2)}#{round(lon, 2)}"
        response = self.table.get_item(Key={'geo_key': geo_key})
        item = response.get('Item')
        
        if item and item.get('expires_at', 0) > int(time.time()):
            return item
        return None

    def save_weather(self, lat: float, lon: float, temp: float, forecast_min: float):
        geo_key = f"{round(lat, 2)}#{round(lon, 2)}"
        self.table.put_item(Item={
            'geo_key': geo_key,
            'temperature': Decimal(str(temp)),
            'forecast_min': Decimal(str(forecast_min)) if forecast_min is not None else None,
            'expires_at': int(time.time()) + self.ttl_seconds
        })
