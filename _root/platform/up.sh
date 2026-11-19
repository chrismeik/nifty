#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

CMD="docker compose -f $SCRIPT_DIR/_compose/compose.yml --env-file $SCRIPT_DIR/_compose/.env"

# Autodiscover product-level overrides
while IFS= read -r override; do
  env_file="$(dirname "$override")/.env"
  if [[ -f "$env_file" ]]; then
    CMD="$CMD --env-file $env_file"
  fi
  CMD="$CMD -f $override"
done < <(find "$ROOT_DIR" -mindepth 5 -maxdepth 10 -name 'compose.override.yml' | sort)

if [[ "${VERATREE_ENV:-}" == "production" ]]; then
  while IFS= read -r override; do
    CMD="$CMD -f $override"
  done < <(find "$ROOT_DIR" -mindepth 5 -maxdepth 10 -name 'compose.prod.yml' | sort)

  PRODUCT_NGINX="$(find "$ROOT_DIR" -path '*/_platform/_nginx/nginx.prod.conf' ! -path '*/_root/*' | head -1)"
  if [[ -n "$PRODUCT_NGINX" ]]; then
    export NGINX_CONF="$PRODUCT_NGINX"
  fi
fi

exec $CMD "$@"
