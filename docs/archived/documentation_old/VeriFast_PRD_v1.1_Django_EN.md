# VeriFast v1.0 - Product Requirements Document (PRD) - Django Edition

## 1. Product Vision
VeriFast is an innovative web application designed to transform reading into an interactive training experience. Our focus is to improve reading speed and comprehension using an advanced speed reader, AI-generated quizzes, and a robust gamification system. The platform will be multilingual, with full support for English and Spanish, and the capacity to expand to other languages. The user experience will be clean and minimalist, with a robust architecture prepared for future expansions and adaptation to each user's reading level.

The application will feature a robust social component, allowing user interaction through comments on articles. The user experience will be managed through Total Experience (accumulated XP) and Experience Points (spendable XP for social interactions).

## 2. Technology Stack (Revised for Django)
VeriFast's architecture will be based on the Django ecosystem to guarantee robustness, scalability, and rapid development.
*   **Backend:** **Django**, utilizing its "apps" architecture for modularity.
*   **Asynchronous Tasks:** **Celery** (with Worker and Beat) for long-running operations like article ingestion and processing.
*   **Message Broker:** **Redis**, as the intermediary for Celery tasks.
*   **Database:** **PostgreSQL**.
*   **ORM & Migrations:** The built-in **Django ORM** and its integrated **migration system**.
*   **Frontend:** **Django Template Language (DTL)** templates with the **Pico.css** framework.
*   **WSGI Server:** **Gunicorn**, deployed behind a reverse proxy like Nginx.
*   **Authentication:** The built-in **`django.contrib.auth`** module.
*   **Forms:** The **Django Forms** framework.
*   **Internationalization (i18n):** Django's robust **internationalization framework** for translation management (`.po`, `.mo` files).
*   **JSON API:** **Django REST Framework (DRF)** for building the flexible API.
*   **Admin Dashboard:** The **`django.contrib.admin`** module for data management.

## 3. Data Model (Implemented with Django ORM)
The data model is designed to support core functionalities. All models will include a `.to_dict()` method for serialization.

*   **User (extending `django.contrib.auth.models.AbstractUser` or a One-to-One Profile):**
    *   Standard Django fields: `id`, `username`, `email`, `password` (hashed by Django), `is_staff`, `is_superuser`.
    *   Custom fields: `is_admin`, `current_wpm`, `max_wpm`, `total_xp`, `current_xp_points`, `negative_xp_points`, `preferred_language`, `theme`, `last_successful_wpm_used`, `llm_api_key_encrypted`, `preferred_llm_model`, `ad_free_articles_count`.
*   **Article (`models.Model`):**
    *   `id`, `url`, `title`, `image_url`, `language`, `processing_status`, `quiz_data` (JSONField), `raw_content`, `content`, `source`, `publication_date`, `is_user_submitted`, `timestamp`, `user` (ForeignKey to User), `llm_model_used`, `reading_level`, `tags` (ManyToManyField to Tag).
*   **Tag (`models.Model`):**
    *   `id`, `name`.
*   **QuizAttempt (`models.Model`):**
    *   `id`, `user` (ForeignKey), `article` (ForeignKey), `score`, `wpm_used`, `xp_earned`, `xp_awarded`, `result`, `timestamp`, `reading_time_seconds`, `quiz_time_seconds`, `quiz_rating`, `quiz_feedback`.
*   **Comment (`models.Model`):**
    *   `id`, `user` (ForeignKey), `article` (ForeignKey), `text`, `timestamp`, `parent_comment` (ForeignKey to 'self').
*   **CommentInteraction (`models.Model`):**
    *   `id`, `user` (ForeignKey), `comment` (ForeignKey), `type`, `level`, `xp_cost`, `timestamp`.
*   **AdminCorrectionDataset (`models.Model`):**
    *   `id`, `original_article_url`, `original_content_hash`, `corrected_content`, `correction_type`, `admin_user` (ForeignKey), `timestamp`.

## 4. Anonymous User Flow
*(No change in functionality; implementation will use Django views).*

## 5. Registered User Flow and Gamification (Clarified Rules)
*   **Registration/Login:** Managed by `django.contrib.auth`.
*   **Profile Page:** A Django view that displays user statistics and a Django `ProfileForm` for managing preferences.
*   **Gamification Logic (Final Rules):**
    *   WPM progression rules and the base XP formula will be implemented exactly as in the original PRD.
    *   **Comment Cost:** Posting a new, top-level comment costs **10 XP**. Replying to a comment costs **5 XP**.
    *   **Comment Interactions:** There will be two buttons: `[👍 Positive]` and `[👎 Negative]`. Repeated clicks on the positive button will cycle through Bronze (5 XP), Silver (10 XP), and Gold (20 XP) levels, adjusting the cost. The negative button can be used to reverse the level.
    *   **XP Reward:** A comment's author receives **exactly 50%** of the XP spent on "Positive" interactions on their comment.
    *   **Negative Points:** `negative_xp_points` are accumulated for admin tracking. Default comment sorting will be by a "net score" based on interactions.
*   **Speed Reader UI (Clarified):**
    *   The article content is **not displayed directly**. The user interacts with a control section (`[< -5] [250/300 WPM] [+5 >]`, `[Start Speed Reading]`, `[Start Quiz]`).
    *   Clicking "Start Speed Reading" launches a **full-screen modal** with a dark background for reading.
    *   Clicking "Start Quiz" launches a **similar modal** with one-by-one questions and a timer.
*   **Quiz Feedback (Final Rules):**
    *   Successful Quiz (`>60%`): Displays XP earned and provides detailed feedback **only for incorrect answers**.
    *   Failed Quiz (`<60%`): Displays a generic failure message with no detailed feedback to encourage a retry.

## 6. Content Engine (Clarified Strategy)
*   **Source Priority:** 1. User-submitted URLs, 2. Curated GNews API, 3. RSS Feeds, 4. Currents API, 5. Exploratory GNews, 6. Wikipedia/Books.
*   **API Keys:** All system-level API keys will be managed via a `.env` file and loaded into `settings.py` with `django-environ`.
*   **Long-form Content Chunking:** The strategy will be: 1. Split by chapters or `<h2>` sections. 2. Group paragraphs into 400-600 word segments. 3. Each segment becomes a database `Article`.

## 7. Processing Task (Clarified Error Policy)
*   **LLM API Retry Policy:** The Celery task will retry failed LLM API calls up to **3 times** with an exponential backoff (60s, 120s, 240s). After the final failure, the article's `processing_status` will be set to `'failed'`.

## 8. Admin Dashboard (Implementation with Django Admin)
*   This requirement will be met using the **`django.contrib.admin`** module. The development task is to **register all data models** in `app/admin.py` to make them manageable via the auto-generated admin interface. Custom `ModelAdmin` classes can be created to add filters, search, and custom actions like "Retry Processing".

## 9. Architecture and Extensibility (Updated for DRF)
*   **JSON API:** The flexible API will be built using **Django REST Framework (DRF)** by creating serializers for the models and viewsets for the endpoints.
*   **LLM Integration:** The abstraction layer remains a key architectural requirement, allowing for model flexibility and user-key management.