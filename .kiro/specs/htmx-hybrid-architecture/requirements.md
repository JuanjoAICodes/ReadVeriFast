# Requirements Document

## Introduction

The current VeriFast article reading system uses complex JavaScript for speed reading and quiz functionality, resulting in high maintenance burden, debugging difficulties, and performance issues. This refactor will implement a hybrid HTMX + minimal JavaScript architecture that maintains all existing functionality while dramatically reducing complexity and improving maintainability. The new system will work seamlessly for both regular articles and Wikipedia articles.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to maintain all business logic on the server side, so that I can debug, test, and modify the system using familiar Django tools and patterns.

#### Acceptance Criteria

1. WHEN processing user power-ups THEN the system SHALL handle all gamification logic in Django/Python
2. WHEN chunking words for speed reading THEN the system SHALL apply user's purchased features server-side
3. WHEN calculating XP rewards THEN the system SHALL process all calculations in Django views
4. WHEN validating quiz submissions THEN the system SHALL perform all validation server-side
5. WHEN applying font customizations THEN the system SHALL generate CSS settings in Django templates

### Requirement 2

**User Story:** As a user, I want the speed reader to work smoothly without network delays during reading, so that I can maintain focus and reading flow.

#### Acceptance Criteria

1. WHEN starting speed reading THEN the system SHALL send all processed word chunks to the client once
2. WHEN displaying words THEN the system SHALL use client-side timing without server requests
3. WHEN adjusting reading speed THEN the system SHALL update timing locally without server communication
4. WHEN completing reading THEN the system SHALL send only completion notification to server
5. WHEN pausing/resuming THEN the system SHALL handle state changes locally

### Requirement 3

**User Story:** As a user, I want the same reading and quiz experience whether I'm reading regular articles or Wikipedia articles, so that I have a consistent interface across all content types.

#### Acceptance Criteria

1. WHEN viewing any article type THEN the system SHALL provide identical speed reader interface
2. WHEN taking quizzes THEN the system SHALL use the same quiz component for all article types
3. WHEN earning XP THEN the system SHALL apply consistent reward calculations across article types
4. WHEN using power-ups THEN the system SHALL apply features uniformly regardless of article source
5. WHEN navigating THEN the system SHALL maintain consistent URL patterns and routing

### Requirement 4

**User Story:** As a developer, I want to reduce JavaScript complexity from 500+ lines to under 50 lines, so that the codebase is easier to maintain and debug.

#### Acceptance Criteria

1. WHEN implementing speed reader THEN the system SHALL use maximum 30 lines of JavaScript
2. WHEN implementing quiz system THEN the system SHALL use maximum 20 lines of JavaScript
3. WHEN handling user interactions THEN the system SHALL rely on HTMX for server communication
4. WHEN managing state THEN the system SHALL use Alpine.js for minimal client-side reactivity
5. WHEN debugging issues THEN the system SHALL provide clear error messages in Django logs

### Requirement 5

**User Story:** As a user, I want optimal performance with minimal network requests, so that the reading experience is fast and responsive.

#### Acceptance Criteria

1. WHEN loading an article page THEN the system SHALL make only 1 initial request
2. WHEN initializing speed reader THEN the system SHALL make only 1 setup request
3. WHEN reading a 100-word article THEN the system SHALL make 0 additional requests during reading
4. WHEN completing reading THEN the system SHALL make only 1 completion request
5. WHEN taking a quiz THEN the system SHALL make maximum 2 requests (init + submit)

### Requirement 6

**User Story:** As a user with purchased power-ups, I want all my features to work seamlessly in the new architecture, so that I don't lose any functionality I've paid for.

#### Acceptance Criteria

1. WHEN I have word chunking power-ups THEN the system SHALL group words according to my purchased level
2. WHEN I have font customization THEN the system SHALL apply my preferred fonts and styling
3. WHEN I have smart connector grouping THEN the system SHALL intelligently group small words
4. WHEN I have quiz hints THEN the system SHALL provide contextual help during quizzes
5. WHEN I have extended time THEN the system SHALL apply appropriate time limits

### Requirement 7

**User Story:** As a user, I want the system to work progressively, so that core functionality is available even if JavaScript fails to load.

#### Acceptance Criteria

1. WHEN JavaScript is disabled THEN the system SHALL display article content in readable format
2. WHEN HTMX fails to load THEN the system SHALL provide fallback form submissions
3. WHEN Alpine.js is unavailable THEN the system SHALL maintain basic interactivity
4. WHEN network is slow THEN the system SHALL show loading states and graceful degradation
5. WHEN errors occur THEN the system SHALL display helpful error messages to users

### Requirement 8

**User Story:** As a system administrator, I want comprehensive logging and monitoring, so that I can track system performance and debug issues effectively.

#### Acceptance Criteria

1. WHEN users interact with speed reader THEN the system SHALL log reading sessions and completion rates
2. WHEN quiz submissions occur THEN the system SHALL track response times and success rates
3. WHEN errors happen THEN the system SHALL log detailed error information with context
4. WHEN performance issues arise THEN the system SHALL provide metrics on response times
5. WHEN debugging THEN the system SHALL offer clear stack traces and request information