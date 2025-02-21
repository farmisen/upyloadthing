import base64
import json
import mimetypes
import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, Coroutine, List

import httpx

from upyloadthing.file_key import generate_key
from upyloadthing.presign import make_presigned_url
from upyloadthing.schemas import (
    ACLValue,
    DeleteFileResponse,
    ListFileResponse,
    RenameFilesResponse,
    UploadResult,
    UsageInfoResponse,
    UTApiOptions,
    UTtoken,
)
from upyloadthing.utils import snakify

SDK_VERSION = "7.4.4"
BE_ADAPTER = "server-sdk"
API_URL = "https://api.uploadthing.com"


class BaseUTApi(ABC):
    """Base class for UploadThing API client.

    This abstract class defines the interface for both synchronous and
    asynchronous clients.
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
        """Create headers required for UploadThing API requests.

        Returns:
            dict: Headers containing SDK version, adapter type, and API key
        """
        return {
            "x-uploadthing-version": SDK_VERSION,
            "x-uploadthing-be-adapter": BE_ADAPTER,
            "x-uploadthing-api-key": self.token.api_key,
        }

    @abstractmethod
    def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
    ) -> dict | Coroutine[Any, Any, dict]:
        """Make an HTTP request to the UploadThing API.

        Args:
            method: HTTP method to use
            path: API endpoint path
            data: Request data/parameters

        Returns:
            Response data as dictionary or coroutine
        """
        pass

    @abstractmethod
    def upload_files(
        self,
        files: BinaryIO | List[BinaryIO],
        content_disposition: str = "inline",
        acl: str | None = "public-read",
    ) -> List[UploadResult] | Coroutine[Any, Any, List[UploadResult]]:
        """Upload one or more files to UploadThing.

        Args:
            files: Single file or list of files to upload
            content_disposition: Content disposition header value
            acl: Access control list setting for uploaded files

        Returns:
            List of upload results or coroutine
        """
        pass

    @abstractmethod
    def delete_files(
        self, keys: str | List[str], key_type: str | None = "file_key"
    ) -> DeleteFileResponse | Coroutine[Any, Any, DeleteFileResponse]:
        """Delete one or more files from UploadThing.

        Args:
            keys: Single key or list of keys identifying files to delete
            key_type: Type of key provided ('file_key' or 'custom_id')

        Returns:
            Delete operation response or coroutine
        """
        pass

    @abstractmethod
    def list_files(
        self, limit: int | None = None, offset: int | None = None
    ) -> ListFileResponse | Coroutine[Any, Any, ListFileResponse]:
        """List files stored in UploadThing.

        Args:
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            File listing response or coroutine
        """
        pass

    @abstractmethod
    def get_usage_info(
        self,
    ) -> UsageInfoResponse | Coroutine[Any, Any, UsageInfoResponse]:
        """Get usage information for the UploadThing account.

        Returns:
            Usage information response or coroutine
        """
        pass

    @abstractmethod
    def rename_files(
        self, updates: List[dict[str, str]]
    ) -> RenameFilesResponse | Coroutine[Any, Any, RenameFilesResponse]:
        """Rename one or more files.

        Args:
            updates: List of update objects containing either:
                    - fileKey and newName
                    - customId and newName

        Returns:
            Rename operation response or coroutine
        """
        pass

    def _prepare_file_data(
        self, file: BinaryIO, content_disposition: str, acl: str | None
    ) -> dict:
        """Prepare file metadata and presigned URL for upload.

        Args:
            file: File-like object to upload
            content_disposition: Content disposition header value
            acl: Access control list setting

        Returns:
            dict: Prepared file data including presigned URL
        """
        file_seed = uuid.uuid4().hex
        file_key = generate_key(file_seed, self.token.app_id)
        file_name = getattr(file, "name", f"upload_{uuid.uuid4()}")
        file_size = file.seek(0, 2)
        file.seek(0)
        file_type = (
            mimetypes.guess_type(file_name)[0] or "application/octet-stream"
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

        return {
            "file_key": file_key,
            "name": file_name,
            "size": file_size,
            "type": file_type,
            "custom_id": file_seed,
            "file": file,
            "ingest_url": ingest_url,
        }

    def _prepare_request(
        self, method: str, path: str, data: dict | None = None
    ) -> tuple[str, dict, dict | None]:
        """Prepare common request parameters.

        Args:
            method: HTTP method to use
            path: API endpoint path
            data: Request data/parameters

        Returns:
            tuple: (url, headers, prepared_data)
        """
        if path.startswith("/"):
            url = f"{self.api_url}{path}"
        else:
            url = path

        headers = self._make_headers()

        def is_file_like(obj):
            return hasattr(obj, "read") and callable(obj.read)

        if isinstance(data, dict):
            has_files = any(
                isinstance(v, tuple) and len(v) >= 2 and is_file_like(v[1])
                for v in data.values()
            )
            if has_files:
                return url, headers, {"files": data}
            return url, headers, {"json": data}

        return url, headers, None

    def _handle_error_response(self, e: httpx.HTTPStatusError) -> None:
        """Handle HTTP error responses consistently.

        Args:
            e: The HTTP error exception

        Raises:
            httpx.HTTPStatusError: Enhanced error with more details
        """
        error_msg = f"UploadThing API error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            if "error" in error_data:
                error_msg += f" - {error_data['error']}"
        except Exception:
            pass
        raise httpx.HTTPStatusError(
            error_msg, request=e.request, response=e.response
        ) from e

    def _validate_acl_updates(self, updates: List[dict[str, str]]) -> None:
        """Validate ACL update requests.

        Args:
            updates: List of update objects containing ACL changes

        Raises:
            ValueError: If any ACL value is invalid or required fields
            are missing
        """
        for update in updates:
            # Check for required identifier
            if not any(key in update for key in ["fileKey", "customId"]):
                raise ValueError(
                    "Each update must contain either 'fileKey' or 'customId'"
                )

            # Check for ACL value
            if "acl" not in update:
                raise ValueError("Missing 'acl' in update")
            try:
                ACLValue(update["acl"])  # Validate enum value
            except ValueError as e:
                raise ValueError(
                    f"ACL must be one of: {', '.join(f"'{v.value}'" for v in ACLValue)}"  # noqa: E501
                ) from e
