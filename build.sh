#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
export BLIS_ARCH="generic"
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate
