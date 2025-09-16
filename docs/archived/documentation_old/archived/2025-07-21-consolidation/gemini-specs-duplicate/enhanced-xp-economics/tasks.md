**TASK-001: Update XP Calculation Logic** \[PENDING]
*   **Description:** Modify the `XPCalculationEngine.calculate_quiz_xp` method in `xp_system.py` to include the perfect score (25%) and WPM improvement (50 XP) bonuses.
*   **Expected Outcome:** The function returns a dictionary containing the correct total XP and a breakdown of all applied bonuses.
*   **Dependencies:** None

**TASK-002: Update Social Interaction Costs** \[PENDING]
*   **Description:** In `xp_system.py`, update the `SocialInteractionManager.INTERACTION_COSTS` dictionary with the new values (Bronze: 5, Silver: 15, Gold: 30).
*   **Expected Outcome:** The `add_interaction` method uses the new, lower costs for processing interactions.
*   **Dependencies:** None

**TASK-003: Implement Feature Store UI in Profile** \[PENDING]
*   **Description:** Add the "Premium Feature Store" to the `user_profile.html` template. This includes fetching the feature list in the `UserProfileView` and rendering it.
*   **Expected Outcome:** The user profile page displays a list of available features, their costs, and their current ownership status ("Owned" or "Purchase").
*   **Dependencies:** None

**TASK-004: Implement AJAX Purchase Logic** \[PENDING]
*   **Description:** Write the JavaScript in the profile template to handle the "Purchase" button clicks. It should make an AJAX `POST` request to the `/purchase-feature/` endpoint.
*   **Expected Outcome:** Clicking "Purchase" sends the correct feature key to the backend. The frontend updates the UI (button state, XP balance) based on the JSON response.
*   **Dependencies:** TASK-003

**TASK-005: Integrate Owned Features into Speed Reader** \[PENDING]
*   **Description:** In `ArticleDetailView`, pass the user's owned features into the template context. Modify the speed reader's JavaScript in `article_detail.html` to read these context variables.
*   **Expected Outcome:** The speed reader UI dynamically adapts. For example, the "3-word chunking" option in the dropdown is only enabled if `user_owns_3_word_chunking` is true.
*   **Dependencies:** TASK-004

**TASK-006: Implement Smart Symbol Handling in JS** \[PENDING]
*   **Description:** Add a new JavaScript function to the speed reader that processes the word list to handle smart symbols if the user owns the feature.
*   **Expected Outcome:** When enabled, punctuation like `(` `)` `"` appears at the edge of the word box, not attached to the word.
*   **Dependencies:** TASK-005

**TASK-007: Implement Perfect Score UI** \[PENDING]
*   **Description:** In the quiz results section of `article_detail.html`, add a new display area that is shown only when the user gets a perfect score.
*   **Expected Outcome:** A 100% score displays the encouraging message and the two recommended articles (next similar, random unread) with links.
*   **Dependencies:** TASK-001

**TASK-008: Verify Free Comment Privilege** \[PENDING]
*   **Description:** Ensure the `post_comment` logic in `ArticleDetailView` correctly checks for the perfect score privilege and passes the `is_perfect_score_free` flag to the `SocialInteractionManager`.
*   **Expected Outcome:** A user who scored 100% on a quiz is not charged any XP for their next comment on that article.
*   **Dependencies:** TASK-001