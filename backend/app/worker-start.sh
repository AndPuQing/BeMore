#! /usr/bin/env bash
set -e

python /app/app/pre_start.py

celery -A app.worker worker -l info -c 4
