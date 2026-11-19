#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KEY="${VERATREE_SSH_KEY:-$HOME/.ssh/veratree-prod.pem}"
IP="${VERATREE_SERVER_IP}"

if [[ -z "$IP" ]]; then
  echo "Error: VERATREE_SERVER_IP is not set"
  exit 1
fi

rsync -avz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='node_modules' \
  -e "ssh -i \"$KEY\" -o StrictHostKeyChecking=no" \
  "$REPO_ROOT/" \
  ec2-user@${IP}:~/veratree/root/ 2>&1 | tail -10

ssh -i "$KEY" -o StrictHostKeyChecking=no ec2-user@${IP} \
  "cd ~/veratree/root && VERATREE_ENV=production bash _root/platform/up.sh up -d --build 2>&1 | tail -20 && bash _root/platform/up.sh exec nginx nginx -s reload"
