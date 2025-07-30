# VeriFast Development Setup

*Last Updated: July 21, 2025*
*Status: Current*

## Development Environment Setup

### 1. Development Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists
```

### 2. Database Configuration
```bash
# For development, SQLite is sufficient
python manage.py migrate
python manage.py loaddata fixtures/sample_data.json  # If available
```

### 3. Environment Variables
Create a `.env` file with development settings:
```env
DEBUG=True
SECRET_KEY=your-development-secret-key
DATABASE_URL=sqlite:///db.sqlite3
GEMINI_API_KEY=your-gemini-api-key
```

### 4. Frontend Development
```bash
# Install frontend dependencies
npm install

# For development with hot reload
npm run dev
```

## Development Workflow

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific test modules
python manage.py test verifast_app.test_xp_system
python manage.py test verifast_app.test_tag_system
```

### Code Quality
```bash
# Type checking
mypy .

# Code formatting
ruff format .

# Linting
ruff check .
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Development Tools

### Admin Interface
Access the Django admin at `http://localhost:8000/admin/` with your superuser credentials.

### API Testing
- REST API available at `http://localhost:8000/api/`
- API documentation at `http://localhost:8000/api/docs/` (if configured)

### Debugging
- Django Debug Toolbar is available in development mode
- Use `python manage.py shell` for interactive debugging

## Project Structure

```
verifast/
├── config/          # Django settings
├── verifast_app/    # Main application
├── core/            # Core functionality
├── templates/       # HTML templates
├── static/          # Static files
├── documentation/   # Project documentation
└── .kiro/          # Kiro specifications
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run tests and ensure they pass
4. Update documentation if needed
5. Submit a pull request

## Related Documentation
- [Installation Guide](installation.md)
- [Project Architecture](../architecture/overview.md)
- [Testing Guide](../development/testing.md)