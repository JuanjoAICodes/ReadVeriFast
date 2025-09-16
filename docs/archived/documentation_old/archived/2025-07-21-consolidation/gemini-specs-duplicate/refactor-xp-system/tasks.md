**TASK-001: Refactor Quiz Submission in `ArticleDetailView`** \[PENDING]

*   **Description:** Modify the `post` method in `verifast_app.views.ArticleDetailView` to use the new XP system for quiz submissions.
*   **Expected Outcome:**
    *   The view creates a `QuizAttempt` object.
    *   It calls `QuizResultProcessor.process_quiz_completion` with the required objects.
    *   It uses the returned data to display appropriate messages to the user.
    *   The old `calculate_xp_reward` and `update_user_stats_after_quiz` calls from `gamification.py` are removed.
*   **Dependencies:** None

**TASK-002: Refactor Comment Posting in `ArticleDetailView`** \[PENDING]

*   **Description:** Modify the `post` method in `verifast_app.views.ArticleDetailView` to use the `SocialInteractionManager` for posting comments.
*   **Expected Outcome:**
    *   The view calls `SocialInteractionManager.post_comment`.
    *   It correctly handles the `is_perfect_score_free` privilege.
    *   It catches `InsufficientXPError` and displays a user-friendly error message.
    *   The old `post_comment` call from `gamification.py` is removed.
*   **Dependencies:** TASK-001

**TASK-003: Refactor Comment Interaction in `CommentInteractView`** \[PENDING]

*   **Description:** Modify the `post` method in `verifast_app.views.CommentInteractView` to use the `SocialInteractionManager`.
*   **Expected Outcome:**
    *   The view calls `SocialInteractionManager.add_interaction`.
    *   It correctly handles the logic for deducting XP from the interactor and rewarding the author.
    *   It catches `InsufficientXPError` and displays an appropriate error message.
*   **Dependencies:** None

**TASK-004: Refactor Quiz Submission in `api_views.py`** \[PENDING]

*   **Description:** Modify the `submit_quiz` function in `verifast_app.api_views` to use the `QuizResultProcessor`.
*   **Expected Outcome:**
    *   The API view creates a `QuizAttempt` object.
    *   It calls `QuizResultProcessor.process_quiz_completion`.
    *   It returns a standardized JSON response based on the data from the processor.
    *   All legacy XP calculation logic is removed.
*   **Dependencies:** None

**TASK-005: Refactor Commenting in `api_views.py`** \[PENDING]

*   **Description:** Modify `post_article_comment` and `interact_with_comment_view` in `verifast_app.api_views` to use the `SocialInteractionManager`.
*   **Expected Outcome:**
    *   The API views correctly call `SocialInteractionManager.post_comment` and `SocialInteractionManager.add_interaction`.
    *   They handle success and error cases (`InsufficientXPError`) by returning appropriate standardized JSON responses.
    *   Legacy logic is removed.
*   **Dependencies:** None

**TASK-006: Deprecate `gamification.py`** \[PENDING]

*   **Description:** Once all calls to `gamification.py` have been removed, delete the file.
*   **Expected Outcome:** The file `verifast_app/gamification.py` is removed from the project.
*   **Dependencies:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005