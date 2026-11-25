"""
Copy files products write to disk into S3.

Call it right after the write (inline; waits for the upload, re-raises on failure):

    from _root._ops._dataops._s3_copy import copy_to_s3

    df.to_parquet(path)
    copy_to_s3(path)

Keys mirror the product tree:
    s3://<S3_COPY_BUCKET>/[S3_COPY_PREFIX/]<path relative to the project home>

One bucket per project + lane (e.g. veratree-bot-sandbox). S3_COPY_PREFIX is an
optional leading prefix, empty by default. Nothing happens unless S3_COPY_ENABLED
and S3_COPY_BUCKET are set.
"""
from .copy import copy_to_s3

__all__ = ["copy_to_s3"]
