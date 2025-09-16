**Feature: Enhanced XP Economics System**

*   **Epic:** As a user, I want a richer gamification experience where I can earn XP in more complex ways and spend it on meaningful features to enhance my reading.

**Acceptance Criteria (EARS):**

**Premium Feature Store:**
*   WHEN a user navigates to their profile
    *   THE SYSTEM SHALL display a "Premium Feature Store" section.
*   WHEN a user views the feature store
    *   THE SYSTEM SHALL list all available premium features (e.g., fonts, word chunking levels, smart symbol handling).
*   WHEN a user attempts to purchase a feature they cannot afford
    *   THE SYSTEM SHALL display a message indicating insufficient spendable XP.
*   WHEN a user has sufficient spendable XP and purchases a feature
    *   THE SYSTEM SHALL deduct the correct amount of `current_xp_points`.
    *   THE SYSTEM SHALL create an `XPTransaction` record for the purchase.
    *   THE SYSTEM SHALL create a `FeaturePurchase` record.
    *   THE SYSTEM SHALL update the corresponding boolean field on the `CustomUser` model (e.g., `has_font_opendyslexic` = True).
    *   THE SYSTEM SHALL prevent the user from purchasing the same feature again.

**Enhanced Speed Reader Features:**
*   WHEN a user has purchased a premium font
    *   THE SYSTEM SHALL make that font selectable in the speed reader interface.
*   WHEN a user has purchased a specific word chunking level (e.g., 3-word chunking)
    *   THE SYSTEM SHALL allow the user to select that chunking level in the speed reader.
*   WHEN a user has purchased "Smart Symbol Handling"
    *   THE SYSTEM SHALL correctly display punctuation at the edges of the word box and remove in-word hyphens during speed reading.

**Advanced XP Calculation:**
*   WHEN a user completes a quiz with a passing score (>=60%)
    *   THE SYSTEM SHALL calculate the XP reward based on the complex formula involving text complexity, WPM, and score percentage.
*   WHEN a user achieves a new personal best WPM on a successful quiz
    *   THE SYSTEM SHALL award a "WPM Improvement" bonus of 50 XP.
*   WHEN a user achieves a perfect score (100%) on a quiz
    *   THE SYSTEM SHALL award a "Perfect Score Bonus" of 25% of the base XP.

**Perfect Score Privileges:**
*   WHEN a user achieves a perfect score on a quiz
    *   THE SYSTEM SHALL allow them to post one comment on that article for free (0 XP cost).
*   WHEN a user achieves a perfect score on a quiz
    *   THE SYSTEM SHALL display an encouraging message and two article recommendations: one with similar tags and one random unread article.

**Refined Social Economy:**
*   WHEN a user gives a "Bronze" interaction
    *   THE SYSTEM SHALL deduct 5 spendable XP.
*   WHEN a user gives a "Silver" interaction
    *   THE SYSTEM SHALL deduct 15 spendable XP.
*   WHEN a user gives a "Gold" interaction
    *   THE SYSTEM SHALL deduct 30 spendable XP.
*   WHEN a user's comment receives a Bronze, Silver, or Gold interaction
    *   THE SYSTEM SHALL award the comment's author 50% of the XP cost as spendable XP.
    *   THE SYSTEM SHALL generate a notification for the author.