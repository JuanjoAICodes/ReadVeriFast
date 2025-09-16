# Getting Started with VeriFast

Welcome to VeriFast! This guide will help you get started with the project, whether you're a new user or a developer looking to contribute.

## For New Users

VeriFast is an AI-powered speed reading platform that helps you read faster and comprehend more. Here's how to get started:

1.  **Create an account:** Register for a new account to start your personalized reading journey.
2.  **Find an article:** Browse our library of articles or submit your own.
3.  **Start reading:** Use our speed reader to read the article at your desired pace.
4.  **Take a quiz:** Test your comprehension with our AI-powered quizzes.
5.  **Earn XP:** Earn experience points for your performance and unlock new features.

## For Developers

This guide will help you set up your development environment and start contributing to VeriFast.

### Prerequisites

*   Python 3.10+
*   Node.js and npm (for frontend dependencies)
*   PostgreSQL (for production)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd verifast
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    npm install
    ```

4.  **Set up the database:**
    ```bash
    python3 manage.py migrate
    ```

5.  **Run the development server:**
    ```bash
    python3 manage.py runserver
    ```

Visit `http://localhost:8000` to see the application running.

### API Keys

You'll need to set up API keys for the following services:

*   **Google Gemini API:** For AI-powered quiz generation.
*   **Wikipedia API:** For content tagging.

Add your API keys to a `.env` file in the root of the project:

```
GEMINI_API_KEY=your-gemini-api-key
WIKIPEDIA_USER_AGENT=VeriFastApp/1.0
```

### Deployment

For instructions on how to deploy VeriFast to a production environment, please see our [Deployment Guide](../development/README.md).
