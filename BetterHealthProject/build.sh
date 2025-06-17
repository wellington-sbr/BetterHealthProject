#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies using Poetry
poetry install --no-interaction --no-root

# Run Django management commands with Poetry
poetry run python manage.py collectstatic --no-input
poetry run python manage.py migrate