#!/bin/bash
# run the container with environment secrets.
set -euo pipefail

require_env() {
  local name="$1"; shift || true
  local hint="${*:-}"
  if [[ -z "${!name:-}" ]]; then
    echo "Error: environment variable $name is not set." >&2
    if [[ -n "$hint" ]]; then
      echo "       $hint" >&2
    fi
    exit 1
  fi
}

# Optional suffix for container name; default to _0
if [ -n "${1:-}" ]; then
  CONTAINER_SUFFIX="_$1"
else
  CONTAINER_SUFFIX="_0"
fi
PROJECT=scjson
IMAGE_NAME=iraa/${PROJECT}:latest
CONTAINER_NAME="${PROJECT}${CONTAINER_SUFFIX}"

# Validate required environment
require_env AWS_REGION        "e.g., us-east-1"

docker run -d \
  -e AWS_REGION="${AWS_REGION}" \
  -e PYTHON_PATH="/home/softoboros/py" \
  -v codex_state:/.codex \
  --name "$CONTAINER_NAME" \
  ${IMAGE_NAME} tail -f /dev/null
# Get a copy of .ssh files from outside repo and populate them on the container once 
# running.  Create these and put them in ../ssh from the repo root
docker cp ~/ssh/known_hosts      "$CONTAINER_NAME":home/softoboros/.ssh/known_hosts
docker cp ~/ssh/id_rsa           "$CONTAINER_NAME":home/softoboros/.ssh/id_rsa
docker cp ~/ssh/id_rsa.pub       "$CONTAINER_NAME":home/softoboros/.ssh/id_rsa.pub
docker cp ~/ssh/config_container "$CONTAINER_NAME":home/softoboros/.ssh/config
docker cp ~/.codex/config.toml   "$CONTAINER_NAME":home/softoboros/.codex/config.toml
# Make sure backend user has access to it's creentials.s
docker exec -u 0 "$CONTAINER_NAME" chown -R "softoboros":"softoboros" \
                                /home/softoboros/.ssh/known_hosts \
                                /home/softoboros/.ssh/id_rsa \
                                /home/softoboros/.ssh/id_rsa.pub \
                                /home/softoboros/.ssh/config \
                                /home/softoboros/.codex/config.toml
#docker exec "$CONTAINER_NAME" git pull --set-upstream origin main
docker exec "$CONTAINER_NAME" pip install -r py/requirements.txt
docker exec -w /home/softoboros/${PROJECT}/js "$CONTAINER_NAME" npm ci
