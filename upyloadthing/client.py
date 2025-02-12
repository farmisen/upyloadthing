import base64
import json
import mimetypes
import os
import uuid
from typing import BinaryIO, List

import requests

from upyloadthing.file_key import generate_key
from upyloadthing.presign import make_presigned_url
from upyloadthing.schemas import (
    DeleteFileResponse,
    ListFileResponse,
    UploadResult,
    UsageInfoResponse,
    UTApiOptions,
    UTtoken,
)
from upyloadthing.utils import snakify

SDK_VERSION = "7.4.4"
BE_ADAPTER = "server-sdk"
API_URL = "https://api.uploadthing.com"


class UTApi:
    """UploadThing API client for handling file uploads and management.

    This class provides methods to interact with the UploadThing service,
    including file uploads, deletions, listing, and usage information.

    Args:
        options (UTApiOptions | None): Configuration options for the API
        client.
            If not provided, will attempt to use environment variables.

    Raises:
        ValueError: If UPLOADTHING_TOKEN is not provided either through options
        or environment variables.
    """

    def __init__(self, options: UTApiOptions | None = None):
        self.options = options or UTApiOptions()
        b64_token = (
            options.token if options else os.getenv("UPLOADTHING_TOKEN")
        )
        if not b64_token:
            raise ValueError("UPLOADTHING_TOKEN is required")
        decoded_token = snakify(
            json.loads(base64.b64decode(b64_token).decode("utf-8"))
        )
        self.token = UTtoken.model_validate(decoded_token)
        self.region = (
            options.region
            if options and options.region
            else os.getenv("UPLOADTHING_REGION") or self.token.regions[0]
        )

        self.api_url = API_URL

    def _make_headers(self) -> dict:
        """Create headers required for API requests.

        Returns:
            dict: Dictionary containing the required headers for UploadThing
            API requests.
        """
        headers = {
            "x-uploadthing-version": SDK_VERSION,
            "x-uploadthing-be-adapter": BE_ADAPTER,
            "x-uploadthing-api-key": self.token.api_key,
        }
        return headers

    def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
    ) -> dict:
        """Make an HTTP request to the UploadThing API.

        Args:
            method (str): HTTP method to use (GET, POST, PUT, etc.)
            path (str): API endpoint path or full URL
            data (dict | None): Request data. Can contain regular JSON data or
            file objects.

        Returns:
            dict: JSON response from the API, converted to snake_case

        Raises:
            requests.exceptions.RequestException: If the HTTP request fails
        """
        if path.startswith("/"):
            url = f"{self.api_url}{path}"
        else:
            url = path

        headers = self._make_headers()

        # Helper function to check if value is a file-like object
        def is_file_like(obj):
            return hasattr(obj, "read") and callable(obj.read)

        # Check if data contains any file-like objects
        has_files = False
        if isinstance(data, dict):
            has_files = any(
                isinstance(v, tuple) and len(v) >= 2 and is_file_like(v[1])
                for v in data.values()
            )

        # Make the request based on the content type
        if data is None:
            response = requests.request(
                method=method, url=url, headers=headers
            )
        elif has_files:
            response = requests.request(
                method=method, url=url, headers=headers, files=data
            )
        else:
            response = requests.request(
                method=method, url=url, headers=headers, json=data
            )

        response.raise_for_status()
        return snakify(response.json())

    def upload_files(
        self,
        files: BinaryIO | List[BinaryIO],
        content_disposition: str = "inline",
        acl: str | None = "public-read",
    ) -> UploadResult | List[UploadResult]:
        """Upload one or more files to UploadThing.

        Args:
            files (BinaryIO | List[BinaryIO]): Single file or list of files to
            upload
            content_disposition (str, optional): Content-Disposition header
            value.
            acl (str | None, optional): Access control level for uploaded
            files.

        Returns:
            UploadResult | List[UploadResult]: Upload result(s) containing file
            information.
            Returns single UploadResult if one file was uploaded, or a list for
            multiple files.
        """
        if not isinstance(files, list):
            files = [files]

        files_data = []
        for file in files:
            file_seed = uuid.uuid4().hex
            file_key = generate_key(file_seed, self.token.app_id)
            file_name = getattr(file, "name", f"upload_{uuid.uuid4()}")
            file_size = file.seek(0, 2)
            file.seek(0)
            file_type = (
                mimetypes.guess_type(file_name)[0]
                or "application/octet-stream"
            )
            ingest_url = make_presigned_url(
                self.region,
                file_key,
                self.token.api_key,
                self.token.app_id,
                file_name,
                file_size,
                file_type,
                file_seed,
                content_disposition,
                acl,
            )
            file_data = {
                "file_key": file_key,
                "name": file_name,
                "size": file_size,
                "type": file_type,
                "custom_id": file_seed,
                "file": file,
                "ingest_url": ingest_url,
            }
            files_data.append(file_data)

        results = []
        for file_data in files_data:
            print(f"Uploading {file_data}...")
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
            results.append(UploadResult(**result))

        return results[0] if len(results) == 1 else results

    def delete_files(
        self, keys: str | List[str], key_type: str | None = "file_key"
    ) -> DeleteFileResponse:
        """Delete one or more files from UploadThing.

        Args:
            keys (str | List[str]): Single key or list of keys identifying
            files to delete
            key_type (str | None, optional): Type of key provided ('file_key'
            or 'custom_id').
        Returns:
            DeleteFileResponse: Response containing information about the
            deletion operation
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
        """List files stored in UploadThing.

        Args:
            limit (int | None, optional): Maximum number of files to return.
            offset (int | None, optional): Number of files to skip.

        Returns:
            ListFileResponse: Response containing list of files and pagination
            information
        """
        params = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        response = self._request("POST", "/v6/listFiles", params)
        return ListFileResponse(**response)

    def get_usage_info(self) -> UsageInfoResponse:
        """Get usage information for the UploadThing account.

        Returns:
            UsageInfoResponse: Response containing usage statistics and limits
        """
        result = self._request("POST", "/v6/getUsageInfo")
        return UsageInfoResponse(**result)
