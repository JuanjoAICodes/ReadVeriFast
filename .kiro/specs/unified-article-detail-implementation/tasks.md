# Implementation Plan

This implementation follows the established working specifications from the documentation architecture files as the definitive reference.

- [x] 1. Implement Article Header Section per Complete Spec
  - Create comprehensive article header with all metadata fields as specified
  - Implement responsive image display (left-aligned, max 300px width)
  - Add automatic word count and reading level calculations in ArticleDetailView
  - Include language badge, Wikipedia indicator, and publication date display
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement Tags Section per Complete Spec
  - Display all article tags as clickable links to tag detail pages
  - Show "No tags available" message when no tags exist
  - Implement responsive tag layout with proper styling
  - Ensure tag links use `tag.get_absolute_url()` method
  - _Requirements: 1.4, 1.5_

- [x] 3. Implement Single Immersive Mode Speed Reader per Single-Mode Spec
  - [x] 3.1 Create HTMX Speed Reader Initialization Endpoint
    - Implement `speed_reader_init` view with server-side content processing
    - Process article content with user power-ups on server
    - Return `speed_reader_active.html` partial with word chunks JSON
    - Include user WPM settings and article metadata
    - _Requirements: 2.1, 3.1_
  
  - [x] 3.2 Create Immersive Overlay Interface per Single-Mode Spec
    - Implement full-screen overlay with `rgba(0, 0, 0, 0.9)` background
    - Create full-width white text strip (`100vw` width, `200px` height)
    - Use `4rem` font size with black text on white background
    - Add `3px solid #333333` border as specified
    - _Requirements: 2.2, 2.3_
  
  - [x] 3.3 Implement Speed Reader Controls per Single-Mode Spec
    - Add play/pause toggle button with visual feedback
    - Implement speed adjustment controls (50-1000 WPM range)
    - Create exit button with "Exit Reading" text
    - Add Escape key functionality for exit
    - _Requirements: 2.4, 2.5_
  
  - [x] 3.4 Create Alpine.js Component per HTMX Hybrid Architecture
    - Implement speedReader Alpine component (max 30 lines)
    - Support function-style initialization with parameters
    - Handle word-by-word progression with timer management
    - Implement proper cleanup on exit
    - _Requirements: 3.2, 3.3_

- [x] 4. Implement Reading Completion and Quiz Unlock per Complete Spec
  - Create `speed_reader_complete` HTMX endpoint
  - Award reading XP and update user statistics
  - Unlock quiz interface via HTMX response
  - Handle both authenticated and anonymous users
  - _Requirements: 2.6, 4.1_

- [x] 5. Implement Quiz Section per Complete Spec
  - [x] 5.1 Create Quiz Interface with HTMX Integration
    - Implement `quiz_start` HTMX endpoint
    - Display quiz interface only after reading completion
    - Show "Quiz is being generated" when quiz_data is missing
    - Handle quiz state management via server-side processing
    - _Requirements: 4.2, 4.3_
  
  - [x] 5.2 Implement Quiz Submission and XP Awards
    - Process quiz answers on server with XP calculation
    - Award XP based on score and performance
    - Unlock commenting for passing scores (≥70%)
    - Handle quiz results display via HTMX
    - _Requirements: 4.4, 4.5_

- [x] 6. Implement Social Comments System per Complete Spec
  - [x] 6.1 Create Comment Form with XP Cost Validation
    - Display comment form only for users with passing quiz scores
    - Show XP cost indicator (10 XP for comments)
    - Implement HTMX comment submission
    - Handle authentication state properly
    - _Requirements: 5.1, 5.2_
  
  - [x] 6.2 Implement Comment Interactions (Bronze/Silver/Gold)
    - Add Bronze (5 XP), Silver (15 XP), Gold (30 XP) interaction buttons
    - Process interactions via HTMX with XP deduction
    - Update comment display with interaction counts
    - Handle insufficient XP scenarios gracefully
    - _Requirements: 5.3, 5.4_

- [x] 7. Implement Related Articles Section per Complete Spec
  - Query articles with shared tags (max 6 articles)
  - Create responsive grid layout for article cards
  - Display article images, titles, and metadata
  - Implement "No related articles found" fallback
  - _Requirements: 1.6_

- [x] 8. Implement CSS Styling per Single-Mode Spec Requirements
  - [x] 8.1 Create Immersive Mode Styles per Exact Specifications
    - Implement `.immersive-overlay` with exact positioning and background
    - Create `.immersive-word-display` with full-width specifications
    - Add `.immersive-controls` with proper spacing and layout
    - Include all specified colors, fonts, and dimensions
    - _Requirements: 2.2, 2.3_
  
  - [x] 8.2 Implement Article Detail Page Styles per Complete Spec
    - Create article header grid layout (auto 1fr columns)
    - Implement responsive design with mobile breakpoints
    - Add tag list styling with proper spacing
    - Create related articles grid with hover effects
    - _Requirements: 1.1, 1.4, 1.6_

- [x] 9. Implement Responsive Design per Both Specifications
  - [x] 9.1 Mobile Optimization for Immersive Mode
    - Reduce font size to 2.5rem on mobile (≤768px)
    - Adjust immersive controls for touch interaction
    - Optimize speed controls layout for mobile
    - Ensure exit button is easily accessible
    - _Requirements: 6.2_
  
  - [x] 9.2 Responsive Article Detail Layout
    - Convert article header to single column on mobile
    - Stack related articles grid on small screens
    - Optimize comment form for mobile input
    - Ensure all touch targets meet accessibility standards
    - _Requirements: 6.1, 6.2_

- [x] 10. Final Integration and Testing
  - [x] 10.1 Integrate All Components
    - Ensure seamless flow between all sections
    - Validate HTMX endpoint connectivity
    - Test complete user journey from article to comments
    - Verify authentication state handling
    - _Requirements: All integration requirements_
  
  - [x] 10.2 Validate Against Original Specifications
    - Confirm implementation matches Single-Mode Spec exactly
    - Verify Complete Spec requirements are fully met
    - Test all specified user flows and interactions
    - Ensure no deviation from established specifications
    - _Requirements: All specification requirements_

- [ ] 11. Fix Critical Template and Display Issues
  - Fix article information display showing raw template variables
  - Restore professional speed reader section styling
  - Fix template method calls to use correct Article model methods
  - Ensure all context variables are properly passed to template
  - _Requirements: 1.1, 1.2, 2.1_