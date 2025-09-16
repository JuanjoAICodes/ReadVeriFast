🌟 GEMINI_DJANGO_MASTER_CONSOLIDATED_v1.md 🌟
This document is the single, definitive source of context, rules, and guidelines for the Gemini Agent for all tasks related to the VeriFast project. It supersedes all previous versions.

The VeriFast_PRD_v1.1_Django_EN.md document remains the primary source for product requirements and features. This master file governs the technical implementation of those features.

1. Vision and General Purpose of the Project
The primary goal of VeriFast is to create a web application that helps users improve their reading speed through gamified exercises on real-world articles. The application will leverage Large Language Models (LLMs) for content processing and quiz generation.

2. Application Architecture and Patterns (Django)
Directory Structure: Utilize Django's standard project structure, with a configuration "project" (config) and multiple "apps" for modularity (verifast_app, etc.).

Dependency Management: New Python libraries must be added to requirements.txt.

Database (Django ORM): Use the Django ORM for all interactions with the PostgreSQL database. Model definitions must reside in the models.py file of their respective apps.

Forms (Django Forms): Use Django Forms for all web forms, ensuring server-side validation and CSRF protection.

URLs and Views: URLs are defined in urls.py and views in views.py within each app. Prioritize the use of Class-Based Views (CBVs) for scalability.

Templates (DTL): Extend a base.html template to maintain UI consistency.

Admin Panel: Use django.contrib.admin for the backend. The task is to register models, not build admin views from scratch.

3. Coding Standards and Quality
Case Conventions: Use snake_case for variables, functions, and filenames. Use PascalCase for classes.

Docstrings: All modules, classes, and functions must have Google-style docstrings.

Clarity: Write clean, readable, and self-commenting code where possible.

4. Error Handling and Logging
4.1 Logging Configuration
- Implement comprehensive Django logging in settings.py with structured logging
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log all external API calls with request/response details and timing
- Include user context and request IDs in logs for debugging
- Use both file and console handlers for development and production

4.2 Exception Handling Patterns
- Wrap all external API calls (LLMs, web scraping) in robust try...except blocks
- Use specific exception types rather than bare except clauses
- Provide meaningful error messages to users while logging technical details
- Log full stack traces with context for debugging
- Implement proper error recovery strategies where possible

4.3 Error Response Standards
- Return consistent error responses in both web and API interfaces
- Include error codes, user-friendly messages, and technical details for debugging
- Log errors with sufficient context to be debuggable and traceable

5. Security
Rely on Django's built-in security features, including django.contrib.auth for password hashing, built-in CSRF protection for forms, and parameterized queries via the ORM to prevent SQL injection.

Never store secret keys or passwords in the source code; use environment variables.

6. Frontend Guidelines
CSS Framework: Use Pico.css for styling. Adhere to its classless, semantic HTML structure.

Client-Side JavaScript: Use vanilla JavaScript for any dynamic client-side behavior. Keep it minimal and well-documented.

7. Asynchronous Processing (Celery)
All slow operations (scraping, LLM calls) must be executed as asynchronous Celery tasks.

Tasks will be defined in tasks.py files within the relevant Django apps.

Redis will be used as the broker.

Tasks must follow the retry policy defined in the PRD.

8. Internationalization (i18n with Django)
Utilize the built-in Django i18n framework.

Strings in Python code will be marked with from django.utils.translation import gettext_lazy as _.

Strings in DTL templates will be marked with the {% trans "..." %} tag.

9. JSON API (with DRF) - API-Ready Backend
The backend MUST be API-ready to support future mobile applications (Android/iOS).

The REST API will be built using Django REST Framework (DRF) following a dual-interface pattern:
- Web Interface: Django templates for browser users
- API Interface: JSON REST API for mobile apps

