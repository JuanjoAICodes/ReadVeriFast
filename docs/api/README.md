# VeriFast API Guide

This guide provides an overview of the VeriFast API.

## API Setup

To use the VeriFast API, you'll need to set up API keys for the following services:

*   **Google Gemini API:** For AI-powered quiz generation.
*   **Wikipedia API:** For content tagging.

Add your API keys to a `.env` file in the root of the project:

```
GEMINI_API_KEY=your-gemini-api-key
WIKIPEDIA_USER_AGENT=VeriFastApp/1.0
```

## Endpoints

The VeriFast API provides endpoints for the following:

*   **Authentication:** User login and registration.
*   **Articles:** Retrieve articles and submit new ones.
*   **Quizzes:** Submit quizzes and get results.
*   **Users:** Manage user profiles and settings.

For more detailed information about the API, please see the [API Setup and Configuration Guide](docs/archived/docs/API_SETUP_GUIDE.md).
