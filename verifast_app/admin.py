from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import (
    CustomUser, Article, Tag, QuizAttempt, Comment, CommentInteraction, 
    AdminCorrectionDataset, XPTransaction, FeaturePurchase
)
from .models_content_acquisition import ContentFingerprint


# Conditionally import and register content acquisition admin panels
if settings.DJANGO_RUN_MODE == 'FULL':
    try:
        from . import admin_content_acquisition  # Registers ContentSource admin and dashboard/orchestrate URLs
    except ImportError:
        pass  # Content acquisition admin not available


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    readonly_fields = ('reading_level', 'llm_model_used', 'timestamp', 'word_count', 'letter_count')
    list_display = ('title', 'source', 'processing_status', 'has_quiz', 'quiz_question_count', 'publication_date')
    list_filter = ('processing_status', 'source', 'language', 'article_type')
    search_fields = ('title', 'url')
    filter_horizontal = ('tags',)
    actions = ['retry_processing', 'reprocess_quiz', 'start_content_motor']

    def get_actions(self, request):
        actions = super().get_actions(request)
        if settings.DJANGO_RUN_MODE != 'FULL':
            if 'start_content_motor' in actions:
                del actions['start_content_motor']
        return actions

    @admin.display(description=_('Has Quiz'), boolean=True)
    def has_quiz(self, obj):
        return bool(obj.quiz_data)

    @admin.display(description=_('Quiz Questions'))
    def quiz_question_count(self, obj):
        if obj.quiz_data:
            return len(obj.quiz_data) if isinstance(obj.quiz_data, list) else _('Invalid format')
        return 0

    @admin.display(description=_('Retry processing for selected articles'))
    def retry_processing(self, request, queryset):
        queryset.update(processing_status='pending')
        # Trigger processing tasks
        from .tasks import process_article, process_wikipedia_article
        for article in queryset:
            if article.article_type == 'wikipedia':
                process_wikipedia_article.delay(article.id)
            else:
                process_article.delay(article.id)

    @admin.display(description=_('Reprocess quiz for selected articles'))
    def reprocess_quiz(self, request, queryset):
        from .tasks import process_article, process_wikipedia_article
        for article in queryset:
            if article.article_type == 'wikipedia':
                process_wikipedia_article.delay(article.id)
            else:
                process_article.delay(article.id)
        self.message_user(request, _("Reprocessing %(count)d articles for quiz generation.") % {'count': queryset.count()})

    @admin.display(description=_('🚀 Start Content Motor - Find New Articles'))
    def start_content_motor(self, request, queryset):
        """Start the content motor to acquire new articles from configured sources"""
        try:
            # Import content acquisition components
            from .models_content_acquisition import ContentSource
            from .tasks_content_acquisition import acquire_content_from_source
            
            # Get active content sources
            active_sources = ContentSource.objects.filter(is_active=True)
            
            if not active_sources.exists():
                self.message_user(
                    request, 
                    _("No active content sources found. Please configure content sources first."),
                    level='WARNING'
                )
                return
            
            # Trigger acquisition for all active sources
            triggered_count = 0
            task_ids = []
            
            for source in active_sources:
                can_request, reason = source.can_make_request()
                
                if can_request:
                    task = acquire_content_from_source.delay(source.id, 'manual', 15)
                    task_ids.append(task.id)
                    triggered_count += 1
                else:
                    self.message_user(
                        request,
                        f"Skipped {source.name}: {reason}",
                        level='WARNING'
                    )
            
            if triggered_count > 0:
                self.message_user(
                    request,
                    _(
                        "🚀 Content Motor started! Triggered acquisition for %(count)d sources. "
                        "Task IDs: %(tasks)s. Check the Content Acquisition Jobs in admin to monitor progress."
                    ) % {
                        'count': triggered_count,
                        'tasks': ', '.join(task_ids[:3]) + ('...' if len(task_ids) > 3 else '')
                    },
                    level='SUCCESS'
                )
            else:
                self.message_user(
                    request,
                    _("No content sources were available for acquisition. Check source health and rate limits."),
                    level='WARNING'
                )
                
        except ImportError:
            self.message_user(
                request,
                _("Content acquisition system not available. Please ensure all content acquisition modules are installed."),
                level='ERROR'
            )
        except Exception as e:
            self.message_user(
                request,
                _("Error starting content motor: %(error)s") % {'error': str(e)},
                level='ERROR'
            )

    def delete_queryset(self, request, queryset):
        """
        Custom delete_queryset to ensure related objects are deleted first
        to prevent FOREIGN KEY constraint failures.
        """
        # Explicitly delete related objects that have a ForeignKey to Article
        # Even if on_delete=CASCADE is set, this can help with complex scenarios
        # or database-level inconsistencies.

        # Delete related Comments
        Comment.objects.filter(article__in=queryset).delete()
        # Delete related QuizAttempts
        QuizAttempt.objects.filter(article__in=queryset).delete()
        # Delete related ContentFingerprints
        ContentFingerprint.objects.filter(article__in=queryset).delete()
        

        # Now call the superclass's delete_queryset to delete the Articles themselves
        super().delete_queryset(request, queryset)

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'url', 'source', 'article_type', 'language')
        }),
        (_('Processing Status'), {
            'fields': ('processing_status', 'llm_model_used', 'timestamp')
        }),
        (_('Content Analysis'), {
            'fields': ('reading_level', 'word_count', 'letter_count'),
            'classes': ('collapse',)
        }),
        (_('Quiz Data'), {
            'fields': ('quiz_data',),
            'classes': ('collapse',)
        }),
        (_('Content'), {
            'fields': ('content', 'raw_content', 'summary'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('publication_date', 'image_url', 'tags'),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/admin_custom.css',)
        }


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'current_wpm',
        'total_xp',
        'current_xp_points',
        'xp_earning_streak',
        'perfect_quiz_count',
    )
    search_fields = ('username', 'email')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Reading Performance', {
            'fields': ('current_wpm', 'max_wpm', 'last_successful_wpm_used')
        }),
        ('XP System', {
            'fields': (
                'total_xp', 'current_xp_points', 'lifetime_xp_earned', 
                'lifetime_xp_spent', 'xp_earning_streak', 'last_xp_earned'
            )
        }),
        ('Quiz Statistics', {
            'fields': ('perfect_quiz_count', 'quiz_attempts_count')
        }),
        ('Premium Fonts', {
            'fields': (
                'has_font_opensans', 'has_font_opendyslexic', 'has_font_roboto',
                'has_font_merriweather', 'has_font_playfair'
            ),
            'classes': ('collapse',)
        }),
        ('Premium Chunking', {
            'fields': (
                'has_2word_chunking', 'has_3word_chunking', 
                'has_4word_chunking', 'has_5word_chunking'
            ),
            'classes': ('collapse',)
        }),
        ('Smart Features', {
            'fields': ('has_smart_connector_grouping', 'has_smart_symbol_handling'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('preferred_language', 'theme')
        }),
    )
    
    readonly_fields = (
        'total_xp', 'lifetime_xp_earned', 'lifetime_xp_spent', 
        'last_xp_earned', 'perfect_quiz_count', 'quiz_attempts_count'
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'timestamp')
    search_fields = ('user__username', 'article__title')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'score', 'wpm_used', 'xp_awarded', 'timestamp')
    search_fields = ('user__username', 'article__title')


