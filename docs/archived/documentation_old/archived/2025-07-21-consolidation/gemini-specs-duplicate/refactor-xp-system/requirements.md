**Feature: Refactor XP and Gamification Logic**

*   **User Story:** As a developer, I want to centralize all XP and gamification logic into the new `xp_system.py` module so that the codebase is cleaner, more maintainable, and ready for the implementation of the Enhanced XP Economics System.

**Acceptance Criteria (EARS):**

*   WHEN a user submits a quiz
    *   THE SYSTEM SHALL use the `QuizResultProcessor.process_quiz_completion` function to calculate XP and update user stats.
*   WHEN a user's quiz submission results in a new WPM record
    *   THE SYSTEM SHALL correctly update the user's `max_wpm` via the `XPCalculationEngine`.
*   WHEN a user's quiz submission is a perfect score
    *   THE SYSTEM SHALL grant the "free comment" privilege for that article.
*   WHEN a user posts a new comment or a reply
    *   THE SYSTEM SHALL use the `SocialInteractionManager.post_comment` function to handle the action and deduct spendable XP (`current_xp_points`).
*   WHEN a user interacts with a comment (Bronze, Silver, Gold)
    *   THE SYSTEM SHALL use the `SocialInteractionManager.add_interaction` function to process the interaction, deduct spendable XP, and award XP to the comment's author.
*   WHEN any XP is earned or spent
    *   THE SYSTEM SHALL create a corresponding record in the `XPTransaction` model.
*   WHEN the legacy `gamification.py` module is called
    *   THE SYSTEM SHALL log a deprecation warning (initially), and the calls shall be removed.