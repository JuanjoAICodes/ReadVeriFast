# VeriFast Feature Inventory

A consolidated inventory of platform features compiled from current and legacy documentation, and validated against the codebase. Organized by domain with pointers to implementation locations and primary templates/endpoints.

Last updated: 2025-08-19

## 1) Reading Experience (Speed Reader)

Key capabilities
- Immersive reading mode (full-screen, minimal distractions)
- Server-side processing (HTMX hybrid) with minimal client JS
- WPM control, estimated reading time, graceful fallback UI
- Reading completion triggers XP award and unlocks quiz

Premium/advanced
- Word chunking: 1 (default), 2/3/4/5-word chunking (premium)
- Smart connector grouping (e.g., "the dragon")
- Smart symbol handling (punctuation spacing)
- Font and theme preferences (OpenSans, Roboto, Merriweather, Playfair, OpenDyslexic)

Implementation
- Views: `verifast_app/views.py` → `speed_reader_init`, `speed_reader_complete`, `process_content_with_powerups`
- Templates: `verifast_app/templates/verifast_app/partials/speed_reader_active.html`, `.../speed_reader_error.html`
- Feature flags (user): `verifast_app/models.py` (`has_2word_chunking`, etc.)
- Premium store/ownership: `verifast_app/xp_system.py` (PremiumFeatureStore)

## 2) Quiz System

Key capabilities
- AI/Gemini-generated quizzes stored per article
- HTMX hybrid flow: reading complete → quiz unlock → quiz interface → results
- Pass threshold: ≥ 60%; Perfect: 100%
- Minimal client script for timing; server renders/questions and grading

Implementation
- Views: `verifast_app/views.py` → `QuizStartView`, `QuizSubmissionAPIView`, `ReadingCompleteView`
- Templates: `verifast_app/templates/verifast_app/partials/quiz_unlock.html`, `quiz_interface.html`, `quiz_results.html`, `quiz_error.html`
- Models: `Article.quiz_data`, `QuizAttempt`

## 3) Comments & Interactions

Key capabilities
- Authenticated: can comment after passing quiz (≥ 60%)
- Anonymous: can comment after passing quiz (≥ 60%), providing a display name; stored under a guest mechanism
- Costs: new comment (10 XP), reply (5 XP) unless perfect 100% (free for auth users)
- Interactions: Bronze (5 XP) / Silver (15 XP) / Gold (30 XP); author receives 50% as XP
- HTMX-based refresh of comments section upon quiz pass

Implementation
- Views: `AddCommentView`, `CommentInteractView`, `CommentsSectionView`
- Templates: `verifast_app/templates/verifast_app/partials/comments_section.html`, `comments_list.html`
- Models: `Comment`, `CommentInteraction`
- XP integration: `verifast_app/xp_system.py` (SocialInteractionManager)
- URLs: `verifast_app/urls.py` (`comments/section/<article_id>/`)

## 4) XP (Gamification) System

Key capabilities
- XP earning: quiz completion (score, speed, complexity), reading completion, interaction rewards
- XP spending: premium features, comments/replies, interactions
- Transactions: all changes recorded, with validation and audit trail
- Monitoring: economy metrics, anomaly detection, performance helpers

Implementation
- `verifast_app/xp_system.py`: XPCalculationEngine, XPTransactionManager, XPMonitoringManager, XPPerformanceManager, SocialInteractionManager, PremiumFeatureStore
- Models: `XPTransaction`, `FeaturePurchase`, `CustomUser` balance fields
- Templates: user profile and XP widgets (`verifast_app/templates/verifast_app/components/*`)

## 5) Premium Feature Store

Key capabilities
- Catalog of features: fonts, chunking sizes, smart reading features
- Bundles with discounts (e.g., chunking progression, smart combo)
- Purchase flow with balance checking and activation

Implementation
- `verifast_app/xp_system.py`: `PremiumFeatureStore` and bundles, pricing
- Views/UI: `PremiumStoreView` and `templates/verifast_app/premium_store.html`

## 6) Tag System & Discovery

