"""Thin S3 helpers. Keys are plain strings; callers decide the layout."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .client import get_client


@dataclass(frozen=True)
class S3Object:
    key: str
    size: int
    last_modified: datetime


def list_objects(bucket: str, prefix: str) -> dict[str, S3Object]:
    """Every object under prefix, keyed by object key."""
    out: dict[str, S3Object] = {}
    paginator = get_client("s3").get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for o in page.get("Contents", []):
            out[o["Key"]] = S3Object(o["Key"], o["Size"], o["LastModified"])
    return out


def upload_file(local: Path, bucket: str, key: str) -> None:
    get_client("s3").upload_file(str(local), bucket, key)

