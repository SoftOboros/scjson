#!/usr/bin/env bash
python -m scjson typescript -o ../js
python -m scjson schema -o ..
python -m scjson schema -o ../js
python -m scjson schema -o ../java/src/main/resources