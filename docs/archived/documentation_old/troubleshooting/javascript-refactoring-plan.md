# JavaScript Refactoring Plan for HTMX Compliance

## Current Violations
- `speed-reader.js`: 190 lines (exceeds 50-line limit)
- `quiz-handler.js`: 253 lines (exceeds 50-line limit)

## Recommended Solutions

### Option 1: Move Logic to Server-Side (Preferred)
1. **Speed Reader**: Convert to HTMX endpoints
   - `/speed-reader/next-word/<article_id>/` - Get next word
   - `/speed-reader/adjust-speed/<article_id>/` - Adjust WPM
   - `/speed-reader/complete/<article_id>/` - Mark reading complete

2. **Quiz Handler**: Convert to HTMX endpoints
   - `/quiz/question/<article_id>/<question_num>/` - Get question HTML
   - `/quiz/submit/<article_id>/` - Submit and get results HTML

### Option 2: Split into Minimal Alpine.js Components
1. **speed-reader-minimal.js** (< 50 lines)
   - Basic word display and timing only
   - Server handles content processing

2. **quiz-minimal.js** (< 50 lines)
   - Basic navigation and form handling
   - Server handles scoring and results

### Option 3: Inline JavaScript in Templates
- Move critical JavaScript directly into templates
- Use Alpine.js x-data for component state
- Keep external files under 50 lines

## Implementation Priority
1. Fix CSRF tokens (✅ Complete)
2. Refactor speed reader to HTMX endpoints
3. Refactor quiz handler to HTMX endpoints
4. Update documentation

## Timeline
- Week 1: Speed reader refactoring
- Week 2: Quiz handler refactoring  
- Week 3: Testing and documentation updates