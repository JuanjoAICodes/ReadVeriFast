# XP System Documentation

*Last Updated: July 21, 2025*
*Status: Current*

## Overview

The VeriFast XP (Experience Points) System is a comprehensive gamification framework that rewards users for engaging with content and provides premium features through XP spending.

## Core Components

### 1. XP Calculation Engine
**Location:** `verifast_app/xp_system.py`

Calculates XP rewards based on:
- **Quiz Performance** - Score-based rewards (higher scores = more XP)
- **Reading Speed** - WPM-based bonuses
- **Perfect Scores** - Bonus XP for 100% quiz scores
- **Content Difficulty** - Harder content provides more XP

### 2. Transaction Management
**Features:**
- **Earning XP** - Secure XP addition with validation
- **Spending XP** - Premium feature purchases
- **Transaction History** - Complete audit trail
- **Balance Validation** - Prevents negative balances

### 3. Premium Features
**Available Purchases:**
- **Font Customization** - OpenSans font option (30 XP)
- **Advanced Analytics** - Detailed reading statistics
- **Priority Support** - Enhanced user support

## XP Earning Opportunities

### Quiz Completion
- **Base XP:** 10-50 points based on score
- **Perfect Score Bonus:** +25 XP for 100% scores
- **Speed Bonus:** Additional XP for high WPM

### Social Interactions
- **Posting Comments:** 10 XP per comment
- **Receiving Likes:** 2.5 XP per interaction
- **Quality Content:** Bonus XP for well-received comments

### Content Engagement
- **Article Completion:** XP based on article length and difficulty
- **Tag Discovery:** XP for exploring new topics
- **Consistent Usage:** Daily engagement bonuses

## XP Spending System

### Premium Features Store
```python
FEATURES = {
    'font_opensans': {
        'name': 'OpenSans Font',
        'description': 'Premium font for better reading experience',
        'cost': 30,
        'category': 'customization'
    }
}
```

### Purchase Process
1. **Feature Selection** - User chooses premium feature
2. **Balance Check** - Validates sufficient XP
3. **Transaction Creation** - Records the purchase
4. **Feature Activation** - Enables the feature for user
5. **Balance Update** - Deducts XP from user account

## Technical Implementation

### Models
- **CustomUser.current_xp_points** - User's XP balance
- **XPTransaction** - All XP earning/spending records
- **FeaturePurchase** - Premium feature ownership
- **QuizAttempt** - Quiz performance data

### Key Classes

#### XPCalculationEngine
```python
def calculate_quiz_xp(self, quiz_attempt, article):
    """Calculate XP earned from quiz completion"""
    base_xp = self.get_base_xp(quiz_attempt.score)
    speed_bonus = self.get_speed_bonus(quiz_attempt.wpm_used)
    perfect_bonus = self.get_perfect_score_bonus(quiz_attempt.score)
    return base_xp + speed_bonus + perfect_bonus
```

#### XPTransactionManager
```python
def earn_xp(self, user, amount, source, transaction_type, description):
    """Safely add XP to user account with transaction record"""
    
def spend_xp(self, user, amount, source, description):
    """Safely deduct XP with balance validation"""
```

### Security Features
- **Transaction Validation** - Prevents invalid XP amounts
- **Balance Protection** - Cannot spend more XP than available
- **Audit Trail** - Complete transaction history
- **Concurrent Safety** - Thread-safe XP operations

## Performance Optimizations

### Caching Strategy
- **User XP Balance** - Cached for 15 minutes
- **Feature Ownership** - Cached for 1 hour
- **Transaction History** - Paginated queries

### Database Optimization
- **Indexes** - On user_id, transaction_type, created_at
- **Query Optimization** - Bulk operations for multiple users
- **Connection Pooling** - Efficient database usage

## Analytics and Monitoring

### XP Economy Metrics
- **Daily XP Earned** - Total XP generated per day
- **Feature Purchase Rates** - Premium feature adoption
- **User Engagement** - XP earning patterns
- **Balance Distribution** - XP wealth distribution

### Monitoring Tools
```python
class XPMonitoringManager:
    def get_economy_metrics(self):
        """Get comprehensive XP economy statistics"""
        
    def detect_anomalies(self):
        """Detect suspicious XP activity"""
        
    def generate_user_xp_report(self, user):
        """Generate detailed user XP report"""
```

## API Endpoints

### XP Information
- `GET /api/user/xp/` - Current user XP balance
- `GET /api/user/xp/transactions/` - Transaction history
- `GET /api/user/xp/features/` - Available premium features

### Feature Purchases
- `POST /api/user/xp/purchase/` - Purchase premium feature
- `GET /api/user/xp/owned-features/` - User's premium features

## Testing

### Test Coverage
- **XP Calculation** - All earning scenarios
- **Transaction Management** - Earning and spending flows
- **Security Validation** - Invalid transaction prevention
- **Performance** - Concurrent transaction handling

### Test Files
- `verifast_app/test_xp_system.py` - Core XP system tests
- `verifast_app/test_xp_economics.py` - Economic model tests

## Configuration

### XP Rates
```python
# Base XP rates (configurable)
QUIZ_BASE_XP = 10
PERFECT_SCORE_BONUS = 25
COMMENT_XP = 10
INTERACTION_XP = 2.5
```

### Feature Costs
Premium feature costs are defined in `PremiumFeatureStore.FEATURES` and can be adjusted based on economy balance.

## Future Enhancements

### Planned Features
- **XP Multipliers** - Temporary XP boost events
- **Achievement System** - XP rewards for milestones
- **Leaderboards** - Community XP rankings
- **XP Gifting** - Transfer XP between users

### Economy Balancing
- **Dynamic Pricing** - Adjust feature costs based on demand
- **Inflation Control** - Manage XP economy growth
- **Seasonal Events** - Special XP earning opportunities

## Related Documentation
- [Tag System](tag-system.md)
- [Speed Reader](speed-reader.md)
- [API Specification](../api/specification.md)