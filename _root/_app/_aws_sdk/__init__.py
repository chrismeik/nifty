"""Shared AWS access for every product: `from _app._aws_sdk import s3`."""
from .client import get_client, get_session

__all__ = ["get_client", "get_session"]
