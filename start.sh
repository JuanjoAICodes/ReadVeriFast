#!/usr/bin/env bash
# Exit on error
set -o errexit

# Start all services with Honcho
honcho -f Procfile.production start