API Structure:
- serializers.py files will be created to define the JSON representation of models
- viewsets will be created in api_views.py to define the API endpoints
- API URLs will be separated in api_urls.py for clean organization
- JWT token-based authentication for mobile apps
- Comprehensive API documentation with Swagger/OpenAPI

API Response Format:
All API responses must follow a consistent format with success/error indicators, data payload, and metadata.

10. Gamification and Business Logic
All gamification logic (XP calculation, WPM updates, comment interaction rules) must be implemented following the exact and clarified business rules in the PRD.

This logic should reside in well-defined and tested service functions or model methods to keep views "thin."

10.1 Service Layer Pattern
- Create service classes for complex business logic in services.py files
- Keep views thin by moving business logic to services
- Use static methods for stateless operations
- Implement proper error handling in service methods
- Use @transaction.atomic for operations that modify multiple models

10.2 Transaction Management
- Use @transaction.atomic for operations that modify multiple models
- Handle database integrity errors gracefully
- Implement proper rollback strategies for failed operations
- Log transaction failures with sufficient context for debugging

11. Agentic Tool Usage & Pre-Flight Checklist (MANDATORY)
This section governs your behavior when acting as an autonomous agent.

Planning is Mandatory: For any multi-step task, first think and propose a high-level plan of which tools you will use.

The "Read-Before-Write" Mandate (Prevents NameError, FieldError, ImportError):

Model Fields: Before writing any code (views.py, tasks.py, etc.) that accesses a model, you MUST first use your read_file tool on the relevant app/models.py file to confirm the exact field names.

URL Names: Before writing a redirect() or {% url %} tag, you MUST first use your read_file tool on the relevant app/urls.py file to confirm the exact app_name and the name of the URL pattern.

Run Validation Commands: After completing a stage, use your run_shell_command tool to execute validation commands (ruff, mypy, pytest) if requested.

Self-Correction: If a validation command fails, do not stop. Read the error, analyze the code, and use your tools to fix the bug. Re-run validation until it passes.

12. Canonical Naming & Referencing Protocol (MANDATORY)
This protocol is the single source of truth for all naming and referencing to prevent common Django errors.

A. URL Naming (NoReverseMatch Fix)
URL Names MUST use snake_case. (name='article_list')

The app_name Namespace is MANDATORY in every app's urls.py. (app_name = 'verifast_app')

All URL References MUST be Namespaced. ({% url 'verifast_app:article_list' %})

B. Model and Field Naming (FieldError Fix)
The models.py file is the sole source of truth.

No Assumptions: You MUST use read_file on the relevant models.py to confirm field names before using them in queries or forms.

Explicit Imports are MANDATORY for all models.

C. Module and Import Paths (ImportError Fix)
Standard Structure: All new features must be built within a standard Django app structure.

Absolute Imports: All imports MUST be absolute from the project root. (from verifast_app.models import Article). Relative imports (from .models) are forbidden.

13. Performance Best Practices
13.1 Database Optimization
- Use select_related() and prefetch_related() for database optimization to reduce N+1 queries
- Implement database indexing for frequently queried fields
- Use Django's database query optimization tools (django-debug-toolbar in development)
- Monitor query performance and optimize slow queries

13.2 Caching Strategy
- Use Django's caching framework for expensive operations
- Implement Redis caching for frequently accessed data
- Cache API responses where appropriate
- Use template fragment caching for expensive template rendering

13.3 API Performance
- Implement pagination for large datasets
- Use response compression (gzip) for API responses
- Minimize payload sizes by only sending necessary data
- Implement proper HTTP caching headers

14. Process Management (honcho) Protocol (MANDATORY)
This protocol ensures a clean and controllable development environment.

Procfile is the Source of Truth: All long-running processes are defined in the Procfile.

Use honcho: The human operator will run honcho start to start the web server and workers.

NEVER Run Servers in the Background: You are strictly forbidden from using manage.py runserver &, celery worker &, or any other backgrounding method. Instruct the human operator to run and stop processes.