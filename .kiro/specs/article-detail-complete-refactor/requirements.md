# Article Detail Page Complete Refactor - Requirements

*Last Updated: July 28, 2025*  
*Status: CRITICAL REFACTOR REQUIRED*

## Introduction

The current article detail page has significant architectural violations and missing features. This refactor will implement the complete HTMX hybrid architecture with all required functionality as specified in the models and documentation.

## Requirements

### Requirement 1: Fix Architecture Violations

**User Story:** As a developer, I want the article detail page to follow the HTMX hybrid architecture, so that the system is maintainable and performant.

#### Acceptance Criteria

1. WHEN implementing speed reader THEN it SHALL use HTMX endpoints with Alpine.js (max 30 lines)
2. WHEN implementing quiz system THEN it SHALL use HTMX for loading and submission
3. WHEN processing content THEN it SHALL be done server-side with user power-ups applied
4. WHEN displaying interactive elements THEN they SHALL use progressive enhancement
5. WHEN handling user interactions THEN they SHALL minimize network requests

### Requirement 2: Implement Missing Article Metadata

**User Story:** As a user, I want to see complete article information including image, reading level, and word count, so that I can make informed reading decisions.

#### Acceptance Criteria

1. WHEN viewing an article THEN it SHALL display the article image if available
2. WHEN viewing an article THEN it SHALL show calculated word count
3. WHEN viewing an article THEN it SHALL show calculated reading level
4. WHEN viewing an article THEN it SHALL display source information properly
5. WHEN viewing an article THEN it SHALL show publication date if available

### Requirement 3: Implement Complete Tags System

**User Story:** As a user, I want to see article tags and navigate to related content, so that I can explore topics of interest.

#### Acceptance Criteria

1. WHEN viewing an article THEN it SHALL display all associated tags
2. WHEN clicking a tag THEN it SHALL navigate to the tag detail page
3. WHEN viewing tags THEN they SHALL be properly styled and responsive
4. WHEN no tags exist THEN it SHALL show appropriate message
5. WHEN tags are Wikipedia-validated THEN they SHALL show validation status

### Requirement 4: Fix Speed Reader with Single Immersive Mode

**User Story:** As a user, I want a streamlined speed reading experience with full-screen immersive mode, so that I can focus on reading without distractions.

#### Acceptance Criteria

1. WHEN clicking "Start Reading" THEN it SHALL launch immersive mode directly
2. WHEN in immersive mode THEN it SHALL display full-width white text strip
3. WHEN reading THEN it SHALL use server-processed content with user power-ups
4. WHEN completing reading THEN it SHALL unlock quiz via HTMX
5. WHEN using keyboard shortcuts THEN they SHALL work in immersive mode

### Requirement 5: Implement Working Quiz System

**User Story:** As a user, I want to take comprehension quizzes after reading, so that I can test my understanding and earn XP.

#### Acceptance Criteria

1. WHEN reading is complete THEN quiz SHALL be unlocked automatically
2. WHEN starting quiz THEN it SHALL load via HTMX with proper interface
3. WHEN answering questions THEN it SHALL track progress and validate answers
4. WHEN submitting quiz THEN it SHALL calculate score and award XP
5. WHEN quiz is complete THEN it SHALL unlock commenting privileges

### Requirement 6: Implement Comments System

**User Story:** As a user, I want to read and write comments on articles, so that I can engage with the community and share insights.

#### Acceptance Criteria

1. WHEN viewing article THEN it SHALL display existing comments in threaded format
2. WHEN quiz is completed THEN commenting SHALL be unlocked
3. WHEN adding comment THEN it SHALL charge appropriate XP cost
4. WHEN viewing comments THEN Bronze/Silver/Gold interaction buttons SHALL be available
5. WHEN interacting with comments THEN XP SHALL be awarded to comment authors

### Requirement 7: Implement Related Articles

**User Story:** As a user, I want to discover related articles based on shared tags, so that I can continue learning about topics of interest.

#### Acceptance Criteria

1. WHEN viewing article THEN it SHALL show articles with shared tags
2. WHEN displaying related articles THEN they SHALL show preview information
3. WHEN clicking related article THEN it SHALL navigate to article detail page
4. WHEN no related articles exist THEN it SHALL show appropriate message
5. WHEN displaying related articles THEN they SHALL be responsive and well-formatted

### Requirement 8: Implement Proper Data Calculations

**User Story:** As a system, I want to automatically calculate article metadata, so that users have accurate information about content difficulty and length.

#### Acceptance Criteria

