# Upyloadthing

[![Build Status](https://github.com/farmisen/upyloadthing/workflows/CI/badge.svg)](https://github.com/farmisen/upyloadthing/actions)
[![PyPI version](https://badge.fury.io/py/upyloadthing.svg)](https://badge.fury.io/py/upyloadthing)
[![Python Versions](https://img.shields.io/pypi/pyversions/upyloadthing.svg)](https://pypi.org/project/upyloadthing/)

Python client for the [uploadthing](https://docs.uploadthing.com/api-reference/openapi-spec) API - The easiest way to add file uploads to your Python application.

## Installation

```bash
pip install upyloadthing
```

## Quick Start

```python
from upyloadthing import UTApi, UTApiOptions

# Initialize with token
api = UTApi(UTApiOptions(token="your-token"))

# Upload a file
with open("example.png", "rb") as f:
    result = api.upload_files(f)
    print(f"File uploaded: {result.url}")
```

## Environment Variables

The SDK can be configured using environment variables:

- `UPLOADTHING_TOKEN` - Your uploadthing API token (required if not passed to UTApiOptions)
- `UPLOADTHING_REGION` - Preferred upload region (optional, defaults to first available region found in the decoded token)

## Examples

### Upload Multiple Files

```python
files = [
    open("image1.jpg", "rb"),
    open("image2.jpg", "rb")
]
results = api.upload_files(files)
for result in results:
    print(f"Uploaded: {result.url}")
```

### Delete Files

```python
# Delete by file key
response = api.delete_files("file_key_123")

# Delete multiple files
response = api.delete_files(["key1", "key2"])

# Delete by custom ID
response = api.delete_files("custom_123", key_type="custom_id")
```

### Rename Files

```python
# Rename files using new names
response = api.rename_files([
    {"fileKey": "file_key_123", "newName": "new_name.jpg"},
    {"fileKey": "file_key_456", "newName": "other_name.png"}
])

# Update files with custom IDs
response = api.rename_files([
    {"customId": "custom_123", "newName": "new_name.jpg"},
    {"customId": "custom_456", "newName": "other_name.png"}
])

# Mix of new names and custom IDs
response = api.rename_files([
    {"fileKey": "file_key_123", "newName": "new_name.jpg"},
    {"customId": "custom_456", "newName": "other_name.png"}
])
```

### List Files

```python
# Get first 10 files
files = api.list_files(limit=10)
for file in files.files:
    print(f"{file.name}: {file.url}")

# Pagination
files = api.list_files(limit=10, offset=10)
```

### Check Usage

```python
usage = api.get_usage_info()
print(f"Total storage used: {usage.total_bytes / 1024 / 1024:.2f} MB")
print(f"Files uploaded: {usage.files_uploaded}")
```

## Error Handling

The SDK uses standard Python exceptions:

```python
from requests.exceptions import HTTPError

try:
    api.upload_files(file)
except HTTPError as e:
    if e.response.status_code == 413:
        print("File too large")
    else:
        print(f"Upload failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## API Reference

### Client Classes

Both clients provide the same methods with identical parameters, but different execution patterns:

#### UTApi (Synchronous)
```python
from upyloadthing import UTApi

api = UTApi(UTApiOptions(token="your-token"))
result = api.upload_files(file)
```

#### AsyncUTApi (Asynchronous)
```python
from upyloadthing import AsyncUTApi

api = AsyncUTApi(UTApiOptions(token="your-token"))
result = await api.upload_files(file)
```

### Methods

Both clients provide these methods:

- `upload_files(files: BinaryIO | List[BinaryIO], content_disposition: str = "inline", acl: str | None = "public-read") -> List[UploadResult]`
  - Upload one or more files
  - Returns list of upload results

- `delete_files(keys: str | List[str], key_type: str = "file_key") -> DeleteFileResponse`
  - Delete one or more files by key or custom ID
  - Returns deletion result

- `list_files(limit: int | None = None, offset: int | None = None) -> ListFileResponse`
  - List uploaded files with optional pagination
  - Returns file listing

- `rename_files(updates: List[dict[str, str]]) -> RenameFilesResponse`  
  - Rename files or update their custom IDs  
  - Updates list should contain dicts with:  
    - Either `fileKey` or `customId` (one is required)  
    - `newName` (required)  
  - Returns rename operation result  

- `get_usage_info() -> UsageInfoResponse`
  - Get account usage statistics
  - Returns usage information

### Response Models

All response models are defined in `upyloadthing/schemas.py`:

- `UploadResult` - File upload result containing:
  - `file_key: str`
  - `name: str`
  - `size: int`
  - `type: str`
  - `url: str`
  - `ufs_url: str`
  - `app_url: str`
  - `file_hash: str`
  - `server_data: Dict | None`
- `DeleteFileResponse` - File deletion result containing:
  - `success: bool`
  - `deleted_count: int`
- `ListFileResponse` - File listing result containing:
  - `has_more: bool`
  - `files: List[FileData]`
- `RenameFilesResponse` - File rename result containing:
  - `success: bool`
  - `renamed_count: int`
- `UsageInfoResponse` - Usage statistics containing:
  - `total_bytes: int`
  - `app_total_bytes: int`
  - `files_uploaded: int`
  - `limit_bytes: int`

## License

MIT
