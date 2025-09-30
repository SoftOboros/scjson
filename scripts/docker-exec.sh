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
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:?Need CODEX_ACCESS_KEY_ID set}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:?Need AWS_SECRET_ACCESS_KEY set}" \
  -e DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY}" \
  -e DJANGO_DB_PASSW="${DJANGO_DB_PASSW}" \
  -e OPENAI_ORG_KEY="${OPENAI_ORG_KEY}" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e DJANGO_AWS_USER_ID="${DJANGO_AWS_USER_ID}" \
  -e DJANGO_AWS_ACCESS_KEY_ID="${DJANGO_AWS_ACCESS_KEY_ID}" \
  -e DJANGO_AWS_SECRET_ACCESS_KEY="${DJANGO_AWS_SECRET_ACCESS_KEY}" \
  -e DJANGO_EMAIL_HOST_PASSWORD="${DJANGO_EMAIL_HOST_PASSWORD}" \
  -e PYTHON_PATH="/home/softoboros/softoboros/backend" \
  "$CONTAINER_NAME" bash
