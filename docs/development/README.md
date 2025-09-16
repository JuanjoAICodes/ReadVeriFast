# VeriFast Development Guide

This guide provides conventions and best practices for developing on the VeriFast platform.

## Code Style

The project uses `ruff` for linting and formatting. Please ensure your code adheres to the project's style guidelines.

*   **Linting and formatting:**
    ```bash
    ruff check .
    ```

## Testing

The project uses `pytest` for testing. Please add tests for any new features or bug fixes.

*   **Running tests:**
    ```bash
    pytest
    ```

## Commits

Follow conventional commit message standards.

## Branching

Create a new branch for each feature or bug fix.

## Dependencies

Use `pip` to manage Python dependencies and `npm` for frontend dependencies. All dependencies should be added to the appropriate `requirements.txt` or `package.json` file.

## Architecture

VeriFast is a Django-based web application that uses HTMX hybrid architecture for speed reading functionality with gamification elements, AI-powered quizzes, and social features.

### Core Architecture Principles

*   **HTMX Hybrid Approach:** Server-side dominance with minimal client JavaScript.
*   **Technology Stack:** Django, PostgreSQL, HTMX + Alpine.js, Celery with Redis.

For a more detailed explanation of the architecture, please see the [Project Architecture Guide](docs/archived/documentation/PROJECT_ARCHITECTURE_GUIDE.md).
