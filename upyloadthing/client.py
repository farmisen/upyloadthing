from typing import BinaryIO, List

import httpx

from upyloadthing.base_client import BaseUTApi
from upyloadthing.schemas import (
    DeleteFileResponse,
    ListFileResponse,
    RenameFilesResponse,
    UpdateACLResponse,
    UploadResult,
    UsageInfoResponse,
)
from upyloadthing.utils import snakify


class UTApi(BaseUTApi):
    """Synchronous UploadThing API client.

    This class provides synchronous methods for interacting with the
    UploadThing API. Use this client for standard synchronous operations.
    """

    def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Make an HTTP request to the UploadThing API.

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
            with httpx.Client() as client:
                response = client.request(
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

    def upload_files(
        self,
        files: BinaryIO | List[BinaryIO],
        content_disposition: str = "inline",
        acl: str | None = "public-read",
    ) -> List[UploadResult]:
        """Upload one or more files to UploadThing synchronously.

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

        results = []
        for file_data in files_data:
            result = self._request(
                "PUT",
                file_data["ingest_url"],
                {
                    "file": (
                        file_data["name"],
                        file_data["file"],
                        file_data["type"],
                    )
                },
            )

            upload_result = UploadResult(
                file_key=file_data["file_key"],
                name=file_data["name"],
                size=file_data["size"],
                type=file_data["type"],
                **result,
            )
            results.append(upload_result)

        return results

    def delete_files(
        self, keys: str | List[str], key_type: str | None = "file_key"
    ) -> DeleteFileResponse:
        """Delete one or more files from UploadThing synchronously.

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
        result = self._request("POST", "/v6/deleteFiles", data)
        return DeleteFileResponse(**result)

    def list_files(
        self, limit: int | None = None, offset: int | None = None
    ) -> ListFileResponse:
        """List files stored in UploadThing synchronously.

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

        response = self._request("POST", "/v6/listFiles", params)
        return ListFileResponse(**response)

    def get_usage_info(self) -> UsageInfoResponse:
        """Get usage information for the UploadThing account synchronously.

        Returns:
            UsageInfoResponse: Response containing usage statistics
        """
        result = self._request("POST", "/v6/getUsageInfo")
        return UsageInfoResponse(**result)

    def rename_files(
        self, updates: List[dict[str, str]]
    ) -> RenameFilesResponse:
        """Rename one or more files synchronously.

        Args:
            updates: List of update objects containing either:
                    - fileKey and newName
                    - customId and newName

        Returns:
            RenameFilesResponse: Response containing rename results
        """
        result = self._request("POST", "/v6/renameFiles", {"updates": updates})
        return RenameFilesResponse(**result)

    def update_acl(self, updates: List[dict[str, str]]) -> UpdateACLResponse:
        """Update ACL settings for one or more files synchronously.

        Args:
            updates: List of update objects containing either:
                    - fileKey and acl
                    - customId and acl
                    where acl must be a valid ACLValue

        Returns:
            UpdateACLResponse: Response containing update results
        """
        self._validate_acl_updates(updates)
        result = self._request("POST", "/v6/updateACL", {"updates": updates})
        return UpdateACLResponse(**result)
