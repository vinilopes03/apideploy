from typing import Any, Dict, List
from pydantic import BaseModel, HttpUrl

import os
from functools import lru_cache
from dataclasses import dataclass


class Artifact(BaseModel):
    artifact_id: str
    filename: str
    size_bytes: int
    content_type: str
    download_url: HttpUrl
    expires_at: str


class AnalyzeRequest(BaseModel):
    asset_id: str
    callback_url: HttpUrl
    callback_token: str
    asset_metadata: Dict[str, Any] = {}
    artifact_manifest: Dict[str, List[Artifact]] = {}


@dataclass(frozen=True)
class Settings:
    analyzer_name: str
    analyzer_version: str
    redis_url: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    name = os.environ.get("ANALYZER_NAME")
    version = os.environ.get("ANALYZER_VERSION")
    redis_url = os.environ.get("REDIS_URL")
    if not name:
        raise RuntimeError("ANALYZER_NAME  env var not set")
    if not version:
        raise RuntimeError("ANALYZER_VERSION env var not set")
    if not redis_url:
        raise RuntimeError("REDIS_URL env var not set")

    return Settings(analyzer_name=name, analyzer_version=version, redis_url=redis_url)


SETTINGS = get_settings()