1. WHEN article is saved THEN word count SHALL be calculated automatically
2. WHEN article is processed THEN reading level SHALL be calculated using Flesch-Kincaid
3. WHEN calculations are missing THEN they SHALL be computed on first view
4. WHEN displaying metrics THEN they SHALL be formatted appropriately
5. WHEN calculations fail THEN appropriate fallbacks SHALL be used

### Requirement 9: Implement Mobile Responsiveness

**User Story:** As a mobile user, I want the article detail page to work perfectly on my device, so that I can read and interact comfortably.

#### Acceptance Criteria

1. WHEN viewing on mobile THEN all sections SHALL be properly responsive
2. WHEN using immersive mode THEN it SHALL work on mobile devices
3. WHEN interacting with elements THEN touch targets SHALL be appropriately sized
4. WHEN viewing images THEN they SHALL scale properly on small screens
5. WHEN using quiz interface THEN it SHALL be mobile-friendly

### Requirement 10: Implement Accessibility Features

**User Story:** As a user with accessibility needs, I want the article detail page to be fully accessible, so that I can use all features regardless of my abilities.

#### Acceptance Criteria

1. WHEN using screen reader THEN all content SHALL be properly announced
2. WHEN navigating with keyboard THEN all interactive elements SHALL be accessible
3. WHEN viewing content THEN proper ARIA labels SHALL be present
4. WHEN using high contrast mode THEN content SHALL remain readable
5. WHEN motion is reduced THEN animations SHALL respect user preferences

## Technical Requirements

### Backend Requirements

1. **View Updates**: ArticleDetailView must calculate missing fields and provide complete context
2. **HTMX Endpoints**: Create endpoints for speed reader init, reading completion, quiz loading, quiz submission
3. **Content Processing**: Implement server-side content processing with user power-ups
4. **XP Integration**: Proper XP calculation and awarding for all interactions
5. **Comment System**: Complete comment CRUD operations with XP validation

### Frontend Requirements

1. **HTMX Integration**: Replace JavaScript-heavy implementations with HTMX
2. **Alpine.js Components**: Minimal Alpine.js for speed reader (max 30 lines)
3. **Progressive Enhancement**: All features work without JavaScript
4. **Responsive Design**: Mobile-first responsive implementation
5. **Accessibility**: WCAG AA compliance

### Database Requirements

1. **Field Calculations**: Automatic word count and reading level calculation
2. **Migration**: Data migration to populate missing fields
3. **Indexing**: Proper database indexes for performance
4. **Relationships**: Correct handling of all model relationships

## Success Criteria

### Functional Success
- All article metadata displays correctly
- Speed reader works with single immersive mode
- Quiz system functions properly with XP awards
- Comments system allows interaction with XP costs
- Related articles display based on shared tags

### Technical Success
- HTMX hybrid architecture implemented correctly
- Alpine.js usage limited to 30 lines for speed reader
- Server-side content processing working
- Mobile responsiveness achieved
- Accessibility standards met

### Performance Success
- Page load time under 2 seconds
- Immersive mode activation under 100ms
- HTMX requests complete under 500ms
- No JavaScript errors in console
- Proper caching implemented

## Risk Mitigation

### Technical Risks
- **Complex Refactor**: Break into small, testable increments
- **HTMX Learning Curve**: Provide clear examples and documentation
- **Data Migration**: Test thoroughly on staging environment
- **Performance Impact**: Monitor and optimize database queries

### User Experience Risks
- **Feature Disruption**: Maintain backward compatibility during transition
- **Mobile Issues**: Test extensively on various devices
- **Accessibility Regression**: Automated accessibility testing
- **Quiz Functionality**: Comprehensive testing of quiz flow

## Dependencies

### Internal Dependencies
- XP system must be working correctly
- Tag system must be properly implemented
- User authentication system must be functional
- Comment system models must be complete

### External Dependencies
- HTMX library integration
- Alpine.js library integration
- Reading level calculation algorithms
- Image processing for article images

## Timeline Considerations

### Phase 1: Foundation (Critical)
1. Fix data calculations (word count, reading level)
2. Implement basic article header with all metadata
3. Add tags display and navigation

### Phase 2: Core Features (High Priority)
1. Implement HTMX speed reader with immersive mode
2. Fix quiz system with HTMX integration
3. Add comments section with XP integration

### Phase 3: Enhancement (Medium Priority)
1. Add related articles section
2. Implement mobile optimizations
3. Add accessibility improvements

### Phase 4: Polish (Low Priority)
1. Performance optimizations
2. Advanced features
3. Additional testing and refinement

This requirements document provides the complete specification for refactoring the article detail page to meet all architectural and functional requirements.