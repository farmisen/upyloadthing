import base64
import json
from io import BytesIO

import httpx
import pytest
import respx

from upyloadthing import (
    AsyncUTApi,
    DeleteFileResponse,
    ListFileResponse,
    UploadResult,
    UsageInfoResponse,
    UTApiOptions,
)
from upyloadthing.base_client import API_URL

# Test data
MOCK_TOKEN = base64.b64encode(
    json.dumps(
        {
            "appId": "test-app",
            "apiKey": "test-key",
            "regions": ["sea2"],
        }
    ).encode()
).decode()


@pytest.fixture
def ut_api():
    """Fixture to create an AsyncUTApi instance with mock token."""
    options = UTApiOptions(token=MOCK_TOKEN)
    return AsyncUTApi(options)


@pytest.fixture
def mock_file():
    """Fixture to create a mock file."""
    file = BytesIO(b"test content")
    file.name = "test.jpg"
    return file


def test_init_with_options():
    """Test AsyncUTApi initialization with options."""
    options = UTApiOptions(token=MOCK_TOKEN, region="eu-west-1")
    api = AsyncUTApi(options)
    assert api.token.app_id == "test-app"
    assert api.token.api_key == "test-key"
    assert api.region == "eu-west-1"


def test_init_without_token():
    """Test AsyncUTApi initialization without token raises error."""
    with pytest.raises(ValueError, match="UPLOADTHING_TOKEN is required"):
        AsyncUTApi(UTApiOptions(token=None))


def test_make_headers(ut_api):
    """Test header generation."""
    headers = ut_api._make_headers()
    assert headers["x-uploadthing-api-key"] == "test-key"
    assert "x-uploadthing-version" in headers
    assert "x-uploadthing-be-adapter" in headers


@pytest.mark.asyncio
@respx.mock
async def test_upload_files(respx_mock: respx.MockRouter, ut_api, mock_file):
    """Test file upload functionality."""
    upload_response = {
        "fileHash": "dae427dff5fa285fc87a791dc8b7daf1",
        "url": "https://utfs.io/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "ufsUrl": "https://lhdsot44oz.ufs.sh/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "appUrl": "https://utfs.io/a/lhdsot44oz/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
    }

    respx_mock.put(url__regex="https://sea2.ingest.uploadthing.com/").mock(
        return_value=httpx.Response(200, json=upload_response)
    )

    result = (await ut_api.upload_files(mock_file))[0]
    assert result.file_key is not None
    assert result.name == "test.jpg"
    assert result.size == len(b"test content")
    assert result.type == "image/jpeg"
    assert result.file_hash == "dae427dff5fa285fc87a791dc8b7daf1"
    assert (
        result.url
        == "https://utfs.io/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg="
    )
    assert (
        result.ufs_url
        == "https://lhdsot44oz.ufs.sh/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg="
    )
    assert (
        result.app_url
        == "https://utfs.io/a/lhdsot44oz/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg="
    )
    assert result.server_data is None


@pytest.mark.asyncio
@respx.mock
async def test_upload_multiple_files(respx_mock: respx.MockRouter, ut_api):
    """Test uploading multiple files."""
    files = [BytesIO(b"test1 content"), BytesIO(b"test2 content")]
    for i, f in enumerate(files):
        f.name = f"test{i + 1}.jpg"

    upload_response = {
        "fileHash": "dae427dff5fa285fc87a791dc8b7daf1",
        "url": "https://utfs.io/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "ufsUrl": "https://lhdsot44oz.ufs.sh/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "appUrl": "https://utfs.io/a/lhdsot44oz/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
    }

    respx_mock.put(url__regex="https://sea2.ingest.uploadthing.com/").mock(
        return_value=httpx.Response(200, json=upload_response)
    )

    result = await ut_api.upload_files(files)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(r, UploadResult) for r in result)


