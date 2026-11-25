from pydantic_settings import BaseSettings


class AwsSettings(BaseSettings):
    # Credentials come from boto3's default chain (env vars, ~/.aws, instance role).
    AWS_REGION: str  # required: set in .env (e.g. us-east-1)
    AWS_PROFILE: str | None = None
    AWS_ENDPOINT_URL: str | None = None  # e.g. a MinIO/LocalStack URL in dev
