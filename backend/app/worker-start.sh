#! /usr/bin/env bash
set -e

python /app/app/pre_start.py

celery -A app.worker worker -E -l INFO -c 4
