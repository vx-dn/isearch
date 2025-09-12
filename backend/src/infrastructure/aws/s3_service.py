"""AWS S3 service implementation."""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, List, Optional, Any
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3 operations."""

    def __init__(self, region_name: str = None):
        """Initialize S3 service."""
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.s3_resource = boto3.resource("s3", region_name=region_name)

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        file_size: int,
        content_type: str = "image/jpeg",
        expiration: int = 3600,
    ) -> Dict[str, Any]:
        """Generate presigned URL for file upload."""
        try:
            # Define the policy for the presigned URL
            fields = {
                "Content-Type": content_type,
                "x-amz-meta-file-size": str(file_size),
            }

            conditions = [
                {"Content-Type": content_type},
                ["content-length-range", 1, file_size],
                {"x-amz-meta-file-size": str(file_size)},
            ]

            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=bucket,
                Key=key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expiration,
            )

            logger.debug(f"Generated presigned URL for {bucket}/{key}")
            return presigned_post
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to generate presigned URL for {bucket}/{key}: {e}")
            raise

    async def generate_presigned_url_for_download(
        self, bucket: str, key: str, expiration: int = 3600
    ) -> str:
        """Generate presigned URL for file download/viewing."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expiration,
            )
            logger.debug(f"Generated download URL for {bucket}/{key}")
            return url
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to generate download URL for {bucket}/{key}: {e}")
            raise

    async def generate_thumbnail_url(
        self, bucket: str, key: str, expiration: int = 3600
    ) -> str:
        """Generate URL for thumbnail image."""
        return await self.generate_presigned_url_for_download(bucket, key, expiration)

    async def resize_large_image(
        self,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
        max_size: tuple = (2048, 2048),
    ) -> bool:
        """Resize large images for processing."""
        try:
            # Download the original image
            response = self.s3_client.get_object(Bucket=source_bucket, Key=source_key)
            image_data = response["Body"].read()

            # Open and resize the image
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if necessary (handles RGBA, etc.)
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Resize maintaining aspect ratio
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save to bytes
                output_buffer = io.BytesIO()
                img.save(output_buffer, format="JPEG", quality=85, optimize=True)
                output_buffer.seek(0)

                # Upload resized image
                self.s3_client.put_object(
                    Bucket=target_bucket,
                    Key=target_key,
                    Body=output_buffer.getvalue(),
                    ContentType="image/jpeg",
                    Metadata={"resized": "true", "original_key": source_key},
                )

            logger.debug(
                f"Resized image from {source_bucket}/{source_key} to {target_bucket}/{target_key}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to resize image {source_bucket}/{source_key}: {e}")
            return False

    async def create_thumbnail(
        self,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
        size: tuple = (400, 240),
    ) -> bool:
        """Create thumbnail image."""
        try:
            # Download the source image
            response = self.s3_client.get_object(Bucket=source_bucket, Key=source_key)
            image_data = response["Body"].read()

            # Open and create thumbnail
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Create thumbnail maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Create a new image with the exact thumbnail size and center the resized image
                thumbnail = Image.new("RGB", size, (255, 255, 255))  # White background

                # Calculate position to center the image
                x = (size[0] - img.width) // 2
                y = (size[1] - img.height) // 2
                thumbnail.paste(img, (x, y))

                # Save to bytes
                output_buffer = io.BytesIO()
                thumbnail.save(output_buffer, format="JPEG", quality=80, optimize=True)
                output_buffer.seek(0)

                # Upload thumbnail
                self.s3_client.put_object(
                    Bucket=target_bucket,
                    Key=target_key,
                    Body=output_buffer.getvalue(),
                    ContentType="image/jpeg",
                    Metadata={
                        "thumbnail": "true",
                        "original_key": source_key,
                        "thumbnail_size": f"{size[0]}x{size[1]}",
                    },
                )

            logger.debug(
                f"Created thumbnail from {source_bucket}/{source_key} to {target_bucket}/{target_key}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to create thumbnail for {source_bucket}/{source_key}: {e}"
            )
            return False

    async def delete_objects(self, bucket: str, keys: List[str]) -> int:
        """Delete multiple objects from S3."""
        if not keys:
            return 0

        try:
            # S3 batch delete supports up to 1000 objects per request
            deleted_count = 0
            batch_size = 1000

            for i in range(0, len(keys), batch_size):
                batch_keys = keys[i : i + batch_size]
                delete_objects = [{"Key": key} for key in batch_keys]

                response = self.s3_client.delete_objects(
                    Bucket=bucket, Delete={"Objects": delete_objects, "Quiet": True}
                )

                deleted_count += len(response.get("Deleted", []))

                # Log any errors
                if "Errors" in response:
                    for error in response["Errors"]:
                        logger.error(
                            f"Failed to delete {error['Key']}: {error['Message']}"
                        )

            logger.debug(f"Deleted {deleted_count} objects from {bucket}")
            return deleted_count
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete objects from {bucket}: {e}")
            return 0

    async def copy_object(
        self, source_bucket: str, source_key: str, target_bucket: str, target_key: str
    ) -> bool:
        """Copy object from one location to another."""
        try:
            copy_source = {"Bucket": source_bucket, "Key": source_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=target_bucket, Key=target_key
            )
            logger.debug(
                f"Copied {source_bucket}/{source_key} to {target_bucket}/{target_key}"
            )
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to copy object: {e}")
            return False

    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if object exists in S3."""
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Error checking if object exists {bucket}/{key}: {e}")
            return False
