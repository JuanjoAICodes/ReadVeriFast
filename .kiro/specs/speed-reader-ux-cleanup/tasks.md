# Speed Reader UX Cleanup Implementation Tasks

## Implementation Plan

- [x] 1. Simplify Speed Reader Interface on Article Page
  - Remove word chunking controls from article detail template
  - Remove font selection dropdown from article page
  - Remove smart feature checkboxes from article page
  - Remove dark mode toggle from article page
  - Keep only essential controls: word display, start/pause/reset, speed control
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Replace Speed Slider with +/- Buttons
  - Remove WPM range slider from article template
  - Add speed decrease button (-) with 5 WPM decrement
  - Add speed increase button (+) with 5 WPM increment
  - Add current speed display between buttons
  - Update JavaScript to handle button clicks instead of slider input
  - Ensure speed changes apply immediately to running reader
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 3. Convert Article Content Button to Direct Link
  - Change the "View Original Article" button to an `<a>` tag that links directly to the article's source URL.
  - The link should open in a new tab.
  - Remove the now-unused hidden `div` containing the article content and the associated show/hide JavaScript.
  - _Requirements: 3.1, 3.2_

- [x] 4. Implement Frontend Quiz Modal and Logic
  - Create a full-screen modal for the quiz interface.
  - On "Start Quiz" click, launch the modal and display the first question from the `quizData` JSON object.
  - Implement question navigation (Next/Previous).
  - Track user's selected answers for each question.
  - On quiz completion, send the user's answers to the backend API endpoint for grading.
  - Display the final score and XP awarded to the user in the modal.
  - Add a "Close" button to dismiss the modal.
  - _Requirements: 3.3, 3.4_

- [x] 5. Implement Backend Quiz Submission API Endpoint
  - Create a new Django view to handle POST requests for quiz submissions.
  - Receive user answers, article ID, WPM, and time data.
  - Grade the quiz by comparing user answers to correct answers in `article.quiz_data`.
  - Calculate score and XP earned based on quiz performance.
  - Create a `QuizAttempt` record in the database.
  - Return a JSON response with the quiz results (score, XP, messages).
  - _Requirements: 3.3, 3.4_

- [x] 6. Update Quiz Unlock Logic for Dual Access
  - Modify article view logic to track original article access
  - Update quiz eligibility to accept either speed reader OR original article access
  - Add session/database tracking for article access method
  - Ensure quiz button shows when either condition is met
  - Test both unlock paths thoroughly
  - _Requirements: 3.3, 3.4_

- [x] 7. Move Power-Up Settings to Profile Page
  - Add reading preferences section to user profile template
  - Move word chunking controls to profile page
  - Move font selection to profile page
  - Move smart feature toggles to profile page
  - Move dark mode toggle to profile page
  - Create organized sections for different preference types
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 8. Implement Profile Settings Form Handling
  - Add reading preferences form to UserProfileForm
  - Handle form submission for all power-up settings
  - Save preferences to user model fields
  - Add form validation for preference inputs
  - Provide user feedback on successful settings save
  - Test all preference saving and loading
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 9. Update Speed Reader JavaScript for Profile Settings
  - Modify speed reader to load user preferences from context
  - Remove preference controls from article page JavaScript
  - Ensure settings from profile are applied automatically
  - Update chunking, font, and smart feature application
  - Test that profile settings work correctly in speed reader
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 10. Enhance Profile Page UI for Settings
  - Design clean, organized layout for reading preferences
  - Group related settings into logical sections
  - Add helpful descriptions and tooltips
  - Implement responsive design for mobile devices
  - Add visual indicators for premium vs free features
  - Test profile page usability and organization
  - _Requirements: 2.1, 2.4_

- [x] 11. Update Article Page Styling and Layout
  - Clean up article page layout after control removal
  - Improve speed reader visual prominence
  - Style the +/- speed buttons attractively
  - Ensure responsive design still works properly
  - Test visual hierarchy and user focus
  - _Requirements: 1.1, 1.3, 1.4_

- [x] 12. Test Complete User Experience Flow
  - Test simplified article reading experience
  - Verify profile settings work across all articles
  - Test both speed reader and original article quiz unlock paths
  - Ensure no functionality is lost in simplification
  - Test on multiple devices and screen sizes
  - Validate user experience improvements
  - _Requirements: All requirements validation_