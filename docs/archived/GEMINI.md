# VeriFast - AI-Powered Speed Reading Platform

## Project Overview

This project is a Django-based web application called "VeriFast" that aims to provide a comprehensive speed reading experience. It integrates AI-powered features, gamification, and social elements to create an engaging learning platform. The frontend is built using HTMX, and the backend leverages the Gemini API for generating quizzes and the Wikipedia API for content tagging.

The application allows users to read articles in a special speed-reading mode, take quizzes to test their comprehension, and earn experience points (XP) for their performance. Users can spend their XP on premium features, such as custom fonts and advanced reading settings. The platform also includes a social component, allowing users to comment on articles and interact with each other's comments.

## Building and Running

### Prerequisites

*   Python 3.10+
*   Node.js and npm (for frontend dependencies)
*   PostgreSQL (for production)

### Key Commands

*   **Installation:**
    ```bash
    pip install -r requirements.txt
    npm install
    ```
*   **Running the development server:**
    ```bash
    python3 manage.py migrate
    python3 manage.py runserver
    ```
*   **Running tests:**
    ```bash
    pytest
    ```
*   **Linting and formatting:**
    ```bash
    ruff check .
    ```

## Development Conventions

*   **Code Style:** The project uses `ruff` for linting and formatting. Please ensure your code adheres to the project's style guidelines.
*   **Testing:** The project uses `pytest` for testing. Please add tests for any new features or bug fixes.
*   **Commits:** Follow conventional commit message standards.
*   **Branching:** Create a new branch for each feature or bug fix.
*   **Dependencies:** Use `pip` to manage Python dependencies and `npm` for frontend dependencies. All dependencies should be added to the appropriate `requirements.txt` or `package.json` file.
