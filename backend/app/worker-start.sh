#! /usr/bin/env bash
set -e

python /app/app/celeryworker_pre_start.py

celery -A app.worker worker -l info -c 4
