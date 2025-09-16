#!/bin/bash

# VeriFast Local Runner using Honcho
# ----------------------------------
# This script starts all services (web, worker, redis) for local administration
# using Honcho and the Procfile.local file.

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "🔴 ERROR: .env.local file not found."
    echo "Please copy .env.local.example to .env.local and fill in your credentials."
    exit 1
fi

# Check if honcho is installed
if ! command -v honcho &> /dev/null
then
    echo "🔴 ERROR: honcho is not installed."
    echo "Please install it by running: pip install honcho"
    exit 1
fi

echo "🚀 Starting VeriFast Local Admin Environment with Honcho..."

# Start all services using Honcho
# The -e flag loads the environment variables from .env.local
# The -f flag specifies the Procfile to use
honcho -e .env.local -f Procfile.local start
