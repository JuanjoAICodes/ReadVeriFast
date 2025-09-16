# VeriFast v1.0 - Master Implementation PRP
name: "VeriFast v1.0: AI-Powered Speed Reading Platform (Master Build)"
description: |
  The definitive, executable plan for building VeriFast v1.0. This PRP synthesizes all requirements, technical decisions, and clarified business logic into a staged, backend-to-frontend implementation designed to be executed by the project's AI agent orchestrator.

---

## Goal
To build a fully-featured, multilingual (English/Spanish) web platform that helps users improve their reading skills in an interactive and engaging way.

## Why
To transform passive reading into an active training experience, tangibly improving user skills and capturing a global audience with a unique, gamified educational tool.

## What (v1.0 Success Criteria)
- [ ] Users can register, log in, and manage a profile with custom settings.
- [ ] A background task engine ingests and processes content from multiple APIs and sources.
- [ ] An LLM generates quizzes and tags for all content.
- [ ] A modal-based Speed Reader and Quiz UI provides an immersive user experience.
- [ ] A detailed, non-ambiguous gamification system rewards users with XP and progression.
- [ ] A robust comment and interaction system fosters community engagement.
- [ ] A Django Admin-powered dashboard provides full control over the application's data.

---

## All Needed Context

### Documentation & References (Pattern Library)
- **file:** `examples/models/user_example.py`
  - **why:** This is the required pattern for all Django models. It demonstrates the use of standard fields, the `__str__` method, and the mandatory `.to_dict()` method for API serialization.
- **file:** `examples/views/basic_view_example.py`
  - **why:** This is the pattern for Class-Based Views (CBVs). It shows how to define `template_name` and pass custom data to the template via `get_context_data`.
- **file:** `examples/tasks/async_task_example.py`
  - **why:** This is the required pattern for all asynchronous background tasks. It demonstrates the use of the `@shared_task` decorator from Celery.
- **file:** `examples/tests/test_model_example.py`
  - **why:** This is the pattern for all tests. It shows how to use Django's `TestCase`, set up data with `setUpTestData`, and write clear, specific assertions.

### Desired Codebase Tree (Django)
Use code with caution.
Markdown
verifast/
├── app/
│ ├── init.py
│ ├── models/
│ ├── tasks/
│ ├── main/
│ ├── auth/
│ ├── admin.py
│ ├── static/
│ ├── templates/
│ └── i18n/
├── migrations/
├── tests/
├── config/
│ ├── init.py
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── manage.py
└── ... (other root files)

Generated code
### Known Gotchas & Critical Rules
- **LLM API Retry Policy:** Any failed LLM API call must be retried up to 3 times with an exponential backoff (60s, 120s, 240s). On final failure, set article `processing_status` to `'failed'`.
- **Invalid URL Submission:** The `process_article_task` must validate user-submitted URLs. If the content type is not `text/html` or `text/plain`, or if the HTTP status is >= 400, the task must fail and notify the user.
- **API Rate Limits:** The content ingestion tasks must respect the daily rate limits for each API (e.g., Currents: 20/day, GNews: 100/day).
- **Gamification Precision:** The XP and WPM formulas are complex and must be implemented in their own dedicated, testable functions to ensure accuracy.

### Critical Business & Gamification Rules
- **Comment Costs:** Posting a new top-level comment costs **10 XP**. Replying to a comment costs **5 XP**.
- **Interaction Logic:** Implement a state machine for comment interactions using two buttons (`[👍 Positive]`, `[👎 Negative]`). Clicks cycle through levels (e.g., Bronze Like costs 5 XP, Silver 10 XP, etc.) and XP is adjusted accordingly.
- **XP Reward:** A comment author receives **exactly 50%** of the XP spent by users who give their comment a "Positive" interaction.
- **Comment Sorting:** The default sorting for comments on an article page must be by a calculated "net interaction score."

---

## Implementation Blueprint

### Technology Stack
- **Backend Framework:** Django
- **REST API Framework:** Django REST Framework (DRF)
- **Asynchronous Tasks:** Celery with Redis as the broker
- **Frontend CSS:** Pico.css

---

## Stage 1: Foundation & Project Setup
- **Tasks:**
  - [ ] Initialize a new Django project named `config` and a primary app named `app`.
  - [ ] Configure `config/settings.py` to use `django-environ` to load variables from the `.env` file.
  - [ ] Create a `base.html` template in `app/templates/` that includes the CDN link for Pico.css and defines a `{% block content %}`.
  - [ ] Implement all data models as defined in the PRD's "Modelo de Datos" section inside `app/models/`. Follow the pattern from `examples/models/user_example.py`.
  - [ ] Run `python manage.py makemigrations` and `python manage.py migrate` to create the initial database schema.

---

## Stage 2: User Authentication & Admin Dashboard
- **Tasks:**
  - [ ] Implement user registration, login, and logout views using Django's built-in `django.contrib.auth`.
  - [ ] Create the user profile page view, following the Class-Based View pattern from `examples/views/basic_view_example.py`.
  - [ ] In `app/admin.py`, register all created models with `django.contrib.admin` to generate the admin dashboard automatically.
- **Validation:**
  - **Command:** `pytest`

---

## Stage 3: Asynchronous Content Engine
- **Tasks:**
  - [ ] Configure Celery and Redis and integrate them with the Django project.
  - [ ] In `app/tasks/`, create the `fetch_new_articles_task`. Follow the pattern from `examples/tasks/async_task_example.py`.
  - [ ] In `app/tasks/`, create the `process_article_task`, ensuring it implements the robust chunking strategy for long content and the LLM API retry policy.
- **Validation:**
  - **Command:** `pytest`

---

## Stage 4: Core Frontend & Reading Experience
- **Tasks:**
  - [ ] Create the article list and detail views. The detail page must only display the article metadata and the Speed Reader control section.
  - [ ] Implement the Speed Reader UI as a full-screen modal with WPM controls, launched by a `[Start Speed Reading]` button.
  - [ ] Implement the Quiz UI, also as a full-screen modal, with the specified question state machine (next/pass logic).
  - [ ] Ensure the `[Start Quiz]` button is disabled until the reading is complete.
- **Validation:**
  - **Command:** `ruff check .`

---

## Stage 5: Gamification & Social Features
- **Tasks:**
  - [ ] Create a dedicated, testable function for calculating XP rewards based on the exact formula.
  - [ ] Implement the logic to save `QuizAttempt` data and update user `total_xp`, `current_wpm`, etc.
  - [ ] Implement the comment posting logic, ensuring it checks for a passed quiz and deducts the correct XP cost (10 for new, 5 for reply).
  - [ ] Implement the front-end and back-end logic for the comment interaction state machine.
- **Validation:**
  - **Command:** `pytest`

---

## Stage 6: API Layer & Final Testing
- **Tasks:**
  - [ ] Set up Django REST Framework and create a simple, read-only API endpoint for articles to prepare for future clients.
  - [ ] Write comprehensive unit and integration tests for all critical components: models, gamification logic, and tasks. Follow the pattern from `examples/tests/test_model_example.py`.
- **Validation:**
  - **Command:** `ruff check . --fix`
  - **Command:** `mypy .`
  - **Command:** `pytest`