from django import template
from ..models import CommentInteraction

register = template.Library()

@register.simple_tag
def get_user_interaction(comment, user):
    """Get the user's interaction with a specific comment, if any."""
    if not user.is_authenticated:
        return None
    
    try:
        return CommentInteraction.objects.get(comment=comment, user=user)
    except CommentInteraction.DoesNotExist:
        return None

@register.filter
def interaction_count(comment):
    """Get the total number of interactions for a comment."""
    return comment.commentinteraction_set.count()

@register.filter
def interaction_breakdown(comment):
    """Get a breakdown of interactions by type."""
    interactions = comment.commentinteraction_set.all()
    breakdown = {'BRONZE': 0, 'SILVER': 0, 'GOLD': 0, 'REPORT': 0}
    
    for interaction in interactions:
        breakdown[interaction.interaction_type] += 1
    
    return breakdown