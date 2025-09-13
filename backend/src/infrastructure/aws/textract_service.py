"""AWS Textract service implementation."""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class TextractService:
    """Service for AWS Textract operations."""

    def __init__(self, region_name: str = None):
        """Initialize Textract service."""
        self.textract_client = boto3.client("textract", region_name=region_name)

    async def extract_text(self, bucket: str, key: str) -> Dict[str, Any]:
        """Extract text from image using AWS Textract."""
        try:
            response = self.textract_client.detect_document_text(
                Document={"S3Object": {"Bucket": bucket, "Name": key}}
            )
            logger.debug(f"Extracted text from {bucket}/{key}")
            return response
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to extract text from {bucket}/{key}: {e}")
            raise

    def parse_receipt_data(self, textract_response: Dict[str, Any]) -> str:
        """Parse raw Textract response to extract plain text."""
        try:
            blocks = textract_response.get("Blocks", [])
            text_lines = []

            # Extract all LINE type blocks
            for block in blocks:
                if block.get("BlockType") == "LINE":
                    text = block.get("Text", "").strip()
                    if text:
                        text_lines.append(text)

            # Join all lines with newlines
            extracted_text = "\n".join(text_lines)

            logger.debug(f"Parsed {len(text_lines)} lines of text")
            return extracted_text
        except Exception as e:
            logger.error(f"Failed to parse Textract response: {e}")
            return "N/A"

    def extract_key_value_pairs(
        self, textract_response: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract key-value pairs from Textract response (for forms)."""
        try:
            blocks = textract_response.get("Blocks", [])
            key_value_pairs = {}

            # Create a map of block IDs to blocks for easier lookup
            block_map = {block["Id"]: block for block in blocks}

            # Find KEY_VALUE_SET blocks
            for block in blocks:
                if block.get("BlockType") == "KEY_VALUE_SET":
                    entity_type = block.get("EntityTypes", [])

                    if "KEY" in entity_type:
                        # This is a key block
                        key_text = self._get_text_from_relationships(
                            block, block_map, "CHILD"
                        )

                        # Find the associated value
                        value_text = self._get_text_from_relationships(
                            block, block_map, "VALUE"
                        )

                        if key_text and value_text:
                            key_value_pairs[key_text.strip()] = value_text.strip()

            logger.debug(f"Extracted {len(key_value_pairs)} key-value pairs")
            return key_value_pairs
        except Exception as e:
            logger.error(f"Failed to extract key-value pairs: {e}")
            return {}

    def _get_text_from_relationships(
        self,
        block: Dict[str, Any],
        block_map: Dict[str, Dict[str, Any]],
        relationship_type: str,
    ) -> str:
        """Helper method to extract text from block relationships."""
        try:
            text_parts = []
            relationships = block.get("Relationships", [])

            for relationship in relationships:
                if relationship.get("Type") == relationship_type:
                    ids = relationship.get("Ids", [])

                    for block_id in ids:
                        related_block = block_map.get(block_id)
                        if not related_block:
                            continue

                        if related_block.get("BlockType") == "WORD":
                            text = related_block.get("Text", "")
                            if text:
                                text_parts.append(text)
                        elif related_block.get("BlockType") == "KEY_VALUE_SET":
                            # For VALUE relationships, get the child text
                            child_text = self._get_text_from_relationships(
                                related_block, block_map, "CHILD"
                            )
                            if child_text:
                                text_parts.append(child_text)

            return " ".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to get text from relationships: {e}")
            return ""

    def extract_tables(self, textract_response: Dict[str, Any]) -> List[List[str]]:
        """Extract tables from Textract response."""
        try:
            blocks = textract_response.get("Blocks", [])
            block_map = {block["Id"]: block for block in blocks}

            tables = []

            # Find TABLE blocks
            for block in blocks:
                if block.get("BlockType") == "TABLE":
                    table_data = self._extract_table_data(block, block_map)
                    if table_data:
                        tables.append(table_data)

            logger.debug(f"Extracted {len(tables)} tables")
            return tables
        except Exception as e:
            logger.error(f"Failed to extract tables: {e}")
            return []

    def _extract_table_data(
        self, table_block: Dict[str, Any], block_map: Dict[str, Dict[str, Any]]
    ) -> List[List[str]]:
        """Extract data from a table block."""
        try:
            relationships = table_block.get("Relationships", [])
            cells = {}

            # Get all cell relationships
            for relationship in relationships:
                if relationship.get("Type") == "CHILD":
                    for cell_id in relationship.get("Ids", []):
                        cell_block = block_map.get(cell_id)
                        if cell_block and cell_block.get("BlockType") == "CELL":
                            row_index = (
                                cell_block.get("RowIndex", 1) - 1
                            )  # Convert to 0-based
                            col_index = (
                                cell_block.get("ColumnIndex", 1) - 1
                            )  # Convert to 0-based

                            # Get cell text
                            cell_text = self._get_text_from_relationships(
                                cell_block, block_map, "CHILD"
                            )

                            cells[(row_index, col_index)] = cell_text

            # Convert cells dict to 2D array
            if not cells:
                return []

            max_row = max(pos[0] for pos in cells.keys()) + 1
            max_col = max(pos[1] for pos in cells.keys()) + 1

            table_data = []
            for row in range(max_row):
                row_data = []
                for col in range(max_col):
                    cell_text = cells.get((row, col), "")
                    row_data.append(cell_text)
                table_data.append(row_data)

            return table_data
        except Exception as e:
            logger.error(f"Failed to extract table data: {e}")
            return []

    async def analyze_expense(self, bucket: str, key: str) -> Dict[str, Any]:
        """Analyze expense document using Textract Analyze Expense API."""
        try:
            response = self.textract_client.analyze_expense(
                Document={"S3Object": {"Bucket": bucket, "Name": key}}
            )
            logger.debug(f"Analyzed expense document {bucket}/{key}")
            return response
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to analyze expense document {bucket}/{key}: {e}")
            raise

    def parse_expense_data(self, expense_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse expense analysis response to extract structured data."""
        try:
            expense_documents = expense_response.get("ExpenseDocuments", [])
            if not expense_documents:
                return {}

            # Take the first document (receipts typically have one)
            document = expense_documents[0]

            # Extract summary fields
            summary_fields = {}
            for field in document.get("SummaryFields", []):
                field_type = field.get("Type", {}).get("Text", "")
                field_value = field.get("ValueDetection", {}).get("Text", "")
                if field_type and field_value:
                    summary_fields[field_type.lower().replace(" ", "_")] = field_value

            # Extract line items
            line_items = []
            for line_item_group in document.get("LineItemGroups", []):
                for line_item in line_item_group.get("LineItems", []):
                    item_data = {}
                    for field in line_item.get("LineItemExpenseFields", []):
                        field_type = field.get("Type", {}).get("Text", "")
                        field_value = field.get("ValueDetection", {}).get("Text", "")
                        if field_type and field_value:
                            item_data[field_type.lower().replace(" ", "_")] = (
                                field_value
                            )
                    if item_data:
                        line_items.append(item_data)

            result = {"summary_fields": summary_fields, "line_items": line_items}

            logger.debug(
                f"Parsed expense data: {len(summary_fields)} summary fields, {len(line_items)} line items"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to parse expense data: {e}")
            return {}