@admin.register(CommentInteraction)
class CommentInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'interaction_type', 'timestamp')
    search_fields = ('user__username', 'comment__id')


@admin.register(AdminCorrectionDataset)
class AdminCorrectionDatasetAdmin(admin.ModelAdmin):
    list_display = ('original_article_url', 'admin_user', 'timestamp')
    search_fields = ('original_article_url', 'admin_user__username')


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'transaction_type', 'amount', 'source', 
        'balance_after', 'timestamp'
    )
    list_filter = ('transaction_type', 'source', 'timestamp')
    search_fields = ('user__username', 'description')
    readonly_fields = (
        'user', 'transaction_type', 'amount', 'source', 'description',
        'balance_after', 'timestamp', 'quiz_attempt', 'comment', 'feature_purchased'
    )
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        # Prevent manual creation of transactions through admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing of transactions through admin
        return False


@admin.register(FeaturePurchase)
class FeaturePurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'feature_display_name', 'xp_cost', 'purchase_date'
    )
    list_filter = ('feature_name', 'purchase_date')
    search_fields = ('user__username', 'feature_display_name')
    readonly_fields = (
        'user', 'feature_name', 'feature_display_name', 
        'xp_cost', 'purchase_date', 'transaction'
    )
    ordering = ['-purchase_date']
    
    def has_add_permission(self, request):
        # Prevent manual creation of purchases through admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing of purchases through admin
        return False


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'is_validated', 'article_count', 
        'wikipedia_url', 'created_at', 'last_updated'
    )
    list_filter = ('is_validated', 'created_at', 'last_updated')
    search_fields = ('name', 'description', 'slug')
    readonly_fields = ('slug', 'article_count', 'created_at', 'last_updated')
    actions = ['validate_with_wikipedia', 'update_article_counts']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Wikipedia Integration', {
            'fields': ('is_validated', 'wikipedia_url', 'wikipedia_content'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('article_count', 'created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description="Validate selected tags with Wikipedia")
    def validate_with_wikipedia(self, request, queryset):
        """Validate selected tags with Wikipedia"""
        from .wikipedia_service import WikipediaService
        
        service = WikipediaService()
        validated_count = 0
        
        for tag in queryset:
            try:
                is_valid, data = service.validate_tag_with_wikipedia(tag.name)
                if is_valid and data:
                    tag.wikipedia_url = data.get('url')
                    tag.description = data.get('summary', '')[:500]  # Limit description
                    tag.is_validated = True
                    tag.save()
                    validated_count += 1
            except Exception as e:
                self.message_user(request, f"Error validating {tag.name}: {str(e)}", level='ERROR')
        
        self.message_user(
            request, 
            f"Successfully validated {validated_count} tags with Wikipedia.",
            level='SUCCESS'
        )
    
    @admin.display(description="Update article counts for selected tags")
    def update_article_counts(self, request, queryset):
        """Update article counts for selected tags"""
        updated_count = 0
        
        for tag in queryset:
            try:
                tag.update_article_count()
                updated_count += 1
            except Exception as e:
                self.message_user(request, f"Error updating {tag.name}: {str(e)}", level='ERROR')
        
        self.message_user(
            request,
            f"Successfully updated article counts for {updated_count} tags.",
            level='SUCCESS'
        )
