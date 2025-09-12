"""AWS DynamoDB service implementation."""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DynamoDBService:
    """Service for DynamoDB operations."""

    def __init__(self, region_name: str = None):
        """Initialize DynamoDB service."""
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.client = boto3.client("dynamodb", region_name=region_name)

    async def put_item(self, table_name: str, item: Dict[str, Any]) -> bool:
        """Put an item into DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(Item=item)
            logger.debug(f"Put item to {table_name}: {item.get('id', 'unknown')}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to put item to {table_name}: {e}")
            return False

    async def get_item(
        self, table_name: str, key: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get an item from DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key=key)
            return response.get("Item")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get item from {table_name}: {e}")
            return None

    async def update_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Update an item in DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)
            kwargs = {
                "Key": key,
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_attribute_values,
                "ReturnValues": "UPDATED_NEW",
            }
            if expression_attribute_names:
                kwargs["ExpressionAttributeNames"] = expression_attribute_names

            table.update_item(**kwargs)
            logger.debug(f"Updated item in {table_name}: {key}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to update item in {table_name}: {e}")
            return False

    async def delete_item(self, table_name: str, key: Dict[str, Any]) -> bool:
        """Delete an item from DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)
            table.delete_item(Key=key)
            logger.debug(f"Deleted item from {table_name}: {key}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete item from {table_name}: {e}")
            return False

    async def query(
        self,
        table_name: str,
        key_condition_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[Dict[str, Any]] = None,
        scan_index_forward: bool = True,
    ) -> Dict[str, Any]:
        """Query items from DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)
            kwargs = {
                "KeyConditionExpression": key_condition_expression,
                "ExpressionAttributeValues": expression_attribute_values,
                "ScanIndexForward": scan_index_forward,
            }

            if expression_attribute_names:
                kwargs["ExpressionAttributeNames"] = expression_attribute_names
            if index_name:
                kwargs["IndexName"] = index_name
            if limit:
                kwargs["Limit"] = limit
            if exclusive_start_key:
                kwargs["ExclusiveStartKey"] = exclusive_start_key

            response = table.query(**kwargs)
            return {
                "Items": response.get("Items", []),
                "LastEvaluatedKey": response.get("LastEvaluatedKey"),
                "Count": response.get("Count", 0),
                "ScannedCount": response.get("ScannedCount", 0),
            }
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to query {table_name}: {e}")
            return {
                "Items": [],
                "LastEvaluatedKey": None,
                "Count": 0,
                "ScannedCount": 0,
            }

    async def batch_write(
        self,
        table_name: str,
        items: List[Dict[str, Any]],
        delete_keys: List[Dict[str, Any]] = None,
    ) -> int:
        """Batch write items to DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)

            with table.batch_writer() as batch:
                # Add items
                for item in items:
                    batch.put_item(Item=item)

                # Delete items
                if delete_keys:
                    for key in delete_keys:
                        batch.delete_item(Key=key)

            total_operations = len(items) + (len(delete_keys) if delete_keys else 0)
            logger.debug(f"Batch write to {table_name}: {total_operations} operations")
            return total_operations
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed batch write to {table_name}: {e}")
            return 0

    async def scan_table(
        self,
        table_name: str,
        filter_expression: Optional[str] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Scan DynamoDB table."""
        try:
            table = self.dynamodb.Table(table_name)
            kwargs = {}

            if filter_expression:
                kwargs["FilterExpression"] = filter_expression
            if expression_attribute_values:
                kwargs["ExpressionAttributeValues"] = expression_attribute_values
            if expression_attribute_names:
                kwargs["ExpressionAttributeNames"] = expression_attribute_names
            if limit:
                kwargs["Limit"] = limit
            if exclusive_start_key:
                kwargs["ExclusiveStartKey"] = exclusive_start_key

            response = table.scan(**kwargs)
            return {
                "Items": response.get("Items", []),
                "LastEvaluatedKey": response.get("LastEvaluatedKey"),
                "Count": response.get("Count", 0),
                "ScannedCount": response.get("ScannedCount", 0),
            }
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to scan {table_name}: {e}")
            return {
                "Items": [],
                "LastEvaluatedKey": None,
                "Count": 0,
                "ScannedCount": 0,
            }
