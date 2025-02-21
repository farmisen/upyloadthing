from enum import Enum
from typing import Dict, List

from pydantic import BaseModel


class ACLValue(Enum):
    PUBLIC_READ = "public-read"
    PRIVATE = "private"


class UTApiOptions(BaseModel):
    token: str | None = None
    region: str | None = None


class UTtoken(BaseModel):
    api_key: str
    app_id: str
    regions: List[str]


class FileData(BaseModel):
    id: str
    custom_id: str | None = None
    key: str
    name: str
    status: str
    size: int
    uploaded_at: int


class ListFileResponse(BaseModel):
    has_more: bool
    files: List[FileData]


class DeleteFileResponse(BaseModel):
    success: bool
    deleted_count: int


class RenameFilesResponse(BaseModel):
    success: bool
    renamed_count: int


class UsageInfoResponse(BaseModel):
    total_bytes: int
    app_total_bytes: int
    files_uploaded: int
    limit_bytes: int


class UpdateACLResponse(BaseModel):
    success: bool
    updated_count: int


class UploadResult(BaseModel):
    file_key: str
    name: str
    size: int
    type: str
    url: str
    ufs_url: str
    app_url: str
    file_hash: str
    server_data: Dict | None = None
    acl: ACLValue | None = None
