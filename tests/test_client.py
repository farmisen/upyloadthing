import base64
import json
import re
from io import BytesIO

import pytest
import requests

from upyloadthing.client import API_URL, UTApi
from upyloadthing.schemas import (
    DeleteFileResponse,
    ListFileResponse,
    UploadResult,
    UsageInfoResponse,
    UTApiOptions,
)

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
    """Fixture to create a UTApi instance with mock token."""
    options = UTApiOptions(token=MOCK_TOKEN)
    return UTApi(options)


@pytest.fixture
def mock_file():
    """Fixture to create a mock file."""
    file = BytesIO(b"test content")
    file.name = "test.jpg"
    return file


def test_init_with_options():
    """Test UTApi initialization with options."""
    options = UTApiOptions(token=MOCK_TOKEN, region="eu-west-1")
    api = UTApi(options)
    assert api.token.app_id == "test-app"
    assert api.token.api_key == "test-key"
    assert api.region == "eu-west-1"


def test_init_without_token():
    """Test UTApi initialization without token raises error."""
    with pytest.raises(ValueError, match="UPLOADTHING_TOKEN is required"):
        UTApi(UTApiOptions(token=None))


def test_make_headers(ut_api):
    """Test header generation."""
    headers = ut_api._make_headers()
    assert headers["x-uploadthing-api-key"] == "test-key"
    assert "x-uploadthing-version" in headers
    assert "x-uploadthing-be-adapter" in headers


def test_upload_files(responses, ut_api, mock_file):
    """Test file upload functionality."""
    # Mock the upload response
    upload_response = {
        "fileHash": "dae427dff5fa285fc87a791dc8b7daf1",
        "url": "https://utfs.io/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "ufsUrl": "https://lhdsot44oz.ufs.sh/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
        "appUrl": "https://utfs.io/a/lhdsot44oz/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg=",
    }

    # Mock any PUT request using responses
    responses.put(
        url=re.compile(r"https://sea2.ingest.uploadthing.com/"),
        json=upload_response,
        status=200,
    )

    result = ut_api.upload_files(mock_file)

    # Verify result is correct type
    assert isinstance(result, UploadResult)

    # Verify all fields
    assert result.file_key is not None  # Generated dynamically
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
    assert result.server_data is None  # Default value from schema


def test_upload_multiple_files(responses, ut_api):
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

    responses.put(
        url=re.compile(r"https://sea2.ingest.uploadthing.com/"),
        json=upload_response,
        status=200,
    )

    result = ut_api.upload_files(files)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(r, UploadResult) for r in result)
    for r in result:
        assert r.file_hash == "dae427dff5fa285fc87a791dc8b7daf1"
        assert (
            r.url
            == "https://utfs.io/f/AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg="
        )


def test_delete_files(responses, ut_api):
    """Test file deletion."""
    delete_response = {"success": True, "deleted_count": 1}

    responses.post(
        url=f"{API_URL}/v6/deleteFiles",
        json=delete_response,
        status=200,
    )

    result = ut_api.delete_files(
        "AlZ3KvVUSx6sMzg3ZDRmZmM5NTRhNDBkMmI5ZWQ5ODg2NWZmODc3MTg="
    )
    assert isinstance(result, DeleteFileResponse)
    assert result.success is True
    assert result.deleted_count == 1


def test_list_files(responses, ut_api):
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

    responses.post(
        url=f"{API_URL}/v6/listFiles",
        json=list_response,
        status=200,
    )

    result = ut_api.list_files(limit=10, offset=0)
    assert isinstance(result, ListFileResponse)
    assert len(result.files) == 1
    assert result.has_more is False
    assert result.files[0].id == "file_123"
    assert result.files[0].status == "ready"


def test_get_usage_info(responses, ut_api):
    """Test usage info retrieval."""
    usage_response = {
        "total_bytes": 1024,
        "app_total_bytes": 2048,
        "files_uploaded": 10,
        "limit_bytes": 5000000,
    }

    responses.post(
        url=f"{API_URL}/v6/getUsageInfo",
        json=usage_response,
        status=200,
    )

    result = ut_api.get_usage_info()
    assert isinstance(result, UsageInfoResponse)
    assert result.total_bytes == 1024
    assert result.app_total_bytes == 2048
    assert result.files_uploaded == 10
    assert result.limit_bytes == 5000000


def test_request_with_error(responses, ut_api):
    """Test handling of request errors."""
    responses.get(
        url=f"{API_URL}/test",
        json={"error": "Bad Request"},
        status=400,
    )

    with pytest.raises(requests.exceptions.HTTPError):
        ut_api._request("GET", "/test")


def test_request_with_different_content_types(responses, ut_api):
    """Test requests with different content types."""
    test_response = {"key": "value"}

    responses.post(
        url=f"{API_URL}/test-json",
        json=test_response,
        status=200,
        match=[
            responses.matchers.header_matcher(
                {"Content-Type": "application/json"}
            )
        ],
    )

    result = ut_api._request("POST", "/test-json", {"data": "test"})
    assert result == {"key": "value"}
