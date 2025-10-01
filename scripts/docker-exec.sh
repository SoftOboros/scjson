#!/bin/bash
# run the container with environment secrets.
set -eauv

# Optional suffix for container name; default to _0
if [ -n "$1" ]; then
  CONTAINER_SUFFIX="_$1"
else
  CONTAINER_SUFFIX="_0"
fi
CONTAINER_NAME="scjson${CONTAINER_SUFFIX}"

docker exec $CONTAINER_NAME git config user.name \"$GIT_USERNAME\"
docker exec $CONTAINER_NAME git config user.email $GIT_EMAIL

docker exec \
  -it \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:?Need AWS_ACCESS_KEY_ID set}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:?Need AWS_SECRET_ACCESS_KEY set}" \
  "$CONTAINER_NAME" bash
