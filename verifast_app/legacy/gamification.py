from typing import cast
from verifast_app.models import QuizAttempt, Comment, Article, CustomUser


# Advanced XP calculation formula based on Consolidado VeriFast specification
# XP_ganado = (Complejidad_Texto_Factor * Velocidad_Leida_Factor * Porcentaje_Correcto_Quiz)
#           + Bonus_100_Por_Ciento + Bonus_Mejora_Velocidad

def calculate_xp_reward(score_percentage: float, wpm: int, article: Article, user: CustomUser, last_successful_wpm: int = 0) -> dict:
    """
    Calculates XP reward using the advanced formula from Consolidado VeriFast.

    Returns a dictionary with:
    - total_xp: Total XP to award
    - spendable_xp: XP to add to current_xp_points
    - breakdown: Detailed calculation breakdown
    """
    # 1. Complejidad_Texto_Factor: From reading_level (1 to 10)
    complexity_factor = min(max(article.reading_level or 5.0, 1.0), 10.0)

    # 2. Velocidad_Leida_Factor: wpm_used / max_wpm (max 1.0)
    speed_factor = min(wpm / user.max_wpm, 1.0) if user.max_wpm > 0 else 0.5

    # 3. Porcentaje_Correcto_Quiz: Score percentage (0.0 to 1.0)
    score_factor = score_percentage / 100.0

    # Base XP calculation
    base_xp = complexity_factor * speed_factor * score_factor * 100

    # 4. Bonus_100_Por_Ciento: 50 XP if quiz is 100% correct
    perfect_bonus = 50 if score_percentage >= 100.0 else 0

    # 5. Bonus_Mejora_Velocidad: 1.2x multiplier if current WPM > last successful WPM
    speed_improvement_multiplier = 1.0
    if last_successful_wpm and wpm > last_successful_wpm:
        speed_improvement_multiplier = 1.2
        base_xp *= speed_improvement_multiplier

    # Calculate total XP
    total_xp = int(base_xp + perfect_bonus)

    # Spendable XP is 60% of total XP (40% goes to total_xp only)
    spendable_xp = int(total_xp * 0.6)

    breakdown = {
        'complexity_factor': complexity_factor,
        'speed_factor': speed_factor,
        'score_factor': score_factor,
        'base_xp': base_xp,
        'perfect_bonus': perfect_bonus,
        'speed_improvement_multiplier': speed_improvement_multiplier,
        'total_xp': total_xp,
        'spendable_xp': spendable_xp
    }

    return {
        'total_xp': total_xp,
        'spendable_xp': spendable_xp,
        'breakdown': breakdown
    }

def update_wpm_progression(user: CustomUser, wpm_used: int, score_percentage: float):
    """
    Updates user's WPM based on performance according to Consolidado VeriFast rules:
    - If quiz is 100% correct and wpm_used equals max_wpm, increase max_wpm
    - WPM increase rules: <300: +25, 300-600: +10, 600+: +5
    """
    # Update current WPM to the WPM used in successful attempt
    if score_percentage >= 60.0:  # Successful quiz (60%+ correct)
        user.current_wpm = wpm_used
        user.last_successful_wpm_used = wpm_used

        # Check for max WPM increase (100% score + at max speed)
        if score_percentage >= 100.0 and wpm_used >= user.max_wpm:
            if user.max_wpm < 300:
                user.max_wpm += 25
            elif user.max_wpm < 600:
                user.max_wpm += 10
            else:
                user.max_wpm += 5
    else:
        # Failed quiz - reduce current WPM
        if user.last_successful_wpm_used:
            user.current_wpm = user.last_successful_wpm_used
        else:
            # No previous success, reduce by 10 WPM from failed attempt
            user.current_wpm = max(50, wpm_used - 10)

