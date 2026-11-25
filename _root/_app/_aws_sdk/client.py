from __future__ import annotations

from functools import lru_cache

import boto3

from .settings import AwsSettings


@lru_cache(maxsize=1)
def get_session() -> boto3.session.Session:
    # Settings are read on first use, not at import, so bootstrap's .env loading applies.
    s = AwsSettings()
    return boto3.session.Session(profile_name=s.AWS_PROFILE, region_name=s.AWS_REGION)


@lru_cache(maxsize=None)
def get_client(service: str):
    """Cached low-level client. boto3 clients are thread-safe, so worker threads can share one."""
    return get_session().client(service, endpoint_url=AwsSettings().AWS_ENDPOINT_URL)
