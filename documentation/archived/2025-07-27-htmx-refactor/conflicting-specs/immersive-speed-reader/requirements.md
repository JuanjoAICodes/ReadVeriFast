# Requirements Document

## Introduction

This specification addresses the need to enhance the existing speed reader functionality with an immersive, full-screen reading experience. The current speed reader works well but lacks the focused, distraction-free environment that would optimize the reading experience. We need to implement a full-screen overlay mode that darkens the background and provides a cinema-like reading experience.

## Requirements

### Requirement 1

**User Story:** As a user, I want an immersive full-screen speed reading mode, so that I can focus completely on the text without distractions.

#### Acceptance Criteria

1. WHEN the user starts speed reading THEN the system SHALL create a full-screen overlay that covers the entire viewport
2. WHEN the overlay is active THEN the system SHALL darken the background content to minimize distractions
3. WHEN in immersive mode THEN the system SHALL display only the word display area and essential controls
4. WHEN the user exits immersive mode THEN the system SHALL return to the normal article view seamlessly

### Requirement 2

**User Story:** As a user, I want the speed display to show current/max format, so that I can see both my current reading speed and my maximum achievable speed.

#### Acceptance Criteria

1. WHEN viewing the speed reader THEN the system SHALL display speed in format "current/max" (e.g., "200/400 WPM")
2. WHEN the user adjusts the WPM slider THEN the system SHALL update the current speed number in real-time
3. WHEN the user is authenticated THEN the system SHALL show their personal max WPM from their profile
4. WHEN the user is not authenticated THEN the system SHALL show a default max WPM of 1000

### Requirement 3

**User Story:** As a user, I want simplified controls in immersive mode, so that I can focus on reading without complex interface elements.

#### Acceptance Criteria

1. WHEN in immersive mode THEN the system SHALL display only a single stop button
2. WHEN the stop button is clicked THEN the system SHALL pause reading and exit immersive mode
3. WHEN in immersive mode THEN the system SHALL hide the WPM slider and other secondary controls
4. WHEN in immersive mode THEN the system SHALL maintain the current WPM setting without allowing changes during reading

### Requirement 4

**User Story:** As a user, I want the speed reader rectangle to jump forward and create an immersive experience when I click start, so that I can have a focused reading session.

#### Acceptance Criteria

1. WHEN the user clicks start THEN the speed reader rectangle SHALL expand and jump forward to create a full-screen overlay
2. WHEN the immersive mode activates THEN all page elements SHALL fade to dark/secondary focus
3. WHEN in immersive mode THEN the word display SHALL be prominently centered in the overlay
4. WHEN exiting immersive mode THEN the system SHALL return to the normal article view with preserved reading progress

### Requirement 5

**User Story:** As a user, I want the immersive mode to work consistently across different devices and screen sizes, so that I have a reliable experience regardless of my device.

#### Acceptance Criteria

1. WHEN using immersive mode on mobile devices THEN the system SHALL adapt the layout for smaller screens
2. WHEN using immersive mode on desktop THEN the system SHALL utilize the full screen real estate effectively
3. WHEN the screen orientation changes THEN the system SHALL adjust the layout accordingly
4. WHEN using different browsers THEN the system SHALL maintain consistent functionality and appearance