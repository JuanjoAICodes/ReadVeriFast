# VeriFast - Consolidated Requirements Document

## Product Vision

VeriFast is an innovative web application designed to transform reading into an interactive training experience. The platform improves reading speed and comprehension using an advanced speed reader, AI-generated quizzes, and a robust gamification system with multilingual support (English and Spanish).

## Core User Stories

### Anonymous Users

**US-001: Browse Articles**
- As an anonymous user, I want to browse available articles so that I can see what content is available
- **Acceptance Criteria:**
  - WHEN I visit the homepage THEN I SHALL see a welcome message and navigation to articles
  - WHEN I click "Browse Articles" THEN I SHALL see a list of all processed articles
  - WHEN I view the article list THEN I SHALL see article titles, sources, and publication dates

**US-002: View Article Content**
- As an anonymous user, I want to view article content so that I can read articles normally
- **Acceptance Criteria:**
  - WHEN I click on an article THEN I SHALL be redirected to a login page
  - WHEN not logged in THEN I SHALL NOT have access to speed reading or quiz features

### Registered Users

**US-003: User Registration and Authentication**
- As a new user, I want to create an account so that I can access speed reading features
- **Acceptance Criteria:**
  - WHEN I register THEN I SHALL provide username, email, and password
  - WHEN I register THEN I SHALL start with 0 XP and 250 WPM default speed
  - WHEN I log in THEN I SHALL see my XP in the navigation bar
  - WHEN I log out THEN I SHALL be redirected to the homepage

**US-004: Speed Reading Experience**
- As a registered user, I want to use the speed reader so that I can improve my reading speed
- **Acceptance Criteria:**
  - WHEN I view an article THEN I SHALL see WPM controls and a "Start Speed Reading" button
  - WHEN I click "Start Speed Reading" THEN I SHALL see a full-screen modal with the article text
  - WHEN speed reading THEN I SHALL be able to adjust WPM with +5/-5 controls
  - WHEN I finish reading THEN I SHALL be able to start the quiz

**US-005: Quiz System**
- As a registered user, I want to take quizzes so that I can test my comprehension and earn XP
- **Acceptance Criteria:**
  - WHEN I complete speed reading THEN I SHALL be able to start the quiz
  - WHEN I take a quiz THEN I SHALL see 5 multiple-choice questions one at a time
  - WHEN I complete a quiz THEN I SHALL see my score and XP earned
  - WHEN I score >60% THEN I SHALL see detailed feedback for incorrect answers only
  - WHEN I score <60% THEN I SHALL see a generic failure message encouraging retry

**US-006: Gamification and XP System**
- As a registered user, I want to earn and spend XP so that I can track progress and participate socially
- **Acceptance Criteria:**
  - WHEN I complete a quiz THEN I SHALL earn XP based on score, WPM, and article complexity
  - WHEN I earn XP THEN my total XP SHALL be updated and displayed in navigation
  - WHEN I post a comment THEN I SHALL spend 10 XP (new comment) or 5 XP (reply)
  - WHEN I interact with comments THEN I SHALL spend XP (Bronze: 10, Silver: 50, Gold: 200)

**US-007: Social Features - Comments**
- As a registered user, I want to comment on articles so that I can discuss content with others
- **Acceptance Criteria:**
  - WHEN I complete a quiz THEN I SHALL be able to post comments on that article
  - WHEN I post a comment THEN I SHALL spend the appropriate XP cost
  - WHEN I reply to a comment THEN I SHALL spend 5 XP
  - WHEN others interact with my comments THEN I SHALL receive 50% of the XP they spend

**US-008: Comment Interactions**
- As a registered user, I want to interact with comments so that I can show appreciation or report issues
- **Acceptance Criteria:**
  - WHEN I view comments THEN I SHALL see positive and negative interaction buttons
  - WHEN I click positive THEN I SHALL cycle through Bronze (10 XP), Silver (50 XP), Gold (200 XP)
  - WHEN I click negative THEN I SHALL reverse my interaction level
  - WHEN I report a comment THEN I SHALL spend 0 XP but flag it for moderation

