"""Meilisearch service implementation."""

import asyncio
import logging
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class MeilisearchService:
    """Service for Meilisearch operations."""

    def __init__(self, host: str, api_key: str, index_name: str = "receipts"):
        """Initialize Meilisearch service."""
        self.host = host.rstrip("/")
        self.api_key = api_key
        self.index_name = index_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make HTTP request to Meilisearch."""
        url = f"{self.host}/{endpoint.lstrip('/')}"

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                kwargs = {"headers": self.headers, "params": params}

                if data is not None:
                    kwargs["json"] = data

                async with session.request(method, url, **kwargs) as response:
                    if response.content_type == "application/json":
                        result = await response.json()
                    else:
                        result = {"text": await response.text()}

                    if response.status >= 400:
                        logger.error(f"Meilisearch error {response.status}: {result}")
                        raise Exception(
                            f"Meilisearch error {response.status}: {result}"
                        )

                    return result
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Meilisearch at {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Meilisearch request failed: {e}")
            raise

    async def index_document(self, document: dict[str, Any]) -> bool:
        """Index a document in Meilisearch."""
        try:
            # Ensure the document has an id field
            if "id" not in document:
                document["id"] = document.get("receipt_id", document.get("image_id"))

            endpoint = f"/indexes/{self.index_name}/documents"
            response = await self._make_request("POST", endpoint, data=[document])

            task_uid = response.get("taskUid")
            logger.debug(f"Indexed document {document['id']} (task: {task_uid})")
            return True
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return False

    async def index_documents(self, documents: list[dict[str, Any]]) -> bool:
        """Index multiple documents in Meilisearch."""
        try:
            if not documents:
                return True

            # Ensure all documents have id fields
            for doc in documents:
                if "id" not in doc:
                    doc["id"] = doc.get("receipt_id", doc.get("image_id"))

            endpoint = f"/indexes/{self.index_name}/documents"
            response = await self._make_request("POST", endpoint, data=documents)

            task_uid = response.get("taskUid")
            logger.debug(f"Indexed {len(documents)} documents (task: {task_uid})")
            return True
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return False

    async def search(
        self,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        sort: Optional[list[str]] = None,
        attributes_to_highlight: Optional[list[str]] = None,
        attributes_to_crop: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Search documents in Meilisearch."""
        try:
            endpoint = f"/indexes/{self.index_name}/search"
            search_params = {"q": query, "limit": limit, "offset": offset}

            if filters:
                # Convert filters to Meilisearch filter format
                filter_expressions = []
                for key, value in filters.items():
                    if isinstance(value, dict):
                        # Handle range filters
                        if "gte" in value and "lte" in value:
                            filter_expressions.append(
                                f"{key} >= {value['gte']} AND {key} <= {value['lte']}"
                            )
                        elif "gte" in value:
                            filter_expressions.append(f"{key} >= {value['gte']}")
                        elif "lte" in value:
                            filter_expressions.append(f"{key} <= {value['lte']}")
                    else:
                        filter_expressions.append(f"{key} = {value}")

                if filter_expressions:
                    search_params["filter"] = " AND ".join(filter_expressions)

            if sort:
                search_params["sort"] = sort

            if attributes_to_highlight:
                search_params["attributesToHighlight"] = attributes_to_highlight

            if attributes_to_crop:
                search_params["attributesToCrop"] = attributes_to_crop

            response = await self._make_request("POST", endpoint, data=search_params)

            logger.debug(
                f"Search query '{query}' returned {len(response.get('hits', []))} results"
            )
            return response
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return {"hits": [], "estimatedTotalHits": 0, "processingTimeMs": 0}

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from Meilisearch."""
        try:
            endpoint = f"/indexes/{self.index_name}/documents/{document_id}"
            response = await self._make_request("DELETE", endpoint)

            task_uid = response.get("taskUid")
            logger.debug(f"Deleted document {document_id} (task: {task_uid})")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    async def delete_documents(self, document_ids: list[str]) -> int:
        """Delete multiple documents from Meilisearch."""
        try:
            if not document_ids:
                return 0

            endpoint = f"/indexes/{self.index_name}/documents/delete-batch"
            response = await self._make_request("POST", endpoint, data=document_ids)

            task_uid = response.get("taskUid")
            logger.debug(f"Deleted {len(document_ids)} documents (task: {task_uid})")
            return len(document_ids)
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return 0

    async def update_document(self, document: dict[str, Any]) -> bool:
        """Update a document in Meilisearch."""
        try:
            # Ensure the document has an id field
            if "id" not in document:
                document["id"] = document.get("receipt_id", document.get("image_id"))

            endpoint = f"/indexes/{self.index_name}/documents"
            response = await self._make_request("PUT", endpoint, data=[document])

            task_uid = response.get("taskUid")
            logger.debug(f"Updated document {document['id']} (task: {task_uid})")
            return True
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False

    async def get_document(self, document_id: str) -> Optional[dict[str, Any]]:
        """Get a document by ID from Meilisearch."""
        try:
            endpoint = f"/indexes/{self.index_name}/documents/{document_id}"
            response = await self._make_request("GET", endpoint)
            return response
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    async def clear_index(self) -> bool:
        """Clear all documents from the index."""
        try:
            endpoint = f"/indexes/{self.index_name}/documents"
            response = await self._make_request("DELETE", endpoint)

            task_uid = response.get("taskUid")
            logger.info(
                f"Cleared all documents from index {self.index_name} (task: {task_uid})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            return False

    async def get_index_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        try:
            endpoint = f"/indexes/{self.index_name}/stats"
            response = await self._make_request("GET", endpoint)
            return response
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}

    async def update_settings(self, settings: dict[str, Any]) -> bool:
        """Update index settings."""
        try:
            endpoint = f"/indexes/{self.index_name}/settings"
            response = await self._make_request("PATCH", endpoint, data=settings)

            task_uid = response.get("taskUid")
            logger.debug(f"Updated index settings (task: {task_uid})")
            return True
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False

    async def get_settings(self) -> dict[str, Any]:
        """Get current index settings."""
        try:
            endpoint = f"/indexes/{self.index_name}/settings"
            response = await self._make_request("GET", endpoint)
            return response
        except Exception as e:
            logger.error(f"Failed to get settings: {e}")
            return {}

    async def wait_for_task(self, task_uid: int, timeout: int = 30) -> bool:
        """Wait for a task to complete."""
        try:
            endpoint = f"/tasks/{task_uid}"
            start_time = asyncio.get_event_loop().time()

            while True:
                response = await self._make_request("GET", endpoint)
                status = response.get("status")

                if status in ["succeeded", "failed"]:
                    logger.debug(f"Task {task_uid} completed with status: {status}")
                    return status == "succeeded"

                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning(f"Task {task_uid} timed out after {timeout} seconds")
                    return False

                # Wait before checking again
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to wait for task {task_uid}: {e}")
            return False
