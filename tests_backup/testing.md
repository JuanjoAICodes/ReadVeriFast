# Testing Guide

*Last Updated: July 21, 2025*
*Status: Current*

## Overview

VeriFast uses Django's built-in testing framework along with additional tools for comprehensive testing coverage. This guide covers testing practices, running tests, and writing new tests.

## Testing Framework

### Django Test Framework
- **TestCase** - Database-backed tests with transaction rollback
- **SimpleTestCase** - Lightweight tests without database
- **TransactionTestCase** - Tests requiring database transactions
- **LiveServerTestCase** - Full server tests with real HTTP requests

### Additional Testing Tools
- **Coverage.py** - Code coverage measurement
- **Factory Boy** - Test data generation (if installed)
- **Mock/Patch** - External service mocking
- **Selenium** - Browser automation testing (if needed)

## Running Tests

### Basic Test Commands
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test verifast_app

# Run specific test class
python manage.py test verifast_app.tests.XPSystemTestCase

# Run specific test method
python manage.py test verifast_app.tests.XPSystemTestCase.test_xp_calculation

# Run with verbose output
python manage.py test --verbosity=2

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Test Configuration
```python
# settings.py - Test-specific settings
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
    
    # Disable migrations for faster tests
    class DisableMigrations:
        def __contains__(self, item):
            return True
        def __getitem__(self, item):
            return None
    
    MIGRATION_MODULES = DisableMigrations()
```

## Test Structure

### Current Test Files
```
verifast_app/
├── tests.py                    # Main test file
├── test_xp_system.py          # XP system tests
├── test_xp_economics.py       # XP economics tests
├── test_tag_system.py         # Tag system tests
└── test_files/                # Additional test modules
    ├── test_services.py       # Service layer tests
    ├── test_tasks.py          # Celery task tests
    └── test_wikipedia_service.py # Wikipedia integration tests
```

### Test Organization
```python
# Example test structure
class ModelTestCase(TestCase):
    """Test model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_model_creation(self):
        """Test basic model creation"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.current_xp_points, 0)
    
    def test_model_methods(self):
        """Test model methods"""
        self.assertTrue(self.user.is_authenticated)
```

## Testing Best Practices

### Test Data Management
```python
class TestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Create test data once for the entire test class"""
        cls.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
    
    def setUp(self):
        """Set up for each test method"""
        self.client = Client()
        self.client.force_login(self.user)
```

### Mocking External Services
```python
from unittest.mock import patch, MagicMock

class WikipediaServiceTest(TestCase):
    @patch('verifast_app.wikipedia_service.requests.get')
    def test_wikipedia_api_call(self, mock_get):
        """Test Wikipedia API integration"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'query': {'pages': {'123': {'title': 'Test Page'}}}
        }
        mock_get.return_value = mock_response
        
        # Test the service
        service = WikipediaService()
        result = service.validate_tag_with_wikipedia('test')
        
        self.assertTrue(result[0])  # is_valid
        self.assertIsNotNone(result[1])  # data
```

### Testing Views
```python
class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_authenticated_view(self):
        """Test view requiring authentication"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/profile/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
    
    def test_unauthenticated_redirect(self):
        """Test redirect for unauthenticated users"""
        response = self.client.get('/profile/')
        self.assertRedirects(response, '/login/?next=/profile/')
```

## Specific Test Areas

### XP System Testing
**Location:** `verifast_app/test_xp_system.py`

**Test Coverage:**
- XP calculation accuracy
- Transaction management
- Balance validation
- Premium feature purchases
- Concurrent transaction handling

### Tag System Testing
**Location:** `verifast_app/test_tag_system.py`

**Test Coverage:**
- Tag creation and validation
- Wikipedia integration
- Tag search functionality
- Tag analytics
- Admin interface actions

### Speed Reader Testing
**Frontend Testing:**
- HTMX request/response cycles
- Alpine.js component functionality
- Server-side content processing
- Progressive enhancement fallbacks
- Mobile responsiveness

### API Testing
```python
class APITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_api_authentication(self):
        """Test API authentication"""
        # Test without authentication
        response = self.client.get('/api/user/')
        self.assertEqual(response.status_code, 401)
        
        # Test with authentication
        self.client.force_login(self.user)
        response = self.client.get('/api/user/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_response_format(self):
        """Test API response format"""
        self.client.force_login(self.user)
        response = self.client.get('/api/user/')
        
        data = response.json()
        self.assertIn('username', data)
        self.assertIn('current_xp_points', data)
```