@pytest.mark.asyncio
@respx.mock
async def test_upload_multiple_files_with_different_types(
    respx_mock: respx.MockRouter, ut_api
):
    """Test uploading multiple files with different types."""
    # Create test files of different types
    png_file = BytesIO(b"fake png content")
    png_file.name = "test.png"

    jpg_file = BytesIO(b"fake jpg content")
    jpg_file.name = "test.jpg"

    files = [png_file, jpg_file]

    upload_response = {
        "fileHash": "dae427dff5fa285fc87a791dc8b7daf1",
        "url": "https://utfs.io/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "ufsUrl": "https://lhdsot44oz.ufs.sh/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "appUrl": "https://utfs.io/a/lhdsot44oz/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
    }

    respx_mock.put(url__regex="https://sea2.ingest.uploadthing.com/").mock(
        return_value=httpx.Response(200, json=upload_response)
    )

    result = await ut_api.upload_files(files)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(r, UploadResult) for r in result)

    # Verify file specific details
    assert result[0].name == "test.png"
    assert result[0].type == "image/png"
    assert result[1].name == "test.jpg"
    assert result[1].type == "image/jpeg"


@pytest.mark.asyncio
@respx.mock
async def test_upload_multiple_files_with_custom_disposition(
    respx_mock: respx.MockRouter, ut_api
):
    """Test uploading multiple files with custom content disposition."""
    files = [BytesIO(b"test1 content"), BytesIO(b"test2 content")]
    for i, f in enumerate(files):
        f.name = f"test{i + 1}.txt"

    upload_response = {
        "fileHash": "dae427dff5fa285fc87a791dc8b7daf1",
        "url": "https://utfs.io/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "ufsUrl": "https://lhdsot44oz.ufs.sh/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "appUrl": "https://utfs.io/a/lhdsot44oz/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
    }

    respx_mock.put(url__regex="https://sea2.ingest.uploadthing.com/").mock(
        return_value=httpx.Response(200, json=upload_response)
    )

    result = await ut_api.upload_files(files, content_disposition="attachment")
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(r, UploadResult) for r in result)


@pytest.mark.asyncio
@respx.mock
async def test_delete_files(respx_mock: respx.MockRouter, ut_api):
    """Test file deletion."""
    delete_response = {"success": True, "deleted_count": 1}

    respx_mock.post(f"{API_URL}/v6/deleteFiles").mock(
        return_value=httpx.Response(200, json=delete_response)
    )

    result = await ut_api.delete_files(
        "AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg="
    )
    assert isinstance(result, DeleteFileResponse)
    assert result.success is True
    assert result.deleted_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_list_files(respx_mock: respx.MockRouter, ut_api):
    """Test file listing."""
    list_response = {
        "has_more": False,
        "files": [
            {
                "id": "file_123",
                "key": "AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",  # noqa: E501
                "name": "test.jpg",
                "status": "ready",
                "size": 1024,
                "uploaded_at": 1704067200,
            }
        ],
    }

    respx_mock.post(f"{API_URL}/v6/listFiles").mock(
        return_value=httpx.Response(200, json=list_response)
    )

    result = await ut_api.list_files(limit=10, offset=0)
    assert isinstance(result, ListFileResponse)
    assert len(result.files) == 1
    assert result.has_more is False
    assert result.files[0].id == "file_123"
    assert result.files[0].status == "ready"


@pytest.mark.asyncio
@respx.mock
async def test_get_usage_info(respx_mock: respx.MockRouter, ut_api):
    """Test usage info retrieval."""
    usage_response = {
        "total_bytes": 1024,
        "app_total_bytes": 2048,
        "files_uploaded": 10,
        "limit_bytes": 5000000,
    }

    respx_mock.post(f"{API_URL}/v6/getUsageInfo").mock(
        return_value=httpx.Response(200, json=usage_response)
    )

    result = await ut_api.get_usage_info()
    assert isinstance(result, UsageInfoResponse)
    assert result.total_bytes == 1024
    assert result.app_total_bytes == 2048
    assert result.files_uploaded == 10
    assert result.limit_bytes == 5000000


@pytest.mark.asyncio
@respx.mock
async def test_request_with_error(respx_mock: respx.MockRouter, ut_api):
    """Test handling of request errors."""
    respx_mock.get(f"{API_URL}/test").mock(
        return_value=httpx.Response(400, json={"error": "Bad Request"})
    )

    with pytest.raises(httpx.HTTPError):
        await ut_api._request("GET", "/test")


@pytest.mark.asyncio
@respx.mock
async def test_request_with_different_content_types(
    respx_mock: respx.MockRouter, ut_api
):
    """Test requests with different content types."""
    test_response = {"key": "value"}

    respx_mock.post(f"{API_URL}/test-json").mock(
        return_value=httpx.Response(200, json=test_response)
    )

    result = await ut_api._request("POST", "/test-json", {"data": "test"})
    assert result == {"key": "value"}