Key capabilities
- Wikipedia validation and canonicalization of tags
- Tag analytics: popularity, trending, relationships/co-occurrence
- Tag browsing and related articles

Implementation
- Services: `verifast_app/services/wikipedia_service.py` (validations), `verifast_app/tag_analytics.py`
- Views: `TagSearchView`, `TagDetailView`
- Templates: `templates/verifast_app/tag_search.html`, `tag_detail.html`

## 7) Content Acquisition & Processing

Key capabilities
- Multi-source ingestion: manual, RSS, NewsData, GNews, Wikipedia (and optional others)
- Content deduplication (hashes), quality scoring
- NLP and LLM pipeline for reading level, quiz generation, tag assignment
- Retry/backoff policies for external API calls

Implementation
- Services: `verifast_app/services/*` (rss_service, newsdata_service, gnews_service, content_orchestrator, content_deduplicator)
- Tasks: `verifast_app/tasks.py`, `tasks_content_acquisition.py`
- Admin & commands: `verifast_app/admin_content_acquisition.py`, `management/commands/*`

## 8) User Management & Profiles

Key capabilities
- Auth: session-based, and DRF JWT for API
- Profiles: WPM, XP, preferences (fonts, theme, language)
- Dashboards: attempts, XP balances, transactions, features

Implementation
- Views: `UserProfileView`, `UserProfileUpdateView`, forms
- Templates: `verifast_app/templates/verifast_app/user_profile.html`, `profile_edit.html`
- DRF endpoints (auth profile), see API spec

## 9) Internationalization (i18n)

Key capabilities
- English and Spanish UI
- Language preference per user
- Language switcher and localized URLs

Implementation
- Settings: `LANGUAGES`, `LOCALE_PATHS`, `LocaleMiddleware`
- Templates: language components in `templates/verifast_app/components`

## 10) API Architecture (DRF)

Key capabilities
- JWT auth, rate limits, JSON responses
- Endpoints: auth, articles, quizzes, comments (web via HTMX), XP info, purchases

Implementation
- `verifast_app/api_views.py`, `api_urls.py`
- `config/urls.py` routes `/api/v1/`

## 11) Admin & Dev Tooling

Key capabilities
- Django admin for data management
- Commands for scraping, content setup, Wikipedia articles
- Celery worker/beat for async jobs

Implementation
- Admin: `verifast_app/admin.py`, `admin_urls.py`
- Commands: `verifast_app/management/commands/*`
- Celery: `config/celery.py`

## 12) Performance & Security

Key capabilities
- Caching: user balances, feature store, transaction history
- DB: strategic indexes, prefetch/select_related
- CSRF, throttling, input validation, secure key storage

Implementation
- Cache config in settings, Redis support
- DRF throttles, CSRF headers in HTMX forms

---

## Feature → Code Quick Map

- Speed Reader: `views.py (speed_reader_init, process_content_with_powerups)`, `partials/speed_reader_active.html`
- Quiz: `views.py (QuizStartView, QuizSubmissionAPIView)`, `partials/quiz_*`
- Comments: `views.py (AddCommentView, CommentsSectionView, CommentInteractView)`, `partials/comments_*`
- XP/Store: `xp_system.py`, `components/xp_*`, `premium_store.html`
- Tags/Wikipedia: `services/wikipedia_service.py`, `tag_analytics.py`, `tag_* views/templates`
- Acquisition: `services/*`, `tasks.py`, `admin_*`, `management/commands/*`
- User/Profile: `UserProfileView`, `forms.py`, `user_profile.html`
- API: `api_views.py`, `api_urls.py`, `config/urls.py`

## Notes on Legacy vs Current
- Legacy front-end classes (SpeedReader/QuizInterface JS) documented historically have been replaced by HTMX server-rendered flows.
- Anonymous commenting: docs suggested it; the code now implements it via guest flow (session-enforced pass, guest name input, stored under guest account).
- Thresholds standardized at ≥ 60% for quiz pass, including comment unlock.

## Implementation Status (snapshot)

