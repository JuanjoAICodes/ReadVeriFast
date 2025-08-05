# Speed Reader Single-Mode Architecture Specification

*Last Updated: July 28, 2025*  
*Status: DEFINITIVE SPECIFICATION*  
*Version: 2.0 - Single Immersive Mode*

## CRITICAL: ARCHITECTURAL DECISION

**This document establishes the definitive architecture for VeriFast Speed Reader. Any future refactoring MUST follow this specification.**

### Single-Mode Design Decision
- **REMOVED**: Traditional inline speed reader interface
- **PRIMARY**: Full-screen immersive mode is the ONLY speed reading interface
- **SIMPLIFIED**: Single "Start Reading" button launches immersive mode directly
- **NO FALLBACK**: No dual-mode or optional regular mode

## Interface Specifications

### 1. Immersive Mode as Primary Interface

**Design Requirements:**
```
┌─────────────────────────────────────────────────────────────┐
│                    FULL SCREEN OVERLAY                      │
│                   (Dark Background)                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │              FULL-WIDTH WHITE STRIP                 │    │
│  │                (Side to Side)                       │    │
│  │                                                     │    │
│  │                 CURRENT WORD                        │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│                    [Exit Button]                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Technical Specifications:**
- **Background**: `rgba(0, 0, 0, 0.9)` dark overlay
- **Text Strip**: Full viewport width (`100vw`)
- **Text Color**: `#000000` (black text on white background)
- **Font Size**: `4rem` for optimal readability
- **Strip Height**: `200px` fixed height
- **Strip Background**: `#ffffff` (pure white)
- **Border**: `3px solid #333333` for definition
- **Position**: Centered vertically and horizontally

### 2. User Flow Specification

**Single-Button Activation:**
```
Article Page → [Start Reading] → Immersive Mode → Reading Complete → Quiz Unlock
```

**NO INTERMEDIATE STEPS:**
- No "regular mode" option
- No "switch to immersive" button
- No dual-interface complexity

### 3. Exit Mechanism

**Exit Button Requirements:**
- **Position**: Bottom center of screen
- **Style**: Primary button styling
- **Text**: "Exit Reading" or "Stop Reading"
- **Keyboard**: Escape key functionality
- **Action**: Return to article page

## Implementation Requirements

### 1. Template Structure

**Required HTML Structure:**
```html
<!-- Article Detail Page -->
<section class="speed-reader-section">
    <h2>Speed Reader</h2>
    <button id="start-reading-btn" class="primary">
        Start Reading
    </button>
</section>

<!-- Immersive Overlay (Hidden by default) -->
<div id="immersive-overlay" class="immersive-overlay">
    <div id="immersive-word-display" class="immersive-word-display">
        <!-- Current word/chunk displayed here -->
    </div>
    <div class="immersive-controls">
        <button id="exit-reading-btn" class="immersive-exit-btn">
            Exit Reading
        </button>
    </div>
</div>
```

### 2. CSS Requirements

**Immersive Overlay Styles:**
```css
.immersive-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.9);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
}

.immersive-overlay.active {
    opacity: 1;
    visibility: visible;
}

.immersive-word-display {
    width: 100vw;                    /* FULL WIDTH - SIDE TO SIDE */
    height: 200px;
    background: #ffffff;             /* WHITE BACKGROUND */
    color: #000000;                  /* BLACK TEXT */
    font-size: 4rem;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 3px solid #333333;
    text-align: center;
    word-wrap: break-word;
    padding: 2rem;
    box-sizing: border-box;
}

.immersive-exit-btn {
    margin-top: 2rem;
    padding: 1rem 2rem;
    font-size: 1.2rem;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
}
```

### 3. JavaScript Requirements

**Single-Mode Speed Reader Class:**
```javascript
class ImmersiveSpeedReader {
    constructor(articleContent, userSettings) {
        this.words = this.processContent(articleContent);
        this.currentIndex = 0;
        this.isRunning = false;
        this.wpm = userSettings.wpm || 250;
        
        // Elements
        this.startBtn = document.getElementById('start-reading-btn');
        this.overlay = document.getElementById('immersive-overlay');
        this.wordDisplay = document.getElementById('immersive-word-display');
        this.exitBtn = document.getElementById('exit-reading-btn');
        
        this.init();
    }
    
    init() {
        this.startBtn.addEventListener('click', () => this.startReading());
        this.exitBtn.addEventListener('click', () => this.exitReading());
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    startReading() {
        this.showImmersiveMode();
        this.beginWordDisplay();
    }
    
    showImmersiveMode() {
        this.overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    exitReading() {
        this.overlay.classList.remove('active');
        document.body.style.overflow = '';
        this.stopWordDisplay();
    }
    
    handleKeyboard(event) {
        if (event.key === 'Escape') {
            this.exitReading();
        }
        if (event.key === ' ' && this.overlay.classList.contains('active')) {
            event.preventDefault();
            this.toggleReading();
        }
    }
}
```

## Migration from Dual-Mode System

### 1. Remove Legacy Components

**Files to Modify:**
- Remove regular speed reader HTML from `article_detail.html`
- Remove regular speed reader CSS classes
- Remove dual-mode JavaScript logic
- Update button text from "Immersive Mode" to "Start Reading"

