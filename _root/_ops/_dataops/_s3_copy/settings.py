from pydantic_settings import BaseSettings


class S3CopySettings(BaseSettings):
    S3_COPY_ENABLED: bool = False      # kill switch; off until a bucket is configured
    S3_COPY_BUCKET: str | None = None  # one bucket per project + lane, e.g. veratree-bot-sandbox
    S3_COPY_PREFIX: str = ""           # optional leading prefix; empty = keys mirror the tree

    @property
    def enabled(self) -> bool:
        return bool(self.S3_COPY_ENABLED and self.S3_COPY_BUCKET)

    @property
    def key_base(self) -> str:
        return self.S3_COPY_PREFIX.strip("/")
