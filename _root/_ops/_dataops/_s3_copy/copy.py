"""Copy files to S3 right after they're written. Never deletes from S3."""
from __future__ import annotations

import logging
from pathlib import Path

from _app._aws_sdk import s3

from .settings import S3CopySettings

log = logging.getLogger(__name__)

ROOT_DIR = Path("/root-product")  # the project home inside the containers

_SKIP_SUFFIXES = {".tmp", ".pyc"}


def copy_to_s3(path: str | Path, root: Path = ROOT_DIR) -> int:
    """Upload a file (or every new/changed file in a folder) right after writing it.

        df.to_parquet(path)
        copy_to_s3(path)

    The S3 key mirrors the file's place in the project tree. Runs inline: the
    caller waits for the upload, and a failure is logged and re-raised.
    Does nothing (returns 0) unless S3_COPY_ENABLED and S3_COPY_BUCKET are set.
    Returns the number of files uploaded.
    """
    cfg = S3CopySettings()
    if not cfg.enabled:
        log.debug("s3_copy: copy of %s skipped (S3_COPY_ENABLED/S3_COPY_BUCKET not set)", path)
        return 0

    p = Path(path)
    if p.is_dir():
        return _copy_folder(p, cfg, root)
    if not p.is_file():
        raise FileNotFoundError(f"s3_copy: {p} does not exist")

    _upload(p, s3_key(p, cfg.key_base, root), cfg)
    return 1


def s3_key(local: Path, key_base: str, root: Path = ROOT_DIR) -> str:
    """[key_base/]<path relative to the project home>. The key mirrors the product tree."""
    try:
        rel = Path(local).absolute().relative_to(root).as_posix()
    except ValueError:
        raise ValueError(f"s3_copy: {local} is outside the project home {root}") from None
    return f"{key_base}/{rel}" if key_base else rel


def _copy_folder(folder: Path, cfg: S3CopySettings, root: Path) -> int:
    """Upload files in folder that are missing from S3 or whose size differs."""
    remote = s3.list_objects(cfg.S3_COPY_BUCKET, s3_key(folder, cfg.key_base, root) + "/")
    uploaded = 0
    for f in sorted(folder.rglob("*")):
        if not f.is_file() or f.suffix in _SKIP_SUFFIXES:
            continue
        key = s3_key(f, cfg.key_base, root)
        existing = remote.get(key)
        if existing and existing.size == f.stat().st_size:
            continue
        _upload(f, key, cfg)
        uploaded += 1
    return uploaded


def _upload(local: Path, key: str, cfg: S3CopySettings) -> None:
    try:
        s3.upload_file(local, cfg.S3_COPY_BUCKET, key)
    except Exception:
        log.exception("s3_copy: upload failed %s -> s3://%s/%s", local, cfg.S3_COPY_BUCKET, key)
        raise
    log.info("s3_copy: uploaded %s -> s3://%s/%s", local, cfg.S3_COPY_BUCKET, key)
