"""Process receipt use case implementation."""

from typing import Any, Protocol

from ..config import DOMAIN_CONFIG
from ..dtos import ProcessReceiptRequest, ProcessReceiptResponse
from ..entities import ProcessingStatus
from ..exceptions import ResourceNotFoundError
from ..repositories import ReceiptRepository, SearchRepository


class S3Service(Protocol):
    """Protocol for S3 service operations."""

    async def resize_large_image(
        self, source_bucket: str, source_key: str, target_bucket: str, target_key: str
    ) -> bool:
        """Resize large images for processing."""
        ...

    async def create_thumbnail(
        self, source_bucket: str, source_key: str, target_bucket: str, target_key: str
    ) -> bool:
        """Create thumbnail image (400x240 pixels)."""
        ...


class TextractService(Protocol):
    """Protocol for Textract service operations."""

    async def extract_text(self, bucket: str, key: str) -> dict[str, Any]:
        """Extract text from image using AWS Textract."""
        ...

    def parse_receipt_data(self, textract_response: dict[str, Any]) -> str:
        """Parse raw Textract response to extract plain text."""
        ...


class SQSService(Protocol):
    """Protocol for SQS service operations."""

    async def send_message(self, queue_url: str, message: dict[str, Any]) -> bool:
        """Send message to SQS queue."""
        ...


class ProcessReceiptUseCase:
    """Use case for processing uploaded receipts."""

    def __init__(
        self,
        receipt_repository: ReceiptRepository,
        search_repository: SearchRepository,
        s3_service: S3Service,
        textract_service: TextractService,
    ):
        self.receipt_repository = receipt_repository
        self.search_repository = search_repository
        self.s3_service = s3_service
        self.textract_service = textract_service
        self.max_image_size = (
            DOMAIN_CONFIG.file_constraints.MAX_IMAGE_SIZE_FOR_PROCESSING
        )

    async def execute(self, request: ProcessReceiptRequest) -> ProcessReceiptResponse:
        """Execute the process receipt use case."""
        # Get the receipt
        receipt = await self.receipt_repository.get_by_id(request.receipt_id)
        if not receipt:
            raise ResourceNotFoundError(f"Receipt {request.receipt_id} not found")

        # Mark as processing
        receipt.update_processing_status(ProcessingStatus.PROCESSING)
        await self.receipt_repository.update(receipt)

        try:
            # Step 1: Resize large images if needed
            processing_key = receipt.s3_keys["original"]
            if receipt.file_size > self.max_image_size:
                await self.s3_service.resize_large_image(
                    source_bucket=request.s3_bucket,
                    source_key=receipt.s3_keys["original"],
                    target_bucket=request.s3_bucket,
                    target_key=receipt.s3_keys["resized"],
                )
                processing_key = receipt.s3_keys["resized"]

            # Step 2: Create thumbnail
            await self.s3_service.create_thumbnail(
                source_bucket=request.s3_bucket,
                source_key=processing_key,
                target_bucket=request.s3_bucket,
                target_key=receipt.s3_keys["thumbnail"],
            )

            # Step 3: Extract text using Textract
            textract_response = await self.textract_service.extract_text(
                bucket=request.s3_bucket, key=processing_key
            )

            # Step 4: Parse the response
            extracted_text = self.textract_service.parse_receipt_data(textract_response)

            # Step 5: Update receipt with results
            receipt.set_extraction_results(
                extracted_text=extracted_text, structured_data=textract_response
            )

            # Step 6: Save to database
            await self.receipt_repository.update(receipt)

            # Step 7: Index in search
            await self.search_repository.index_document(receipt)

            return ProcessReceiptResponse(
                receipt_id=request.receipt_id,
                success=True,
                extracted_text=extracted_text,
                structured_data=textract_response,
            )

        except Exception as e:
            # Mark extraction as failed
            receipt.mark_extraction_failed()
            await self.receipt_repository.update(receipt)

            # Still index the document (with "N/A" text) so it appears in search
            await self.search_repository.index_document(receipt)

            error_message = f"Failed to process receipt: {str(e)}"

            return ProcessReceiptResponse(
                receipt_id=request.receipt_id,
                success=False,
                extracted_text="N/A",
                structured_data={},
                error_message=error_message,
            )