def update_user_stats_after_quiz(user: CustomUser, quiz_attempt: QuizAttempt, article: Article):
    """
    Enhanced user stats update using advanced XP calculation and WPM progression.
    """
    # Calculate XP using advanced formula
    xp_result = calculate_xp_reward(
        score_percentage=quiz_attempt.score,
        wpm=quiz_attempt.wpm_used,
        article=article,
        user=user,
        last_successful_wpm=user.last_successful_wpm_used
    )

    # Update XP values
    user.total_xp += xp_result['total_xp']
    user.current_xp_points += xp_result['spendable_xp']

    # Update WPM progression
    update_wpm_progression(user, quiz_attempt.wpm_used, quiz_attempt.score)

    # Update quiz attempt with calculated XP
    quiz_attempt.xp_awarded = xp_result['total_xp']
    quiz_attempt.save()

    user.save()

    return xp_result

# XP costs for social features (using spendable XP points)
XP_COST_NEW_COMMENT = 10
XP_COST_REPLY_COMMENT = 5

# Refined interaction costs from Consolidado VeriFast
INTERACTION_COSTS = {
    'BRONZE': 5,   # Reduced from 10
    'SILVER': 10,  # Reduced from 50
    'GOLD': 20,    # Reduced from 200
    'REPORT': 0    # Free to report
}

def post_comment(user: CustomUser, article: Article, content: str, parent_comment: Comment | None = None) -> bool:
    """
    Handles posting a comment, deducting spendable XP points, and updating user stats.
    Uses current_xp_points (spendable) instead of total_xp.
    """
    xp_cost = XP_COST_REPLY_COMMENT if parent_comment else XP_COST_NEW_COMMENT

    if user.current_xp_points >= xp_cost:
        user.current_xp_points -= xp_cost
        user.save()

        Comment.objects.create(
            article=article,
            user=user,
            content=content,
            parent_comment=parent_comment
        )

        print(f"Comment posted by {user.username}. Spendable XP deducted: {xp_cost}")
        return True
    else:
        print(f"{user.username} does not have enough spendable XP to post a comment.")
        return False

def interact_with_comment(user: CustomUser, comment: Comment, interaction_type: str) -> dict:
    """
    Handles comment interactions (Bronze, Silver, Gold, Report) with refined XP economics.

    Returns:
    - success: Boolean indicating if interaction was successful
    - message: Status message
    - xp_cost: XP cost for the interaction
    - author_reward: XP reward given to comment author (50% of cost)
    """
    from verifast_app.models import CommentInteraction

    # Check if user already interacted with this comment
    existing_interaction = CommentInteraction.objects.filter(
        user=user, comment=comment
    ).first()

    if existing_interaction:
        return {
            'success': False,
            'message': f'You already gave this comment {existing_interaction.interaction_type.lower()}',
            'xp_cost': 0,
            'author_reward': 0
        }

    # Get XP cost for interaction
    xp_cost = INTERACTION_COSTS.get(interaction_type, 0)

    # Check if user has enough spendable XP (except for reports)
    if interaction_type != 'REPORT' and user.current_xp_points < xp_cost:
        return {
            'success': False,
            'message': f'Not enough spendable XP. Need {xp_cost}, have {user.current_xp_points}',
            'xp_cost': xp_cost,
            'author_reward': 0
        }

    # Calculate author reward (50% of XP cost for positive interactions)
    author_reward = 0
    if interaction_type in ['BRONZE', 'SILVER', 'GOLD']:
        author_reward = xp_cost // 2

    # Process the interaction
    if interaction_type != 'REPORT':
        user.current_xp_points -= xp_cost
        user.save()

    # Reward comment author (50% of spent XP)
    if author_reward > 0:
        comment_user = cast(CustomUser, comment.user)
        comment_user.current_xp_points += author_reward
        comment_user.save()

    # Create interaction record
    CommentInteraction.objects.create(
        user=user,
        comment=comment,
        interaction_type=interaction_type,
        xp_cost=xp_cost
    )

    # Handle negative interactions (for future behavior tracking)
    if interaction_type == 'REPORT':
        comment_user = cast(CustomUser, comment.user)
        comment_user.current_xp_points += author_reward
        comment_user.save()

    return {
        'success': True,
        'message': f'Successfully gave {interaction_type.lower()} to comment',
        'xp_cost': xp_cost,
        'author_reward': author_reward
    }