**US-009: User Profile Management**
- As a registered user, I want to manage my profile so that I can track progress and customize settings
- **Acceptance Criteria:**
  - WHEN I view my profile THEN I SHALL see current WPM, max WPM, total XP, and reading history
  - WHEN I access settings THEN I SHALL be able to change language preference and theme
  - WHEN I have an API key THEN I SHALL be able to configure preferred LLM model

### Content Submission

**US-010: Article Submission**
- As a registered user, I want to submit article URLs so that new content can be added to the platform
- **Acceptance Criteria:**
  - WHEN I submit a URL THEN the system SHALL scrape the article content
  - WHEN I submit a duplicate URL THEN I SHALL see a warning message
  - WHEN an article is submitted THEN it SHALL be processed asynchronously with LLM analysis
  - WHEN processing is complete THEN the article SHALL appear in the article list

### Administrative Features

**US-011: Content Management**
- As an administrator, I want to manage articles and users so that I can maintain platform quality
- **Acceptance Criteria:**
  - WHEN I access the admin panel THEN I SHALL see all models with appropriate filters and search
  - WHEN articles fail processing THEN I SHALL be able to retry processing
  - WHEN I need to moderate THEN I SHALL see reported comments and user interactions
  - WHEN I make corrections THEN they SHALL be stored in the AdminCorrectionDataset for LLM training

## Technical Requirements

### Performance Requirements
- **TR-001:** Article processing SHALL complete within 5 minutes for articles up to 10,000 words
- **TR-002:** Speed reader SHALL support WPM ranges from 100 to 1000 words per minute
- **TR-003:** Quiz generation SHALL produce exactly 5 multiple-choice questions per article
- **TR-004:** System SHALL handle concurrent users with response times under 2 seconds

### Security Requirements
- **SR-001:** User passwords SHALL be hashed using Django's built-in authentication
- **SR-002:** API keys SHALL be encrypted before storage in the database
- **SR-003:** All forms SHALL include CSRF protection
- **SR-004:** Admin access SHALL be restricted to staff users only

### Integration Requirements
- **IR-001:** System SHALL integrate with Google Gemini API for quiz generation
- **IR-002:** System SHALL use spaCy for natural language processing
- **IR-003:** System SHALL validate entities against Wikipedia API
- **IR-004:** System SHALL support PostgreSQL for production deployment

### Scalability Requirements
- **SC-001:** System SHALL use Celery for asynchronous task processing
- **SC-002:** System SHALL support horizontal scaling with Redis as message broker
- **SC-003:** Static files SHALL be served efficiently using WhiteNoise
- **SC-004:** Database queries SHALL be optimized to prevent N+1 problems

## Business Rules

### XP Calculation Formula
```
XP = (score_percentage * 50) + (wpm * 2 * complexity_factor)
Where complexity_factor = article.reading_level (Flesch-Kincaid grade)
```

### WPM Progression Rules
- Default starting WPM: 250
- WPM adjustments: ±5 increments
- Maximum WPM: 1000
- Minimum WPM: 100

### Comment Interaction Economics
- New comment cost: 10 XP
- Reply comment cost: 5 XP
- Bronze interaction: 10 XP
- Silver interaction: 50 XP
- Gold interaction: 200 XP
- Author receives: 50% of interaction XP spent

### Content Processing Rules
- Articles must be successfully scraped to enter processing queue
- LLM processing has 3 retry attempts with exponential backoff
- Failed articles are marked with appropriate status for admin review
- Tags are validated against Wikipedia before being assigned

## Multilingual Support

### Language Requirements
- **L-001:** System SHALL support English (en) and Spanish (es) content
- **L-002:** User interface SHALL be available in both languages
- **L-003:** NLP processing SHALL use appropriate language models (en_core_web_sm, es_core_news_sm)
- **L-004:** Wikipedia validation SHALL use language-appropriate endpoints

## Data Retention and Privacy

### Data Requirements
- **DR-001:** User data SHALL be retained according to privacy policy
- **DR-002:** Article content SHALL be stored for processing and user access
- **DR-003:** Quiz attempts SHALL be retained for progress tracking
- **DR-004:** Admin corrections SHALL be stored for LLM improvement

---

*This requirements document represents the consolidated and current state of VeriFast requirements as of July 2025.*