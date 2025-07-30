# Dependency Restoration Requirements

## Introduction

The VeriFast application currently has several critical AI and NLP features disabled due to dependency conflicts. This spec addresses the restoration of full functionality by resolving compatibility issues with external libraries including Google Generative AI, spaCy NLP processing, Wikipedia API integration, and article scraping capabilities.

## Requirements

### Requirement 1: Google Generative AI Integration

**User Story:** As a user, I want the system to generate intelligent quizzes from articles so that I can test my comprehension and earn XP through the gamification system.

#### Acceptance Criteria

1. WHEN an article is processed THEN the system SHALL successfully connect to Google Generative AI API
2. WHEN the API is called THEN the system SHALL generate quiz data with multiple choice questions
3. WHEN quiz generation fails THEN the system SHALL log appropriate error messages and set article status to "failed"
4. WHEN the API key is missing THEN the system SHALL provide clear configuration guidance
5. IF protobuf dependency conflicts exist THEN the system SHALL resolve them without breaking other functionality

### Requirement 2: Natural Language Processing Restoration

**User Story:** As a system administrator, I want NLP entity extraction to work properly so that articles can be automatically tagged with relevant people, organizations, and concepts.

#### Acceptance Criteria

1. WHEN an article is processed THEN the system SHALL extract named entities using spaCy
2. WHEN entities are found THEN the system SHALL categorize them as PERSON, ORG, or other relevant types
3. WHEN numpy conflicts occur THEN the system SHALL resolve them while maintaining compatibility
4. WHEN spaCy models are missing THEN the system SHALL provide clear installation instructions
5. IF language detection is needed THEN the system SHALL support both English and Spanish processing

### Requirement 3: Wikipedia API Integration

**User Story:** As a content curator, I want the system to validate and enrich tags using Wikipedia so that articles have accurate, canonical entity references.

#### Acceptance Criteria

1. WHEN entities are extracted THEN the system SHALL validate them against Wikipedia
2. WHEN Wikipedia pages exist THEN the system SHALL use canonical titles for tag creation
3. WHEN requests library conflicts occur THEN the system SHALL resolve compatibility issues
4. WHEN Wikipedia API calls fail THEN the system SHALL implement proper retry logic with exponential backoff
5. IF duplicate entities are found THEN the system SHALL deduplicate using canonical names

### Requirement 4: Article Scraping Functionality

**User Story:** As a user, I want to submit article URLs and have them automatically scraped and processed so that I can practice speed reading on web content.

#### Acceptance Criteria

1. WHEN a URL is submitted THEN the system SHALL scrape the article content using newspaper3k
2. WHEN scraping succeeds THEN the system SHALL extract title, content, and metadata
3. WHEN newspaper3k conflicts occur THEN the system SHALL resolve requests library compatibility
4. WHEN scraping fails THEN the system SHALL provide meaningful error messages to users
5. IF duplicate URLs are submitted THEN the system SHALL detect and prevent duplicate processing

### Requirement 5: Dependency Management and Cleanup

**User Story:** As a developer, I want a clean, minimal dependency list with compatible versions so that the application runs reliably without bloat.

#### Acceptance Criteria

1. WHEN requirements.txt is cleaned THEN it SHALL contain only essential packages (under 30 total)
2. WHEN dependencies are installed THEN all libraries SHALL be compatible with each other
3. WHEN the application starts THEN no import errors SHALL occur
4. WHEN version conflicts exist THEN specific compatible versions SHALL be pinned
5. IF development dependencies are needed THEN they SHALL be separated from production requirements

**Critical Issues Identified:**
- Current requirements.txt has 320+ packages (should be ~25)
- Missing numpy and spacy (causing NLP failures)
- requests==2.32.3 conflicts with newspaper3k
- protobuf==5.29.5 conflicts with Google AI
- Contains system packages and unrelated development tools

### Requirement 6: Error Handling and Logging

**User Story:** As a system administrator, I want comprehensive error handling and logging so that I can troubleshoot dependency issues effectively.

#### Acceptance Criteria

1. WHEN dependency errors occur THEN the system SHALL log detailed error information
2. WHEN services are temporarily disabled THEN users SHALL receive informative messages
3. WHEN API quotas are exceeded THEN the system SHALL handle graceful degradation
4. WHEN network issues occur THEN the system SHALL implement appropriate retry mechanisms
5. IF critical services fail THEN the system SHALL continue operating with reduced functionality

### Requirement 7: Configuration Management

**User Story:** As a system administrator, I want clear configuration options so that I can properly set up API keys and service endpoints.

#### Acceptance Criteria

1. WHEN API keys are required THEN the system SHALL provide clear configuration documentation
2. WHEN environment variables are missing THEN the system SHALL show helpful error messages
3. WHEN services are optional THEN the system SHALL allow graceful degradation
4. WHEN configuration changes THEN the system SHALL not require full restart
5. IF multiple environments exist THEN configuration SHALL be environment-specific

### Requirement 8: Testing and Validation

**User Story:** As a developer, I want comprehensive tests for all restored functionality so that regressions can be prevented.

#### Acceptance Criteria

1. WHEN dependencies are restored THEN unit tests SHALL verify functionality
2. WHEN API integrations work THEN integration tests SHALL validate end-to-end flows
3. WHEN mocking is needed THEN tests SHALL not depend on external services
4. WHEN edge cases occur THEN tests SHALL cover error scenarios
5. IF performance matters THEN tests SHALL validate response times