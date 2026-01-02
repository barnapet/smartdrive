import boto3
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