**Elements to Remove:**
```html
<!-- REMOVE THESE -->
<div class="word-display">...</div>
<div class="speed-controls">...</div>
<button id="immersive-btn">Immersive Mode</button>

<!-- KEEP ONLY -->
<button id="start-reading-btn">Start Reading</button>
```

### 2. Update User Experience

**Before (Dual-Mode):**
1. User sees inline speed reader
2. User can optionally click "Immersive Mode"
3. Two different interfaces to maintain

**After (Single-Mode):**
1. User sees "Start Reading" button
2. Clicking launches full-screen immersive mode immediately
3. Single interface to maintain

### 3. Update Documentation References

**Files to Update:**
- `README.md` - Update speed reader description
- `documentation/MASTER_PRD.md` - Update feature specifications
- `documentation/features/speed-reader.md` - Update technical docs
- All user-facing help text and tooltips

## Quality Assurance Requirements

### 1. Testing Checklist

**Functional Testing:**
- [ ] "Start Reading" button launches immersive mode
- [ ] Full-width white strip displays correctly
- [ ] Text is centered and readable at 4rem
- [ ] Exit button returns to article page
- [ ] Escape key exits immersive mode
- [ ] No regular speed reader interface visible

**Visual Testing:**
- [ ] White strip spans full screen width (side to side)
- [ ] Dark background overlay covers entire viewport
- [ ] Text contrast is optimal (black on white)
- [ ] Exit button is clearly visible and accessible
- [ ] Mobile responsiveness maintained

**Cross-Browser Testing:**
- [ ] Chrome: Full-width display works correctly
- [ ] Firefox: Overlay positioning correct
- [ ] Safari: Font rendering optimal
- [ ] Mobile browsers: Touch interactions work

### 2. Performance Requirements

**Load Time:**
- Immersive mode activation: < 100ms
- Word display updates: < 16ms (60fps)
- Exit transition: < 300ms

**Memory Usage:**
- No memory leaks during extended reading sessions
- Efficient word array processing
- Proper cleanup on exit

## Accessibility Requirements

### 1. Screen Reader Support

**ARIA Labels:**
```html
<button id="start-reading-btn" 
        aria-label="Start immersive speed reading">
    Start Reading
</button>

<div id="immersive-word-display" 
     role="main" 
     aria-live="polite"
     aria-label="Current word display">
</div>

<button id="exit-reading-btn" 
        aria-label="Exit immersive reading mode">
    Exit Reading
</button>
```

### 2. Keyboard Navigation

**Required Shortcuts:**
- `Enter/Space` on "Start Reading" → Launch immersive mode
- `Space` in immersive mode → Toggle play/pause
- `Escape` in immersive mode → Exit to article page
- `Tab` navigation should work before and after immersive mode

### 3. High Contrast Support

**CSS Requirements:**
```css
@media (prefers-contrast: high) {
    .immersive-word-display {
        background: #ffffff;
        color: #000000;
        border: 5px solid #000000;
    }
}

@media (prefers-reduced-motion: reduce) {
    .immersive-overlay {
        transition: none;
    }
}
```

## Error Handling Specifications

### 1. Graceful Degradation

**No JavaScript Fallback:**
```html
<noscript>
    <div class="speed-reader-fallback">
        <p>Speed reading requires JavaScript. You can read the article normally below:</p>
        <div class="article-content">{{ article.content }}</div>
    </div>
</noscript>
```

### 2. Error States

**Content Loading Errors:**
- Display "Unable to load content" in word display
- Provide "Try Again" button
- Log errors for debugging

**Browser Compatibility:**
- Detect fullscreen API support
- Fallback for older browsers
- Progressive enhancement approach

## Deployment Checklist

### 1. Pre-Deployment

- [ ] Remove all dual-mode code references
- [ ] Update all documentation
- [ ] Test on staging environment
- [ ] Verify mobile responsiveness
- [ ] Check accessibility compliance

### 2. Post-Deployment

- [ ] Monitor user feedback
- [ ] Track usage analytics
- [ ] Verify performance metrics
- [ ] Check error logs
- [ ] Validate cross-browser functionality

## Future Considerations

### 1. Potential Enhancements

**Within Single-Mode Framework:**
- Enhanced keyboard shortcuts
- Reading progress indicators
- Customizable text strip width (while maintaining full-width default)
- Advanced typography options

**Explicitly NOT Planned:**
- Return to dual-mode system
- Optional regular speed reader
- Inline reading interface

### 2. Maintenance Guidelines

**Code Organization:**
- Keep immersive mode logic in single file
- Maintain clear separation of concerns
- Document any changes to this specification
- Update tests when modifying functionality

## Conclusion

This specification establishes the single immersive mode as the definitive speed reading interface for VeriFast. Any future development, refactoring, or enhancement MUST adhere to these requirements to maintain consistency and user experience quality.

**Key Principles:**
1. **Simplicity**: One interface, one user flow
2. **Focus**: Full-screen immersive experience
3. **Accessibility**: WCAG AA compliance
4. **Performance**: Smooth, responsive interactions
5. **Maintainability**: Clean, documented code

---

*This specification is the authoritative reference for VeriFast Speed Reader architecture. All implementation decisions should align with these requirements.*
