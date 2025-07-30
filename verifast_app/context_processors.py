import json
from django.utils.translation import gettext as _
from .models import CustomUser

def user_xp_processor(request):
    """
    Makes the user's total XP available to all templates.
    """
    if request.user.is_authenticated:
        # Ensure we are working with the full CustomUser object
        # request.user might be a lazy object in some cases
        try:
            user = CustomUser.objects.get(pk=request.user.pk)
            return {'total_xp': user.total_xp}
        except CustomUser.DoesNotExist:
            return {}
    else:
        # For anonymous users, get XP from session
        session_xp = request.session.get('total_xp', 0)
        if session_xp > 0:
            # Set session expiry for anonymous users with progress
            request.session.set_expiry(60 * 24 * 60 * 60)  # 60 days in seconds
        return {'total_xp': session_xp}


def admin_premium_processor(request):
    """
    Context processor to provide admin premium feature access.
    Admin users (is_staff=True) get all premium features unlocked.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'is_admin_user': True,
            'admin_has_all_premium': True,
            'admin_premium_notice': _('Admin Mode: All premium features unlocked')
        }
    return {
        'is_admin_user': False,
        'admin_has_all_premium': False,
        'admin_premium_notice': ''
    }


def js_translations_processor(request):
    """
    Context processor to provide JavaScript translations.
    """
    js_translations = {
        # Basic UI
        'loading': _('Loading...'),
        'error': _('Error'),
        'success': _('Success'),
        'confirm': _('Are you sure?'),
        'cancel': _('Cancel'),
        'save': _('Save'),
        'delete': _('Delete'),
        'edit': _('Edit'),
        'close': _('Close'),
        'next': _('Next'),
        'previous': _('Previous'),
        
        # Speed Reader
        'start_reading': _('Start Reading'),
        'pause_reading': _('Pause'),
        'stop': _('Stop'),
        'resume': _('Resume'),
        'reading_finished': _('Reading finished!'),
        'click_start_reading': _('Click Start to begin reading'),
        'no_content_available': _('No content available'),
        'ready_to_read': _('Ready to read'),
        'speed_wpm': _('WPM'),
        'speed_changed_to': _('Speed changed to'),
        'reading_in_progress_warning': _('Reading in progress. Are you sure you want to leave?'),
        
        # Accessibility and Help
        'speed_reader_unavailable': _('Speed Reader Unavailable'),
        'speed_reader_fallback_message': _('The speed reader could not be loaded. You can still read the article below.'),
        'keyboard_shortcuts': _('Keyboard Shortcuts'),
        'start_pause_reading': _('Start/Pause reading'),
        'reset_reading': _('Reset reading'),
        'toggle_immersive': _('Toggle immersive mode'),
        'increase_speed': _('Increase speed'),
        'decrease_speed': _('Decrease speed'),
        'exit_immersive': _('Exit immersive mode'),
        'show_keyboard_shortcuts': _('Show keyboard shortcuts'),
        
        # Quiz
        'quiz_completed': _('Quiz completed!'),
        'quiz_loading': _('Loading quiz...'),
        'quiz_error': _('Error loading quiz'),
        'submit_quiz': _('Submit Quiz'),
        'quiz_score': _('Your score'),
        'quiz_passed': _('Congratulations! You passed!'),
        'quiz_failed': _('Try again to improve your score'),
        'question_of': _('Question {current} of {total}'),
        'quiz_results': _('Quiz Results'),
        'quiz_not_available': _('Quiz not available for this article.'),
        'quiz_start': _('Start Quiz'),
        'quiz_close': _('Close quiz'),
        'quiz_previous': _('Previous'),
        'quiz_next': _('Next'),
        'quiz_submit': _('Submit Quiz'),
        
        # Comments
        'comment_posted': _('Comment posted successfully'),
        'comment_error': _('Error posting comment'),
        'reply_posted': _('Reply posted successfully'),
        'interaction_added': _('Interaction added'),
        'insufficient_xp': _('Not enough XP'),
    }
    
    return {
        'js_translations_json': json.dumps(js_translations)
    }
