# VeriFast Installation Guide

*Last Updated: July 21, 2025*
*Status: Current*

## Prerequisites

- Python 3.10 or higher
- Node.js 16+ (for frontend dependencies)
- Git

## Quick Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd verifast
```

### 2. Set Up Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies
```bash
npm install
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Set Up Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run the Application
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## Detailed Setup

For detailed development setup instructions, see [development.md](development.md).

## Troubleshooting

### Common Issues

1. **Migration Errors**: Ensure database is properly configured in `.env`
2. **Static Files**: Run `python manage.py collectstatic` if static files aren't loading
3. **Dependencies**: Make sure all requirements are installed with `pip install -r requirements.txt`

## Next Steps

- [Development Setup](development.md)
- [Project Architecture](../architecture/overview.md)
- [API Documentation](../api/specification.md)

## Related Documentation
- [Development Setup](development.md) - Detailed development environment setup
- [Project Architecture](../architecture/overview.md) - System architecture overview
- [API Documentation](../api/specification.md) - REST API reference