- Speed Reader
  - Immersive HTMX flow: Implemented
  - WPM controls, fallback UI: Implemented
  - Power-ups (chunking, smart grouping/symbols): Implemented (uses user boolean flags); caveat: does not check PremiumFeatureStore.user_owns_feature, so staff/admin may not see effects unless booleans are set
  - Fonts/themes: Implemented

- Quiz System
  - Generation/storage per article: Implemented (requires data availability)
  - HTMX unlock → interface → results: Implemented
  - Pass threshold ≥ 60%: Implemented (aligned)
  - Option schema normalization (strings vs objects): Partially supported; normalization not enforced universally

- Comments & Interactions
  - Authenticated comments after pass: Implemented
  - Anonymous (guest) comments after pass: Implemented (guest name + session-based pass; stored under guest/superuser account prefix)
  - Perfect score free comment: Implemented (auth users)
  - Interactions (Bronze/Silver/Gold) and author rewards: Implemented
  - HTMX refresh on quiz pass: Implemented

- XP System
  - Earning (quiz, reading, interactions) and spending (features, comments, interactions): Implemented
  - Transactions, validation, monitoring: Implemented
  - Feature store, bundles, pricing: Implemented

- Tag System & Wikipedia
  - Validation/canonicalization: Implemented
  - Analytics and discovery: Implemented
  - Note: duplicate Wikipedia service modules exist (see below)

- Content Acquisition & Processing
  - RSS/News APIs integration, dedup, quality: Implemented (requires API keys to run)
  - NLP/LLM pipeline and retry/backoff: Implemented

- User Management, Profiles, i18n, Admin, API
  - Auth/profile: Implemented
  - i18n (EN/ES): Implemented
  - Admin dashboards/commands: Implemented
  - API (DRF, JWT, throttling): Implemented; paths under /api/v1/


## Incompatibilities and Redundancies

- Legacy client-heavy JS vs current HTMX flows
  - Older docs reference `static/js/speed-reader.js`, `static/js/quiz-interface.js`. Current code uses server-rendered partials with minimal inline scripts. These are alternative approaches; HTMX is the active one.

- Wikipedia service duplication
  - `verifast_app/services/wikipedia_service.py` and `verifast_app/wikipedia_service.py`. Maintain one canonical service to avoid drift; tests/imports should target the services package path.

- Power-up ownership check inconsistency
  - Speed Reader uses user boolean fields (has_2word_chunking, etc.), while feature ownership logic (including staff-implied ownership) lives in PremiumFeatureStore. This can confuse admins who "own" features conceptually but don’t see effects. Recommend using `PremiumFeatureStore.user_owns_feature` in processing.

- Anonymous commenting storage
  - Documentation mentions cookie-based guest identity; current implementation uses session quiz state and stores comments under a guest/superuser account with a visible name prefix. Consider aligning to a dedicated Guest user and optional signed cookie for name.

- Environment configuration
  - Pydantic settings expect JSON lists (or indexed vars) for list fields; incompatible `.env` formats can break startup. Docs should reflect this requirement.

- API path naming
  - Some docs reference `/api/`; current routes are under `/api/v1/`.


## Open Questions

1) Speed Reader power-ups: Should we switch to `PremiumFeatureStore.user_owns_feature` for feature detection (so staff/admin and store ownership are reflected automatically)?
2) Quiz data normalization: Do we need to normalize `options` to strings on load so older quizzes (with `{"text": "..."}`) render consistently?
3) Anonymous comments:
   - Do you want a dedicated non-privileged `guest` account created on setup for attribution?
   - Should we store a signed cookie with `guest_name` (in addition to session pass state) and set an explicit expiry?
   - Do anonymous comments ever incur XP or remain free by design?
4) Wikipedia services: Which module should be the single source of truth? Shall we deprecate the older one?
5) Content acquisition: Which external sources should be enabled by default in non-production environments (given API key requirements)?


## Suggested Future Enhancements
- Use `PremiumFeatureStore.user_owns_feature` in Speed Reader processing to reflect ownership for staff/admin consistently.
- Normalization of quiz option schema (strings vs objects) on load.
- Rate limiting for anonymous comments; optional signed cookie for guest name.
- Dedicated guest user setup on bootstrap.
