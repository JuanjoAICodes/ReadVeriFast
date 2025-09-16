# VeriFast Testing Suite

Comprehensive end-to-end testing framework using Honcho for process management and Puppeteer for browser automation.

## Overview

This testing suite provides:
- **Process Management**: Honcho coordinates Django, Redis, and Celery services
- **Browser Automation**: Puppeteer tests user interactions and UI functionality
- **Integration Testing**: Python tests verify service connectivity and API responses
- **Comprehensive Coverage**: Tests all major features from authentication to XP systems

## Quick Start

### Run Full Test Suite
```bash
./scripts/run_full_test_suite.sh
```

### Run Individual Test Components

**Python Integration Tests:**
```bash
python -m pytest tests/e2e/test_honcho_integration.py -v
```

**Puppeteer Browser Tests:**
```bash
npm run test
```

**With Visible Browser:**
```bash
npm run test:visible
```

**With Slow Motion:**
```bash
npm run test:slow
```

## Test Architecture

### Process Management (Honcho)
- **Procfile.test**: Defines test service configuration
- **Port Isolation**: Test services run on different ports (8001, 6380)
- **Service Coordination**: Ensures all services start in correct order
- **Cleanup**: Automatic process cleanup on test completion

### Browser Testing (Puppeteer)
- **Test Runner**: `tests/puppeteer/test_runner.js` coordinates all browser tests
- **Test Suites**: Organized by feature area
- **Screenshots**: Automatic failure screenshots
- **Reporting**: JSON reports with detailed results

### Integration Testing (Python)
- **Service Health**: Verifies all services are running correctly
- **API Testing**: Tests REST endpoints and responses
- **Database**: Validates database connectivity and operations
- **Concurrency**: Tests application under concurrent load

## Test Suites

### 1. Authentication Tests (`authentication.test.js`)
- User registration with valid/invalid data
- Login/logout functionality
- Profile access and management
- Admin user verification

### 2. Article Reading Tests (`article_reading.test.js`)
- Article list display and pagination
- Article detail view access
- Metadata and tags display
- Responsive design verification

### 3. Speed Reader Tests (`speed_reader.test.js`)
- Speed reader initialization and controls
- WPM slider functionality
- Keyboard shortcuts
- Immersive mode activation/exit
- Premium feature detection
- Settings persistence

### 4. Quiz System Tests (`quiz_system.test.js`)
- Quiz generation and availability
- Quiz interface navigation
- Question structure validation
- Completion and scoring
- XP reward calculation

### 5. XP System Tests (`xp_system.test.js`)
- XP display consistency
- Premium feature store
- Purchase processes
- Feature unlock detection
- Transaction history

## Configuration

### Environment Variables
```bash
# Browser visibility
HEADLESS=false          # Show browser during tests
SLOW_MO=250            # Slow motion delay (ms)

# Test ports
TEST_PORT=8001         # Django test server
REDIS_TEST_PORT=6380   # Redis test instance
```

### Test Settings
- **Database**: In-memory SQLite for fast tests
- **Migrations**: Disabled for speed
- **External APIs**: Mocked/disabled
- **Logging**: Minimal for cleaner output

## Test Data

### Test Users
- **Regular User**: `testuser123` / `SecurePass123!`
- **Admin User**: `admin` / `admin`

### Test Articles
Tests use existing articles in the database or create minimal test content as needed.

## Reporting

### Test Reports
- **Summary**: `test_reports/test_summary.md`
- **Screenshots**: `tests/puppeteer/screenshots/`
- **Detailed JSON**: `tests/puppeteer/reports/`

### Report Contents
- Test execution summary
- Pass/fail rates
- Performance metrics
- Error details and screenshots
- Coverage analysis

## Troubleshooting

### Common Issues

**Services Won't Start:**
```bash
# Check port availability
lsof -i :8001
lsof -i :6380

# Kill existing processes
pkill -f "runserver 8001"
pkill -f "redis-server --port 6380"
```

**Browser Tests Fail:**
```bash
# Run with visible browser for debugging
HEADLESS=false npm run test

# Check browser console errors
# Screenshots are automatically saved on failure
```

**Database Issues:**
```bash
# Reset test database
python manage.py migrate --settings=config.settings_test --run-syncdb
```

### Debug Mode

**Verbose Output:**
```bash
# Python tests
python -m pytest tests/e2e/ -v -s

# Puppeteer tests with slow motion
HEADLESS=false SLOW_MO=500 npm run test
```

**Manual Service Start:**
```bash
# Start services manually for debugging
honcho -f Procfile.test start
```

## Extending Tests

### Adding New Test Suites

1. Create new test file in `tests/puppeteer/suites/`
2. Follow existing pattern:
   ```javascript
   module.exports = async function newFeatureTests(runner) {
       await runner.runTest('Test Name', async (page) => {
           // Test implementation
       });
   };
   ```
3. Add to test runner imports

### Adding Integration Tests

1. Add test methods to `test_honcho_integration.py`
2. Use `honcho_manager` fixture for service access
3. Follow pytest conventions

### Custom Assertions

```javascript
// Puppeteer custom assertions
if (!element) {
    throw new Error('Element not found');
}

// Python custom assertions
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
```

## Performance Considerations

- **Parallel Execution**: Tests run sequentially to avoid conflicts
- **Resource Cleanup**: Automatic cleanup prevents resource leaks
- **Timeout Management**: Appropriate timeouts for different operations
- **Memory Usage**: In-memory database and minimal test data

## CI/CD Integration

The test suite is designed for CI/CD environments:

```yaml
# Example GitHub Actions
- name: Run Full Test Suite
  run: |
    pip install -r requirements.txt
    npm install
    ./scripts/run_full_test_suite.sh
```

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Include proper error handling
3. Add descriptive console output
4. Update this documentation
5. Test both success and failure scenarios

---

*For questions or issues, refer to the project documentation or create an issue.*