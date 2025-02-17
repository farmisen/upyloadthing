import asyncio
from typing import BinaryIO, List

import httpx

from upyloadthing.base_client import BaseUTApi
from upyloadthing.schemas import (
    DeleteFileResponse,
    ListFileResponse,
    RenameFilesResponse,
    UploadResult,
    UsageInfoResponse,
)
from upyloadthing.utils import snakify


class AsyncUTApi(BaseUTApi):
    """Asynchronous UploadThing API client.

    This class provides asynchronous methods for interacting with the
    UploadThing API. Use this client for async/await operations.
    """

    async def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Make an async HTTP request to the UploadThing API.

        Args:
            method: HTTP method to use
            path: API endpoint path
            data: Request data/parameters
            timeout: Request timeout in seconds

        Returns:
            dict: Parsed JSON response

        Raises:
            httpx.TimeoutException: If the request times out
            httpx.HTTPStatusError: If the server returns an error status
        """
        url, headers, request_kwargs = self._prepare_request(
            method, path, data
        )
        request_kwargs = request_kwargs or {}
        request_kwargs.update({"timeout": timeout})

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method, url=url, headers=headers, **request_kwargs
                )
                response.raise_for_status()
                result = snakify(response.json())
                if isinstance(result, dict):  # Type guard
                    return result
                raise TypeError("Expected dict response")
        except httpx.TimeoutException:
            raise httpx.TimeoutException(
                f"Request to {url} timed out after {timeout} seconds"
            ) from None
        except httpx.HTTPStatusError as e:
            self._handle_error_response(e)
            raise  # This ensures we always return or raise

    async def _upload_single_file(self, file_data: dict) -> UploadResult:
        """Upload a single file to UploadThing.

        Args:
            file_data: Dictionary containing file metadata and content

        Returns:
            UploadResult: Result of the upload operation
        """
        result = await self._request(
            "PUT",
            file_data["ingest_url"],
            data={
                "file": (
                    file_data["name"],
                    file_data["file"],
                    file_data["type"],
                )
            },
        )

        return UploadResult(
            file_key=file_data["file_key"],
            name=file_data["name"],
            size=file_data["size"],
            type=file_data["type"],
            **result,
        )

    async def upload_files(
        self,
        files: BinaryIO | List[BinaryIO],
        content_disposition: str = "inline",
        acl: str | None = "public-read",
    ) -> List[UploadResult]:
        """Upload one or more files to UploadThing asynchronously.

        Args:
            files: Single file or list of files to upload (file-like objects)
            content_disposition: Content disposition header value ('inline' or 'attachment')
            acl: Access control list setting for uploaded files

        Returns:
            List[UploadResult]: List of upload results containing file information
        """  # noqa: E501
        if not isinstance(files, list):
            files = [files]

        files_data = [
            self._prepare_file_data(file, content_disposition, acl)
            for file in files
        ]

        # Upload all files in parallel
        results = await asyncio.gather(
            *[self._upload_single_file(file_data) for file_data in files_data]
        )

        return results

    async def delete_files(
        self, keys: str | List[str], key_type: str | None = "file_key"
    ) -> DeleteFileResponse:
        """Delete one or more files from UploadThing asynchronously.

        Args:
            keys: Single key or list of keys identifying files to delete
            key_type: Type of key provided ('file_key' or 'custom_id')

        Returns:
            DeleteFileResponse: Response containing deletion results
        """
        keys_list = [keys] if isinstance(keys, str) else keys
        data = {
            "fileKeys" if key_type == "file_key" else "customIds": keys_list
        }
        result = await self._request("POST", "/v6/deleteFiles", data)
        return DeleteFileResponse(**result)

    async def list_files(
        self, limit: int | None = None, offset: int | None = None
    ) -> ListFileResponse:
        """List files stored in UploadThing asynchronously.

        Args:
            limit: Maximum number of files to return
            offset: Number of files to skip for pagination

        Returns:
            ListFileResponse: Response containing list of files
        """
        params = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        response = await self._request("POST", "/v6/listFiles", params)
        return ListFileResponse(**response)

    async def get_usage_info(self) -> UsageInfoResponse:
        """Get usage information for the UploadThing account asynchronously.

        Returns:
            UsageInfoResponse: Response containing usage statistics
        """
        result = await self._request("POST", "/v6/getUsageInfo")
        return UsageInfoResponse(**result)

    async def rename_files(
        self, updates: List[dict[str, str]]
    ) -> RenameFilesResponse:
        """Rename one or more files asynchronously.

        Args:
            updates: List of update objects containing either:
                    - fileKey and newName
                    - customId and newName

        Returns:
            RenameFilesResponse: Response containing rename results
        """
        result = await self._request(
            "POST", "/v6/renameFiles", {"updates": updates}
        )
        return RenameFilesResponse(**result)
