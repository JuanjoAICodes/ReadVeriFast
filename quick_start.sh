#!/bin/bash

# VeriFast Content Motor - Quick Start Script
# This script provides the fastest way to get your content processing system running

set -e  # Exit on any error

# Handle stop command
if [[ "$1" == "stop" ]]; then
    echo "🛑 Stopping VeriFast Content Motor..."
    echo "===================================="
    
    # Stop Django
    if [[ -f django.pid ]]; then
        PID=$(cat django.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            echo "✅ Django stopped (PID: $PID)"
        else
            echo "⚠️  Django process not running"
        fi
        rm -f django.pid
    else
        echo "⚠️  Django PID file not found"
    fi
    
    # Stop Celery
    if [[ -f celery.pid ]]; then
        PID=$(cat celery.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            echo "✅ Celery stopped (PID: $PID)"
        else
            echo "⚠️  Celery process not running"
        fi
        rm -f celery.pid
    else
        echo "⚠️  Celery PID file not found"
    fi
    
    echo ""
    echo "✅ Content motor stopped"
    echo "Redis is still running (if it was started as a service)"
    exit 0
fi

# Handle status command
if [[ "$1" == "status" ]]; then
    echo "📊 VeriFast Content Motor Status"
    echo "================================"
    
    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis: Running"
    else
        echo "❌ Redis: Not running"
    fi
    
    # Check Django
    if [[ -f django.pid ]] && kill -0 $(cat django.pid) 2>/dev/null; then
        echo "✅ Django: Running (PID: $(cat django.pid))"
    elif curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo "✅ Django: Running on port 8000"
    else
        echo "❌ Django: Not running"
    fi
    
    # Check Celery
    if [[ -f celery.pid ]] && kill -0 $(cat celery.pid) 2>/dev/null; then
        echo "✅ Celery: Running (PID: $(cat celery.pid))"
    else
        echo "❌ Celery: Not running"
    fi
    
    exit 0
fi

echo "🚀 VeriFast Content Motor - Quick Start"
echo "======================================"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected."
    echo "   Consider running: source .venv/bin/activate"
    echo ""
fi

# Check if Redis is running
echo "🔍 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "🚀 Starting Redis..."
    if command -v redis-server > /dev/null 2>&1; then
        redis-server --daemonize yes
        sleep 2
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis started successfully"
        else
            echo "❌ Failed to start Redis"
            exit 1
        fi
    else
        echo "❌ Redis not found. Please install Redis first:"
        echo "   Ubuntu/Debian: sudo apt install redis-server"
        echo "   macOS: brew install redis"
        exit 1
    fi
fi

# Check Django configuration
echo "🔍 Checking Django configuration..."
if python manage.py check > /dev/null 2>&1; then
    echo "✅ Django configuration is valid"
else
    echo "❌ Django configuration has issues. Run: python manage.py check"
    exit 1
fi

# Apply migrations if needed
echo "🔍 Checking database migrations..."
python manage.py migrate --check > /dev/null 2>&1 || {
    echo "🔄 Applying database migrations..."
    python manage.py migrate
}

echo ""
echo "🎯 Choose how to start the content motor:"
echo ""
echo "1) Development Mode (manual - multiple terminals needed)"
echo "2) Production Mode (honcho - single terminal)"
echo "3) Background Mode (daemonized processes)"
echo "4) Just show me the commands"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🔧 DEVELOPMENT MODE INSTRUCTIONS"
        echo "================================"
        echo ""
        echo "Open these commands in separate terminals:"
        echo ""
        echo "Terminal 1 - Django Server:"
        echo "  python manage.py runserver"
        echo ""
        echo "Terminal 2 - Celery Worker:"
        echo "  celery -A config.celery worker --loglevel=INFO"
        echo ""
        echo "Terminal 3 - Celery Flower (optional monitoring):"
        echo "  celery -A config.celery flower"
        echo ""
        echo "Then visit:"
        echo "  - Application: http://localhost:8000"
        echo "  - Admin: http://localhost:8000/admin"
        echo "  - Flower (if running): http://localhost:5555"
        ;;
    
    2)
        echo ""
        echo "🚀 Starting Production Mode with Honcho..."
        if command -v honcho > /dev/null 2>&1; then
            echo "✅ Honcho found, starting services..."
            echo ""
            echo "Press Ctrl+C to stop all services"
            echo ""
            honcho start
        else
            echo "❌ Honcho not found. Install with:"
            echo "   uv pip install honcho"
            echo ""
            echo "Or run manually:"
            echo "   python manage.py runserver &"
            echo "   celery -A config.celery worker --loglevel=INFO &"
        fi
        ;;
    
    3)
        echo ""
        echo "🌙 Starting Background Mode..."
        
        # Start Django with gunicorn
        if command -v gunicorn > /dev/null 2>&1; then
            echo "🚀 Starting Django with Gunicorn..."
            gunicorn config.wsgi:application \
                --bind 0.0.0.0:8000 \
                --workers 3 \
                --daemon \
                --pid django.pid \
                --access-logfile django_access.log \
                --error-logfile django_error.log
            echo "✅ Django started (PID: $(cat django.pid))"
        else
            echo "⚠️  Gunicorn not found, using Django dev server..."
            nohup python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &
            echo $! > django.pid
            echo "✅ Django started (PID: $(cat django.pid))"
        fi
        
        # Start Celery worker
        echo "🚀 Starting Celery worker..."
        celery -A config.celery worker \
            --loglevel=INFO \
            --detach \
            --pidfile=celery.pid \
            --logfile=celery.log
        echo "✅ Celery started (PID: $(cat celery.pid))"
        
        echo ""
        echo "✅ Content motor started in background!"
        echo ""
        echo "Services running:"
        echo "  - Django: http://localhost:8000 (PID: $(cat django.pid))"
        echo "  - Celery: Background processing (PID: $(cat celery.pid))"
        echo "  - Redis: Message broker"
        echo ""
        echo "To stop services:"
        echo "  ./quick_start.sh stop"
        echo ""
        echo "To monitor logs:"
        echo "  tail -f django_access.log"
        echo "  tail -f celery.log"
        ;;
    
    4)
        echo ""
        echo "📋 MANUAL COMMANDS"
        echo "=================="
        echo ""
        echo "Start Redis (if not running):"
        echo "  redis-server --daemonize yes"
        echo ""
        echo "Start Django:"
        echo "  python manage.py runserver"
        echo ""
        echo "Start Celery Worker:"
        echo "  celery -A config.celery worker --loglevel=INFO"
        echo ""
        echo "Start Celery Flower (monitoring):"
        echo "  celery -A config.celery flower"
        echo ""
        echo "Test content processing:"
        echo "  python manage.py shell"
        echo "  >>> from verifast_app.tasks import debug_task"
        echo "  >>> debug_task.delay()"
        echo ""
        echo "Process an article:"
        echo "  >>> from verifast_app.tasks import scrape_and_save_article"
        echo "  >>> scrape_and_save_article.delay('https://example.com/article')"
        ;;
    
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

# If we get here and it's background mode, show additional info
if [[ $choice == "3" ]]; then
    echo ""
    echo "🧪 Testing the setup..."
    sleep 3
    
    # Test if Django is responding
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo "✅ Django is responding on http://localhost:8000"
    else
        echo "⚠️  Django might still be starting up. Check django_access.log"
    fi
    
    # Test if Celery is running
    if kill -0 $(cat celery.pid 2>/dev/null) 2>/dev/null; then
        echo "✅ Celery worker is running"
    else
        echo "⚠️  Celery worker might have issues. Check celery.log"
    fi
fi