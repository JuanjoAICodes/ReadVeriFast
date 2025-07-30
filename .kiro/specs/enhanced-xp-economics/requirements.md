# Enhanced XP Economics System - Requirements Document

## Introduction

This specification defines an advanced XP (Experience Points) economics system that separates accumulated XP from spendable XP, creating a virtual currency economy within VeriFast. Users earn XP through reading activities and can spend it on premium features, social interactions, and enhanced reading capabilities. This system gamifies the platform while providing monetization opportunities and user engagement incentives.

## Requirements

### Requirement 1: Dual XP System Architecture

**User Story:** As a user, I want to have both accumulated XP (permanent record) and spendable XP (currency), so that I can track my total progress while having points to spend on features.

#### Acceptance Criteria

1. WHEN a user earns XP THEN the system SHALL add points to both total_xp (accumulated) and current_xp_points (spendable)
2. WHEN a user spends XP THEN the system SHALL deduct only from current_xp_points, leaving total_xp unchanged
3. WHEN displaying user stats THEN the system SHALL show both accumulated XP and available spendable XP
4. WHEN a user's spendable XP reaches zero THEN the system SHALL prevent XP-based purchases while maintaining total_xp record
5. WHEN calculating user level/rank THEN the system SHALL use total_xp (accumulated) for progression

### Requirement 2: Premium Speed Reader Features

**User Story:** As a user, I want to purchase enhanced speed reader features with my spendable XP, so that I can customize my reading experience with advanced options.

#### Acceptance Criteria

1. WHEN a user has sufficient spendable XP THEN the system SHALL allow purchase of OpenDyslexic font (50 XP)
2. WHEN a user has sufficient spendable XP THEN the system SHALL allow purchase of advanced word chunking (2-3 words) (100 XP) 
3. WHEN a user has sufficient spendable XP THEN the system SHALL allow purchase of smart connector grouping (75 XP)
4. WHEN a user has sufficient spendable XP THEN the system SHALL allow purchase of symbol removal options (25 XP)
5. WHEN a user purchases a feature THEN the system SHALL permanently unlock it for that user

### Requirement 3: Social Interaction Economy

**User Story:** As a user, I want to spend XP on social interactions, so that I can engage meaningfully with the community while my interactions have value.

#### Acceptance Criteria

1. WHEN posting a new comment THEN the system SHALL charge 100 spendable XP
2. WHEN replying to a comment THEN the system SHALL charge 50 spendable XP
3. WHEN giving Bronze interaction THEN the system SHALL charge 5 spendable XP
4. WHEN giving Silver interaction THEN the system SHALL charge 15 spendable XP
5. WHEN giving Gold interaction THEN the system SHALL charge 30 spendable XP
6. WHEN giving Troll report THEN the system SHALL charge 5 spendable XP
7. WHEN giving Bad report THEN the system SHALL charge 15 spendable XP
8. WHEN giving Shit report THEN the system SHALL charge 30 spendable XP
9. WHEN receiving positive interactions THEN the comment author SHALL earn 50% of spent XP as spendable points
10. WHEN receiving negative reports THEN the comment author SHALL NOT lose any XP or receive penalties

### Requirement 4: Dynamic WPM Progression System

**User Story:** As a user, I want to progressively increase my reading speed through perfect quiz performance, so that I can challenge myself and earn bonus rewards for speed improvements.

#### Acceptance Criteria

1. WHEN a new user registers THEN the system SHALL set initial WPM to 200 with max_wpm of 225
2. WHEN a user manually increases WPM THEN the system SHALL allow speeds up to their current max_wpm
3. WHEN a user scores 100% on quiz at maximum WPM THEN the system SHALL increase max_wpm by 25 points
4. WHEN max_wpm increases THEN the system SHALL award bonus XP for speed progression achievement
5. WHEN a user can only gain speed THEN the system SHALL require fresh/first-time quiz attempts (not retries)

### Requirement 5: Quiz Attempt Economics and Diminishing Returns

**User Story:** As a user, I want to be rewarded most for fresh quiz attempts, so that I'm encouraged to explore new content rather than repeat the same quizzes.

#### Acceptance Criteria

1. WHEN taking a quiz for the first time THEN the system SHALL award full XP based on performance
2. WHEN retaking the same quiz THEN the system SHALL reduce XP rewards by 50% for second attempt
3. WHEN retaking quiz multiple times THEN the system SHALL continue reducing XP until reaching 0 points
4. WHEN passing any quiz (even 0 XP retries) THEN the system SHALL unlock commenting privileges
5. WHEN commenting THEN the system SHALL allow using XP earned from any previous quiz attempts

