#!/usr/bin/env bash
# Run Terraform for this project's current lane.
#
#   bash _root/_platform/_terraform/tf.sh plan
#   bash _root/_platform/_terraform/tf.sh apply
#
# Settings come from the environment first (deployed lanes, e.g. GitHub Actions),
# then from _root/_platform/_compose/.env (sandbox).
set -euo pipefail

TF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_HOME="$(cd "$TF_DIR/../../.." && pwd)"
ENV_FILE="$TF_DIR/../_compose/.env"

# Load only the keys we need from .env, without overriding what's already set.
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line; do
    key="${line%%=*}"
    if [[ -z "${!key:-}" ]]; then
      value="${line#*=}"
      value="${value%\"}"; value="${value#\"}"
      export "$key=$value"
    fi
  done < <(grep -E '^(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_REGION|ENVIRONMENT|S3_COPY_BUCKET|S3_COPY_PREFIX)=' "$ENV_FILE" || true)
fi

export ENVIRONMENT="${ENVIRONMENT:-sandbox}"
REGION="${AWS_REGION:?AWS_REGION is not set (in the environment or $ENV_FILE)}"
: "${S3_COPY_BUCKET:?S3_COPY_BUCKET is not set (in the environment or $ENV_FILE)}"

PREFIX="${S3_COPY_PREFIX:-}"
PREFIX="${PREFIX#/}"; PREFIX="${PREFIX%/}"
STATE_KEY="${PREFIX:+$PREFIX/}_root/_platform/_terraform/terraform.tfstate"

export TF_VAR_bucket_name="$S3_COPY_BUCKET"
export TF_VAR_project="$(basename "$PROJECT_HOME")"
export TF_VAR_environment="$ENVIRONMENT"
export TF_VAR_region="$REGION"
export TF_IN_AUTOMATION=1

# Use a local terraform if installed, otherwise the official image.
if command -v terraform >/dev/null 2>&1; then
  tf() { (cd "$TF_DIR" && terraform "$@"); }
else
  tf() {
    docker run --rm -i -u "$(id -u):$(id -g)" \
      -v "$TF_DIR:/work" -w /work -e HOME=/work/.terraform \
      -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e TF_IN_AUTOMATION \
      -e TF_VAR_bucket_name -e TF_VAR_project -e TF_VAR_environment -e TF_VAR_region \
      hashicorp/terraform:1.10.5 "$@"
  }
fi

echo "terraform: project=$TF_VAR_project environment=$ENVIRONMENT bucket=$S3_COPY_BUCKET state=$STATE_KEY" >&2

tf init -input=false -reconfigure \
  -backend-config="bucket=$S3_COPY_BUCKET" \
  -backend-config="key=$STATE_KEY" \
  -backend-config="region=$REGION" >&2

tf "$@"
