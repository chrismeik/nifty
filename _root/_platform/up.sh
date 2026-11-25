#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# ENVIRONMENT names the deployment lane. Any run that doesn't set it is a local
# "sandbox" run; other lanes (e.g. prod) are set by the deploy that calls this script.
export ENVIRONMENT="${ENVIRONMENT:-sandbox}"

CMD="docker compose -f $SCRIPT_DIR/_compose/compose.yml --env-file $SCRIPT_DIR/_compose/.env"

# Autodiscover product-level overrides
while IFS= read -r override; do
  env_file="$(dirname "$override")/.env"
  if [[ -f "$env_file" ]]; then
    CMD="$CMD --env-file $env_file"
  fi
  CMD="$CMD -f $override"
done < <(find "$ROOT_DIR" -mindepth 5 -maxdepth 10 -name 'compose.override.yml' | sort)

# Per-environment overrides: compose.<ENVIRONMENT>.yml and nginx.<ENVIRONMENT>.conf
while IFS= read -r override; do
  CMD="$CMD -f $override"
done < <(find "$ROOT_DIR" -mindepth 5 -maxdepth 10 -name "compose.${ENVIRONMENT}.yml" | sort)

PRODUCT_NGINX="$(find "$ROOT_DIR" -path "*/_platform/_nginx/nginx.${ENVIRONMENT}.conf" ! -path '*/_root/*' | head -1)"
if [[ -n "$PRODUCT_NGINX" ]]; then
  export NGINX_CONF="$PRODUCT_NGINX"
fi

exec $CMD "$@"