### Requirement 6: XP Earning Mechanisms

**User Story:** As a user, I want to earn spendable XP through various reading activities, so that I can accumulate currency for premium features and interactions.

#### Acceptance Criteria

1. WHEN completing a quiz with 60%+ score THEN the system SHALL award base XP plus performance bonuses
2. WHEN reading at higher WPM THEN the system SHALL apply speed multiplier to XP rewards
3. WHEN reading complex articles THEN the system SHALL apply complexity multiplier to XP rewards
4. WHEN achieving perfect quiz scores THEN the system SHALL award bonus XP (25% extra)
5. WHEN improving personal WPM record THEN the system SHALL award improvement bonus XP (50 XP)

### Requirement 5: Premium Feature Management

**User Story:** As a user, I want to manage my purchased premium features, so that I can see what I own and activate/deactivate features as needed.

#### Acceptance Criteria

1. WHEN viewing profile THEN the system SHALL display all purchased premium features
2. WHEN a feature is purchased THEN the system SHALL immediately activate it for the user
3. WHEN using speed reader THEN the system SHALL show only purchased advanced options
4. WHEN insufficient XP for purchase THEN the system SHALL display required XP and current balance
5. WHEN features are unlocked THEN the system SHALL persist the unlock permanently

### Requirement 6: XP Transaction History

**User Story:** As a user, I want to see my XP transaction history, so that I can track how I earn and spend my points.

#### Acceptance Criteria

1. WHEN earning XP THEN the system SHALL record transaction with source (quiz, bonus, etc.)
2. WHEN spending XP THEN the system SHALL record transaction with purpose (comment, feature, etc.)
3. WHEN viewing transaction history THEN the system SHALL show chronological list with details
4. WHEN filtering transactions THEN the system SHALL allow filtering by type (earned/spent) and category
5. WHEN exporting history THEN the system SHALL provide downloadable transaction report

### Requirement 7: XP Balance Validation

**User Story:** As a system administrator, I want XP transactions to be validated and secure, so that users cannot exploit the system or have negative balances.

#### Acceptance Criteria

1. WHEN any XP transaction occurs THEN the system SHALL validate sufficient balance before processing
2. WHEN concurrent transactions occur THEN the system SHALL use database locks to prevent race conditions
3. WHEN XP calculation errors occur THEN the system SHALL log errors and maintain data integrity
4. WHEN suspicious XP activity is detected THEN the system SHALL flag accounts for review
5. WHEN XP balance becomes negative THEN the system SHALL prevent further spending and alert administrators

### Requirement 8: Advanced Quiz Feedback and Navigation System

**User Story:** As a user, I want detailed feedback on my quiz performance and smart navigation suggestions, so that I can learn from mistakes and discover relevant content.

#### Acceptance Criteria

1. WHEN scoring 100% on quiz THEN the system SHALL display "Perfect Quiz! You can comment on this article for free" message
2. WHEN scoring 100% THEN the system SHALL show encouragement about writing to improve retention
3. WHEN scoring 60-99% THEN the system SHALL show feedback only for incorrect answers
4. WHEN showing wrong answers THEN the system SHALL display correct answer in green and big letters, wrong answer in red with strikethrough
5. WHEN quiz is passed (≥60%) THEN the system SHALL show links to: next unread article with most common tags, random unread article, comment section
6. WHEN quiz is failed (<60%) THEN the system SHALL show links to: re-read article, try quiz again
7. WHEN quiz is failed THEN the system SHALL suggest reading at slower speed (last successful WPM or lower)
8. WHEN quiz is failed THEN the system SHALL NOT show correct/incorrect answer feedback
9. WHEN user fails repeatedly THEN the system SHALL recommend progressively slower reading speeds

### Requirement 9: Feature Pricing and Economy Balance

**User Story:** As a product manager, I want to balance XP pricing for features and interactions, so that the economy encourages engagement without being too restrictive.

#### Acceptance Criteria

1. WHEN setting feature prices THEN the system SHALL use configurable pricing that can be adjusted
2. WHEN users complete average quiz THEN they SHALL earn enough XP for 1-2 social interactions
3. WHEN users read regularly THEN they SHALL accumulate enough XP for premium features within reasonable time
4. WHEN analyzing economy THEN the system SHALL provide admin dashboard with XP flow metrics
5. WHEN rebalancing needed THEN the system SHALL allow price adjustments without affecting purchased features

## Technical Requirements

