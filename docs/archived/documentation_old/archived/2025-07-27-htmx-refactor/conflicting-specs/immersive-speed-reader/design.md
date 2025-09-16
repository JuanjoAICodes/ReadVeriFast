# Design Document

## Overview

The immersive speed reader enhancement will transform the existing speed reader into a cinema-like, full-screen reading experience. The design focuses on creating a smooth transition from the normal article view to an immersive overlay that darkens the background and provides a distraction-free reading environment. The key innovation is the "jump forward" animation of the speed reader rectangle that expands into a full-screen overlay.

## Architecture

The enhancement will be implemented as a JavaScript-based overlay system that works with the existing speed reader functionality. The architecture consists of:

1. **Overlay Manager**: Handles the creation, animation, and destruction of the immersive overlay
2. **Animation Controller**: Manages the smooth transition from normal to immersive mode
3. **Display Controller**: Optimizes the word display for full-screen viewing
4. **State Manager**: Preserves reading progress and settings across mode transitions

## Components and Interfaces

### Immersive Overlay Component
- **Purpose**: Create and manage the full-screen reading overlay
- **Functionality**:
  - Generate dark overlay that covers the entire viewport
  - Position word display in the center of the screen
  - Handle responsive layout for different screen sizes
  - Manage z-index layering to ensure proper display hierarchy

### Animation System
- **Purpose**: Provide smooth transitions between normal and immersive modes
- **Functionality**:
  - Animate the speed reader rectangle expansion
  - Fade background elements to secondary focus
  - Scale and position word display for optimal viewing
  - Reverse animations when exiting immersive mode

### Speed Display Enhancement
- **Purpose**: Implement the current/max speed format display
- **Functionality**:
  - Update display format to show "current/max" (e.g., "200/400 WPM")
  - Real-time updates when WPM slider changes
  - Dynamic max speed based on user authentication status
  - Maintain display consistency across mode transitions

### Control System
- **Purpose**: Provide simplified controls in immersive mode
- **Functionality**:
  - Single stop button with prominent positioning
  - Hide secondary controls (WPM slider, reset button)
  - Maintain reading state and progress
  - Handle keyboard shortcuts for accessibility

## Data Models

### Immersive State Model
```javascript
{
  isImmersive: boolean,
  originalPosition: {
    top: number,
    left: number,
    width: number,
    height: number
  },
  currentWord: string,
  wordIndex: number,
  isPlaying: boolean,
  currentWpm: number,
  maxWpm: number
}
```

### Animation Configuration
```javascript
{
  transitionDuration: 300, // milliseconds
  overlayOpacity: 0.9,
  wordDisplayScale: 1.5,
  fadeOutOpacity: 0.3,
  easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
}
```

## Error Handling

- **Browser Compatibility**: Graceful degradation for older browsers without CSS transform support
- **Screen Size Constraints**: Adaptive layout for very small screens or unusual aspect ratios
- **Animation Interruption**: Handle cases where user rapidly toggles between modes
- **State Persistence**: Maintain reading progress if overlay creation fails

## Testing Strategy

### Unit Tests
- Test overlay creation and destruction
- Verify animation timing and smoothness
- Test speed display format updates
- Validate state preservation across transitions

### Integration Tests
- Test with existing speed reader functionality
- Verify compatibility with quiz system
- Test responsive behavior across device sizes
- Validate keyboard navigation and accessibility

### User Experience Tests
- Test animation smoothness on various devices
- Verify readability in immersive mode
- Test ease of entering and exiting immersive mode
- Validate distraction reduction effectiveness

## Implementation Approach

### Phase 1: Speed Display Enhancement
1. Update the speed display format to show "current/max WPM"
2. Implement real-time updates when WPM changes
3. Add dynamic max speed based on user authentication
4. Test display consistency and formatting

### Phase 2: Overlay System
1. Create the immersive overlay HTML structure
2. Implement CSS for full-screen positioning and styling
3. Add dark background overlay with proper opacity
4. Position word display in center with enhanced styling

### Phase 3: Animation Implementation
1. Create smooth transition animations using CSS transforms
2. Implement the "jump forward" effect for the speed reader rectangle
3. Add fade effects for background elements
4. Optimize animation performance and timing

### Phase 4: Control System
1. Implement single stop button in immersive mode
2. Hide secondary controls during immersive reading
3. Add keyboard shortcuts for accessibility
4. Ensure proper state management across transitions

### Phase 5: Integration and Polish
1. Integrate with existing speed reader functionality
2. Test across different browsers and devices
3. Optimize performance and smooth out any animation issues
4. Add final polish and user experience improvements

## Technical Specifications

### CSS Requirements
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
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.immersive-word-display {
  font-size: 4rem;
  color: white;
  text-align: center;
  font-weight: bold;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
}

.background-fade {
  opacity: 0.3;
  transition: opacity 0.3s ease;
}
```

### JavaScript Architecture
- Use modern ES6+ features with fallbacks for older browsers
- Implement event delegation for efficient event handling
- Use requestAnimationFrame for smooth animations
- Maintain separation of concerns between animation, state, and display logic

## Responsive Design Considerations

### Mobile Devices
- Adjust font sizes for smaller screens
- Optimize touch targets for stop button
- Handle orientation changes gracefully
- Ensure readability on various screen densities

### Desktop
- Utilize full screen real estate effectively
- Support keyboard navigation
- Optimize for various screen resolutions
- Maintain aspect ratio considerations

### Accessibility
- Ensure proper ARIA labels for screen readers
- Support keyboard navigation throughout
- Maintain sufficient color contrast
- Provide alternative text for visual elements

## Performance Considerations

- Use CSS transforms instead of changing layout properties for animations
- Implement efficient DOM manipulation to minimize reflows
- Optimize overlay creation to avoid blocking the main thread
- Use passive event listeners where appropriate
- Implement proper cleanup to prevent memory leaks