## Performance Testing

### Database Query Testing
```python
from django.test.utils import override_settings
from django.db import connection

class PerformanceTestCase(TestCase):
    def test_query_count(self):
        """Test database query efficiency"""
        with self.assertNumQueries(2):  # Expected number of queries
            # Code that should execute exactly 2 queries
            articles = Article.objects.select_related('user').all()
            list(articles)  # Force evaluation
```

### Load Testing
```python
import time
from concurrent.futures import ThreadPoolExecutor

class LoadTestCase(TestCase):
    def test_concurrent_xp_transactions(self):
        """Test XP system under load"""
        def earn_xp():
            manager = XPTransactionManager()
            return manager.earn_xp(
                user=self.user,
                amount=10,
                source='test',
                transaction_type='EARN',
                description='Load test'
            )
        
        # Run 10 concurrent transactions
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(earn_xp) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # Verify all transactions succeeded
        self.assertTrue(all(results))
```

## Integration Testing

### End-to-End User Flows
```python
class IntegrationTestCase(TestCase):
    def test_complete_reading_flow(self):
        """Test complete user reading journey"""
        # 1. User logs in
        self.client.login(username='testuser', password='testpass123')
        
        # 2. User selects article
        article = Article.objects.create(
            title='Test Article',
            content='Test content',
            processing_status='complete'
        )
        
        # 3. User reads article (simulate)
        response = self.client.get(f'/articles/{article.id}/')
        self.assertEqual(response.status_code, 200)
        
        # 4. User takes quiz
        quiz_data = {
            'answers': {'1': 'A', '2': 'B'},
            'wpm_used': 250,
            'time_taken': 120
        }
        response = self.client.post(f'/api/articles/{article.id}/quiz/submit/', quiz_data)
        self.assertEqual(response.status_code, 200)
        
        # 5. Verify XP was awarded
        self.user.refresh_from_db()
        self.assertGreater(self.user.current_xp_points, 0)
```

## Test Data Management

### Fixtures
```python
# Create test fixtures
python manage.py dumpdata verifast_app.Article --indent=2 > fixtures/test_articles.json

# Load fixtures in tests
class TestWithFixtures(TestCase):
    fixtures = ['test_articles.json']
    
    def test_with_fixture_data(self):
        articles = Article.objects.all()
        self.assertGreater(articles.count(), 0)
```

### Factory Pattern
```python
# If using Factory Boy
import factory

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    current_xp_points = 100

class ArticleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Article
    
    title = factory.Faker('sentence', nb_words=4)
    content = factory.Faker('text', max_nb_chars=1000)
    processing_status = 'complete'
```

## Continuous Integration

### GitHub Actions Example
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install coverage
    
    - name: Run tests
      run: |
        coverage run --source='.' manage.py test
        coverage report --fail-under=80
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Test Coverage Goals

### Coverage Targets
- **Overall Coverage:** 80%+
- **Critical Components:** 90%+
  - XP System
  - User Authentication
  - Payment/Premium Features
- **Models:** 95%+
- **Views:** 80%+
- **Services:** 85%+

### Coverage Commands
```bash
# Generate coverage report
coverage run --source='.' manage.py test
coverage report

# Generate HTML coverage report
coverage html
# Open htmlcov/index.html in browser

# Check specific files
coverage report --include="verifast_app/xp_system.py"
```

## Debugging Tests

### Test Debugging
```python
import pdb

class DebugTestCase(TestCase):
    def test_with_debugging(self):
        """Test with debugging breakpoint"""
        user = CustomUser.objects.create_user(username='test')
        
        # Set breakpoint for debugging
        pdb.set_trace()
        
        # Continue with test logic
        self.assertEqual(user.username, 'test')
```

### Test Output
```bash
# Run tests with verbose output
python manage.py test --verbosity=2

# Keep test database for inspection
python manage.py test --keepdb

# Run specific test with debugging
python manage.py test verifast_app.tests.TestCase.test_method --debug-mode
```

## Related Documentation
- [Development Setup](../setup/development.md) - Development environment
- [API Specification](../api/specification.md) - API testing
- [XP System](../features/xp-system.md) - XP system testing details
- [Tag System](../features/tag-system.md) - Tag system testing details