# Requirements Document

## Introduction

This specification addresses critical UX improvements needed for the speed reader interface. The current article detail page has too many controls cluttering the speed reader experience. We need to simplify the speed reader interface and move power-up settings to the user profile where they belong.

## Requirements

### Requirement 1

**User Story:** As a user, I want a clean, simple speed reader interface, so that I can focus on reading without distractions.

#### Acceptance Criteria

1. WHEN viewing the speed reader THEN only the reading speed control SHALL be visible
2. WHEN adjusting reading speed THEN it SHALL use +/- buttons with 5 WPM increments
3. WHEN using the speed reader THEN all other controls SHALL be moved to the profile page
4. WHEN the interface is clean THEN users SHALL have a better reading experience

### Requirement 2

**User Story:** As a user, I want all my reading preferences in my profile, so that I can manage them in one centralized location.

#### Acceptance Criteria

1. WHEN viewing my profile THEN I SHALL see all power-up settings (chunking, fonts, smart features)
2. WHEN changing settings in profile THEN they SHALL apply to all future reading sessions
3. WHEN on article pages THEN only essential reading controls SHALL be present
4. WHEN managing preferences THEN the experience SHALL be organized and intuitive

### Requirement 3

**User Story:** As a user, I want the full article content hidden by default, so that I'm encouraged to use the speed reader.

#### Acceptance Criteria

1. WHEN viewing an article THEN the full content SHALL be hidden by default
2. WHEN I want to read traditionally THEN there SHALL be a link to view the original article
3. WHEN accessing the original article THEN it SHALL unlock quiz eligibility
4. WHEN using the speed reader THEN it SHALL also unlock quiz eligibility

### Requirement 4

**User Story:** As a user, I want simple speed controls, so that I can quickly adjust my reading pace.

#### Acceptance Criteria

1. WHEN adjusting speed THEN I SHALL use +/- buttons instead of a slider
2. WHEN clicking + THEN speed SHALL increase by 5 WPM
3. WHEN clicking - THEN speed SHALL decrease by 5 WPM  
4. WHEN speed changes THEN it SHALL be immediately applied to the reader