### XP System Architecture
- **TR-001:** System SHALL maintain separate fields for total_xp and current_xp_points in user model
- **TR-002:** All XP transactions SHALL be atomic and use database transactions
- **TR-003:** XP calculations SHALL be performed server-side to prevent client manipulation
- **TR-004:** Feature unlocks SHALL be stored as permanent user attributes

### Performance Requirements
- **PR-001:** XP balance checks SHALL complete within 100ms
- **PR-002:** Feature unlock status SHALL be cached to avoid repeated database queries
- **PR-003:** XP transaction logging SHALL not impact user experience performance
- **PR-004:** Concurrent XP transactions SHALL be handled without data corruption

### Security Requirements
- **SR-001:** XP transactions SHALL be validated server-side before processing
- **SR-002:** Feature unlock status SHALL be verified on each use to prevent tampering
- **SR-003:** XP transaction logs SHALL be immutable once created
- **SR-004:** Admin XP adjustment capabilities SHALL be logged and audited

## Business Rules

### Complex XP Earning Formula
```
Base XP = (word_count OR letter_count) * speed_multiplier * accuracy_bonus
Speed Multiplier = (wpm_used / 250) * complexity_factor  
Accuracy Bonus = quiz_score_percentage (only if >= 60%)
Perfect Score Bonus = Free comment + encouragement message
Failure Penalty = 0 XP + speed recommendation

Where:
- word_count = total words in article (1 XP per word)
- letter_count = total letters in article (1 XP per letter)
- complexity_factor = article.reading_level / 10
- Only award XP if quiz score >= 60%
- 100% score = free comment privilege
```

### Feature Pricing Structure
- **Basic Features (Free)**: Default font, 1-word chunking, basic controls
- **Tier 1 Features (25-50 XP)**: Symbol removal, basic themes
- **Tier 2 Features (75-100 XP)**: Advanced chunking, specialized fonts
- **Tier 3 Features (150+ XP)**: Premium themes, advanced analytics

### Social Interaction Costs
- **Comment Posting**: 100 XP (new), 50 XP (reply)
- **Positive Interactions**: Bronze (5 XP), Silver (15 XP), Gold (30 XP)
- **Negative Reporting**: Troll (5 XP), Bad (15 XP), Shit (30 XP)
- **Author Rewards**: 50% of interaction cost (positive interactions only)
- **Reporting Balance**: Same costs as positive ratings to encourage thoughtful community moderation

### XP Economy Balance
- **Average Quiz Reward**: 100-300 XP depending on performance
- **Daily Earning Potential**: 500-1000 XP for active users
- **Feature Unlock Timeline**: 1-3 days of regular use per premium feature
- **Social Interaction Budget**: 10-20 interactions per quiz completion

## Data Model Requirements

### User Model Extensions
```python
class CustomUser(AbstractUser):
    # Existing fields...
    total_xp = PositiveIntegerField(default=0)  # Accumulated XP (permanent record)
    current_xp_points = PositiveIntegerField(default=0)  # Spendable XP (currency)
    
    # Premium feature unlocks
    has_opendyslexic_font = BooleanField(default=False)
    has_advanced_chunking = BooleanField(default=False)
    has_connector_grouping = BooleanField(default=False)
    has_symbol_removal = BooleanField(default=False)
    has_premium_themes = BooleanField(default=False)
    
    # XP tracking
    last_xp_earned = DateTimeField(null=True, blank=True)
    xp_earning_streak = PositiveIntegerField(default=0)
```

### XP Transaction Model
```python
class XPTransaction(Model):
    user = ForeignKey(CustomUser, on_delete=CASCADE)
    transaction_type = CharField(choices=[('EARN', 'Earned'), ('SPEND', 'Spent')])
    amount = IntegerField()  # Positive for earn, negative for spend
    source = CharField(max_length=50)  # 'quiz', 'bonus', 'comment', 'feature_purchase'
    description = TextField()
    balance_after = PositiveIntegerField()  # XP balance after transaction
    timestamp = DateTimeField(auto_now_add=True)
    
    # Optional references
    quiz_attempt = ForeignKey(QuizAttempt, null=True, blank=True)
    comment = ForeignKey(Comment, null=True, blank=True)
    feature_purchased = CharField(max_length=50, null=True, blank=True)
```

### Feature Purchase Model
```python
class FeaturePurchase(Model):
    user = ForeignKey(CustomUser, on_delete=CASCADE)
    feature_name = CharField(max_length=50)
    xp_cost = PositiveIntegerField()
    purchase_date = DateTimeField(auto_now_add=True)
    transaction = ForeignKey(XPTransaction, on_delete=CASCADE)
```

---

*This requirements document defines a comprehensive XP economics system that transforms VeriFast into a gamified platform with virtual currency mechanics.*