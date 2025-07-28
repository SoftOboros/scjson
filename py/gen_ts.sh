#!/usr/bin/env bash
#
#  Update typescrupt and schema from pydantic models.
#
python -m scjson typescript -o ../js/src
python -m scjson schema -o ..
python -m scjson schema -o ../js
python -m scjson schema -o ../java/src/main/resources
