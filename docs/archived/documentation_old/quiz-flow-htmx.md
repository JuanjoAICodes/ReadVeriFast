# HTMX Quiz Flow (Standard)

The legacy modal-based quiz and quiz-handler.js have been removed from article pages. The standardized quiz implementation uses HTMX endpoints and server-rendered partials.

Flow overview
- Reading: On article_detail.html, the Speed Reader is loaded via HTMX:
  - Button with hx-get to speed_reader_init -> returns partial speed_reader_active.html.
  - When reading finishes, speed_reader_active dispatches a `readingComplete` event -> hx-post to speed_reader_complete.
  - speed_reader_complete renders quiz_unlock.html (includes a Start Quiz button).

- Start Quiz: The Start Quiz button uses HTMX to GET quiz_start (QuizStartView) which renders quiz_interface.html.

- Quiz Interface:
  - quiz_interface.html renders one question at a time with Alpine.js for navigation.
  - Progress bar shows completion percent; a review step appears after the last question; Submit button is disabled until all questions answered.
  - The form posts via HTMX to quiz_submit_api (QuizSubmissionAPIView) with CSRF header.

- Results:
  - For HTMX requests, quiz_submit_api returns quiz_results.html which shows the score, XP earned, and optional feedback.
  - If passed (>=60%), response includes HX-Trigger {"quiz-passed": true} so the comments section can refresh.

Developer notes
- Alpine initialization after HTMX swaps is handled globally in base.html via htmx.onLoad/afterSwap.
- quiz-handler.js is deprecated and removed from templates; do not re-add it.
- To extend quiz logic, update:
  - QuizStartView in verifast_app/views.py for parsing and normalizing quiz data.
  - QuizSubmissionAPIView for grading logic and XP handling.
  - quiz_interface.html and quiz_results.html for frontend presentation.

Testing
- test_quiz_api.py checks that article pages contain the HTMX Start Quiz hooks and can submit to /en/api/quiz/submit/.
- test_end_to_end_functionality.py looks for HTMX markers instead of the legacy modal.
