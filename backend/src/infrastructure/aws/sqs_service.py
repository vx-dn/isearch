"""AWS SQS service implementation."""

import json
import logging
from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class SQSService:
    """Service for AWS SQS operations."""

    def __init__(self, region_name: str = None):
        """Initialize SQS service."""
        self.sqs_client = boto3.client("sqs", region_name=region_name)
        self.sqs_resource = boto3.resource("sqs", region_name=region_name)

    async def send_message(
        self,
        queue_url: str,
        message: dict[str, Any],
        delay_seconds: int = 0,
        message_group_id: Optional[str] = None,
        message_deduplication_id: Optional[str] = None,
    ) -> bool:
        """Send message to SQS queue."""
        try:
            kwargs = {"QueueUrl": queue_url, "MessageBody": json.dumps(message)}

            if delay_seconds > 0:
                kwargs["DelaySeconds"] = delay_seconds

            # For FIFO queues
            if message_group_id:
                kwargs["MessageGroupId"] = message_group_id
            if message_deduplication_id:
                kwargs["MessageDeduplicationId"] = message_deduplication_id

            response = self.sqs_client.send_message(**kwargs)
            message_id = response.get("MessageId")

            logger.debug(f"Sent message to queue {queue_url}: {message_id}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to send message to queue {queue_url}: {e}")
            return False

    async def send_batch_messages(
        self, queue_url: str, messages: list[dict[str, Any]]
    ) -> int:
        """Send batch of messages to SQS queue."""
        try:
            if not messages:
                return 0

            # SQS batch send supports up to 10 messages per request
            batch_size = 10
            total_sent = 0

            for i in range(0, len(messages), batch_size):
                batch = messages[i : i + batch_size]
                entries = []

                for idx, message in enumerate(batch):
                    entry = {"Id": str(i + idx), "MessageBody": json.dumps(message)}
                    entries.append(entry)

                response = self.sqs_client.send_message_batch(
                    QueueUrl=queue_url, Entries=entries
                )

                successful = len(response.get("Successful", []))
                failed = len(response.get("Failed", []))
                total_sent += successful

                if failed > 0:
                    logger.warning(f"Failed to send {failed} messages in batch")
                    for failure in response.get("Failed", []):
                        logger.error(
                            f"Message {failure['Id']} failed: {failure.get('Message', 'Unknown error')}"
                        )

            logger.debug(f"Sent {total_sent} messages to queue {queue_url}")
            return total_sent
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to send batch messages to queue {queue_url}: {e}")
            return 0

    async def receive_messages(
        self,
        queue_url: str,
        max_messages: int = 1,
        wait_time_seconds: int = 0,
        visibility_timeout_seconds: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Receive messages from SQS queue."""
        try:
            kwargs = {
                "QueueUrl": queue_url,
                "MaxNumberOfMessages": min(max_messages, 10),  # SQS max is 10
                "WaitTimeSeconds": wait_time_seconds,
            }

            if visibility_timeout_seconds is not None:
                kwargs["VisibilityTimeout"] = visibility_timeout_seconds

            response = self.sqs_client.receive_message(**kwargs)
            messages = response.get("Messages", [])

            # Parse message bodies
            parsed_messages = []
            for message in messages:
                try:
                    body = json.loads(message["Body"])
                    parsed_message = {
                        "MessageId": message["MessageId"],
                        "ReceiptHandle": message["ReceiptHandle"],
                        "Body": body,
                        "Attributes": message.get("Attributes", {}),
                        "MessageAttributes": message.get("MessageAttributes", {}),
                    }
                    parsed_messages.append(parsed_message)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message body: {e}")
                    # Include raw message for manual handling
                    parsed_message = {
                        "MessageId": message["MessageId"],
                        "ReceiptHandle": message["ReceiptHandle"],
                        "Body": message["Body"],  # Raw body
                        "Attributes": message.get("Attributes", {}),
                        "MessageAttributes": message.get("MessageAttributes", {}),
                        "ParseError": str(e),
                    }
                    parsed_messages.append(parsed_message)

            logger.debug(
                f"Received {len(parsed_messages)} messages from queue {queue_url}"
            )
            return parsed_messages
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to receive messages from queue {queue_url}: {e}")
            return []

    async def delete_message(self, queue_url: str, receipt_handle: str) -> bool:
        """Delete message from SQS queue."""
        try:
            self.sqs_client.delete_message(
                QueueUrl=queue_url, ReceiptHandle=receipt_handle
            )
            logger.debug(f"Deleted message from queue {queue_url}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete message from queue {queue_url}: {e}")
            return False

    async def delete_batch_messages(
        self, queue_url: str, receipt_handles: list[str]
    ) -> int:
        """Delete batch of messages from SQS queue."""
        try:
            if not receipt_handles:
                return 0

            # SQS batch delete supports up to 10 messages per request
            batch_size = 10
            total_deleted = 0

            for i in range(0, len(receipt_handles), batch_size):
                batch = receipt_handles[i : i + batch_size]
                entries = []

                for idx, receipt_handle in enumerate(batch):
                    entry = {"Id": str(i + idx), "ReceiptHandle": receipt_handle}
                    entries.append(entry)

                response = self.sqs_client.delete_message_batch(
                    QueueUrl=queue_url, Entries=entries
                )

                successful = len(response.get("Successful", []))
                failed = len(response.get("Failed", []))
                total_deleted += successful

                if failed > 0:
                    logger.warning(f"Failed to delete {failed} messages in batch")

            logger.debug(f"Deleted {total_deleted} messages from queue {queue_url}")
            return total_deleted
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete batch messages from queue {queue_url}: {e}")
            return 0

    async def get_queue_attributes(self, queue_url: str) -> dict[str, Any]:
        """Get queue attributes."""
        try:
            response = self.sqs_client.get_queue_attributes(
                QueueUrl=queue_url, AttributeNames=["All"]
            )
            return response.get("Attributes", {})
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get queue attributes for {queue_url}: {e}")
            return {}

    async def purge_queue(self, queue_url: str) -> bool:
        """Purge all messages from queue."""
        try:
            self.sqs_client.purge_queue(QueueUrl=queue_url)
            logger.info(f"Purged all messages from queue {queue_url}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to purge queue {queue_url}: {e}")
            return False
