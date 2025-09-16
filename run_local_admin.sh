#!/bin/bash

# VeriFast Local Admin Runner
# ---------------------------
# This script starts the Django server and a Celery worker for local administration.
# It requires a .env.local file with production settings.

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "🔴 ERROR: .env.local file not found."
    echo "Please copy .env.local.example to .env.local and fill in your production credentials."
    exit 1
fi

echo "🚀 Starting VeriFast Local Admin Environment..."

# Export the local environment file
export $(grep -v '^#' .env.local | xargs)

# Start the Django development server on port 8000
echo "Starting Django server on http://localhost:8000"
python3 manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# Start the Celery worker
# It will listen on the default queue, plus the specific queues for the content motor.
echo "Starting Celery worker..."
celery -A config.celery worker --loglevel=info -Q default,database_ops,acquisition,maintenance,monitoring &
CELERY_PID=$!

echo "✅ Local admin environment is running."
echo "Django Server PID: $DJANGO_PID"
echo "Celery Worker PID: $CELERY_PID"
echo "Press Ctrl+C to stop both processes."

# Wait for either process to exit
wait -n $DJANGO_PID $CELERY_PID

# Cleanup function on exit
cleanup() {
    echo "\n🛑 Stopping services..."
    kill $DJANGO_PID
    kill $CELERY_PID
    echo "All services stopped."
}

# Trap Ctrl+C and call cleanup
trap cleanup INT

# Wait for all background jobs to finish
wait
