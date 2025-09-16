#!/bin/bash

# VeriFast Full Test Suite Runner
# Coordinates Honcho process management with Puppeteer browser testing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_PORT=8001
REDIS_TEST_PORT=6380
HEADLESS=${HEADLESS:-true}
SLOW_MO=${SLOW_MO:-0}

echo -e "${BLUE}🚀 VeriFast Full Test Suite${NC}"
echo "=================================="

# Function to cleanup processes
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up processes...${NC}"
    
    # Kill any existing test processes
    pkill -f "runserver 8001" || true
    pkill -f "redis-server --port 6380" || true
    pkill -f "celery.*worker" || true
    pkill -f "node.*test_runner.js" || true
    
    # Wait a moment for cleanup
    sleep 2
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set up cleanup trap
trap cleanup EXIT

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check if Honcho is installed
if ! command -v honcho &> /dev/null; then
    echo -e "${RED}❌ Honcho not found. Install with: pip install honcho${NC}"
    exit 1
fi

# Check if Node.js and Puppeteer are available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js${NC}"
    exit 1
fi

if [ ! -f "node_modules/puppeteer/package.json" ]; then
    echo -e "${YELLOW}⚠️  Puppeteer not found. Installing...${NC}"
    npm install
fi

# Check if Python dependencies are available
if ! python -c "import django" &> /dev/null; then
    echo -e "${RED}❌ Django not found. Install with: pip install -r requirements.txt${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Prepare test environment
echo -e "\n${BLUE}🔧 Preparing test environment...${NC}"

# Create test database
echo "Creating test database..."
python manage.py migrate --settings=config.settings_test --run-syncdb

# Create test superuser (non-interactive)
echo "Creating test superuser..."
python manage.py shell --settings=config.settings_test << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'admin')
    print('Test superuser created')
else:
    print('Test superuser already exists')
EOF

# Create test user for Puppeteer tests
python manage.py shell --settings=config.settings_test << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='testuser123').exists():
    User.objects.create_user('testuser123', 'test@example.com', 'SecurePass123!')
    print('Test user created')
else:
    print('Test user already exists')
EOF

echo -e "${GREEN}✅ Test environment prepared${NC}"

# Start test services with Honcho
echo -e "\n${BLUE}🚀 Starting test services...${NC}"

# Start Honcho in background
honcho -f Procfile.test start &
HONCHO_PID=$!

# Wait for services to be ready
echo "Waiting for Django server to start..."
for i in {1..30}; do
    if curl -s http://localhost:$TEST_PORT/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Django server is ready${NC}"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Django server failed to start within timeout${NC}"
        exit 1
    fi
    
    echo "Attempt $i/30 - waiting..."
    sleep 2
done

# Run Python integration tests
echo -e "\n${BLUE}🐍 Running Python integration tests...${NC}"
python -m pytest tests/e2e/test_honcho_integration.py -v --tb=short

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Python integration tests passed${NC}"
else
    echo -e "${RED}❌ Python integration tests failed${NC}"
    exit 1
fi

# Run Puppeteer browser tests
echo -e "\n${BLUE}🎭 Running Puppeteer browser tests...${NC}"

# Set environment variables for Puppeteer
export HEADLESS=$HEADLESS
export SLOW_MO=$SLOW_MO

# Run Puppeteer tests
node tests/puppeteer/test_runner.js

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Puppeteer browser tests completed${NC}"
else
    echo -e "${RED}❌ Puppeteer browser tests failed${NC}"
    exit 1
fi

# Generate combined test report
echo -e "\n${BLUE}📊 Generating test report...${NC}"

# Create reports directory
mkdir -p test_reports

# Generate summary report
cat > test_reports/test_summary.md << EOF
# VeriFast Test Suite Report

**Date:** $(date)
**Environment:** Test
**Services:** Django, Redis, Celery, Puppeteer

## Test Results

### Python Integration Tests
- ✅ Service health checks
- ✅ Django application accessibility
- ✅ Database connectivity
- ✅ API endpoint responses
- ✅ Concurrent request handling

### Browser Tests (Puppeteer)
- 🔐 Authentication system tests
- 📚 Article reading functionality
- ⚡ Speed reader system tests
- 🧠 Quiz system functionality
- 💰 XP system and premium features

## Test Coverage Areas

1. **Authentication & User Management**
   - User registration and login
   - Profile management
   - Admin access

2. **Article Management**
   - Article listing and display
   - Content rendering
   - Metadata and tags

3. **Speed Reader System**
   - Basic controls and functionality
   - Immersive mode
   - Premium features
   - Settings persistence

4. **Quiz System**
   - Quiz generation and display
   - User interaction
   - Scoring and XP rewards

5. **XP Economics**
   - XP display and tracking
   - Premium feature store
   - Transaction system

## Screenshots
Browser test screenshots are available in: \`tests/puppeteer/screenshots/\`

## Detailed Reports
- Python test results: Available in pytest output
- Puppeteer test results: \`tests/puppeteer/reports/\`

---
*Generated by VeriFast automated test suite*
EOF

echo -e "${GREEN}✅ Test report generated: test_reports/test_summary.md${NC}"

# Final summary
echo -e "\n${GREEN}🎉 Full test suite completed successfully!${NC}"
echo -e "${BLUE}📁 Test artifacts:${NC}"
echo "  - Test report: test_reports/test_summary.md"
echo "  - Screenshots: tests/puppeteer/screenshots/"
echo "  - Detailed reports: tests/puppeteer/reports/"

echo -e "\n${YELLOW}💡 To run tests with visible browser:${NC}"
echo "  HEADLESS=false ./scripts/run_full_test_suite.sh"

echo -e "\n${YELLOW}💡 To run tests with slow motion:${NC}"
echo "  SLOW_MO=250 ./scripts/run_full_test_suite.sh"