"""
Django Admin Interface for Content Acquisition Management
Provides comprehensive admin controls for content sources and acquisition monitoring
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta

from .models_content_acquisition import (
    ContentSource, ContentAcquisitionJob, ContentFingerprint, AcquisitionMetrics
)
from .tasks_content_acquisition import acquire_content_from_source
from .services.content_orchestrator import ContentAcquisitionOrchestrator


@admin.register(ContentSource)
class ContentSourceAdmin(admin.ModelAdmin):
    """Admin interface for Content Sources"""
    
    list_display = [
        'name', 'source_type', 'language', 'priority', 'status_indicator', 
        'health_score_display', 'last_successful_fetch', 'total_articles_fetched',
        'action_buttons'
    ]
    
    list_filter = [
        'source_type', 'language', 'priority', 'status', 'is_active'
    ]
    
    search_fields = ['name', 'description', 'url']
    
    readonly_fields = [
        'last_successful_fetch', 'last_error', 'consecutive_failures',
        'total_articles_fetched', 'current_hour_requests', 'current_day_requests',
        'created_at', 'updated_at', 'health_score_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'source_type', 'url', 'language')
        }),
        ('Configuration', {
            'fields': ('priority', 'is_active', 'status', 'config_data')
        }),
        ('Rate Limiting', {
            'fields': ('requests_per_hour', 'requests_per_day', 'current_hour_requests', 'current_day_requests')
        }),
        ('Health Monitoring', {
            'fields': ('last_successful_fetch', 'last_error', 'consecutive_failures', 'total_articles_fetched', 'health_score_display')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['test_connection', 'trigger_acquisition', 'reset_counters', 'activate_sources', 'deactivate_sources']
    
    def status_indicator(self, obj):
        """Display status with color coding"""
        colors = {
            'active': 'green',
            'inactive': 'gray',
            'error': 'red',
            'rate_limited': 'orange',
            'maintenance': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_indicator.short_description = 'Status'
    
    def health_score_display(self, obj):
        """Display health score with color coding"""
        score = obj.get_health_score()
        if score >= 80:
            color = 'green'
        elif score >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/100</span>',
            color, score
        )
    health_score_display.short_description = 'Health Score'
    
    def action_buttons(self, obj):
        """Display action buttons for each source"""
        return format_html(
            '<a class="button" href="{}">Test</a> '
            '<a class="button" href="{}">Acquire</a> '
            '<a class="button" href="{}">Stats</a> '
            '<a class="button" href="{}">Orchestrate</a>',
            reverse('admin:test_source', args=[obj.pk]),
            reverse('admin:trigger_source_acquisition', args=[obj.pk]),
            reverse('admin:source_statistics', args=[obj.pk]),
            reverse('admin:orchestrate_acquisition')
        )
    action_buttons.short_description = 'Actions'
    
    def test_connection(self, request, queryset):
        """Test connection for selected sources"""
        results = []
        for source in queryset:
            if source.source_type == 'newsdata_api':
                from .services.newsdata_service import NewsDataService
                service = NewsDataService()
                success, message = service.test_connection(source)
            elif source.source_type == 'gnews_api':
                from .services.gnews_service import GNewsService
                service = GNewsService()
                success, message = service.test_connection(source)
            elif source.source_type == 'newsapi':
                from .services.newsapi_service import NewsAPIService
                service = NewsAPIService()
                success, message = service.test_connection(source)
            elif source.source_type == 'rss':
                from .services.rss_service import RSSProcessor
                service = RSSProcessor()
                success, message = service.test_feed_connection(source)
            else:
                success, message = False, f"Unknown source type: {source.source_type}"
            
            results.append(f"{source.name}: {'✓' if success else '✗'} {message}")
        
        self.message_user(request, "Connection test results:\n" + "\n".join(results))
    test_connection.short_description = "Test connection for selected sources"
    
    def trigger_acquisition(self, request, queryset):
        """Trigger manual acquisition for selected sources"""
        triggered = 0
        for source in queryset:
            if source.is_active:
                acquire_content_from_source.delay(source.id, 'manual', 10)
                triggered += 1
        
        self.message_user(request, f"Triggered acquisition for {triggered} sources")
    trigger_acquisition.short_description = "Trigger manual acquisition"
    
    def reset_counters(self, request, queryset):
        """Reset rate limiting counters"""
        updated = queryset.update(
            current_hour_requests=0,
            current_day_requests=0,
            consecutive_failures=0
        )
        self.message_user(request, f"Reset counters for {updated} sources")
    reset_counters.short_description = "Reset rate limiting counters"
    
    def activate_sources(self, request, queryset):
        """Activate selected sources"""
        updated = queryset.update(is_active=True, status='active')
        self.message_user(request, f"Activated {updated} sources")
    activate_sources.short_description = "Activate selected sources"
    
    def deactivate_sources(self, request, queryset):
        """Deactivate selected sources"""
        updated = queryset.update(is_active=False, status='inactive')
        self.message_user(request, f"Deactivated {updated} sources")
    deactivate_sources.short_description = "Deactivate selected sources"
    
    def get_urls(self):
        """Add custom URLs for admin actions"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='content_acquisition_dashboard'),
            path('test_source/<int:source_id>/', self.admin_site.admin_view(self.test_source_view), name='test_source'),
            path('trigger_acquisition/<int:source_id>/', self.admin_site.admin_view(self.trigger_acquisition_view), name='trigger_source_acquisition'),
            path('source_stats/<int:source_id>/', self.admin_site.admin_view(self.source_statistics_view), name='source_statistics'),
            path('orchestrate/', self.admin_site.admin_view(self.orchestrate_view), name='orchestrate_acquisition'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Content acquisition dashboard"""
        # Get overall statistics
        total_sources = ContentSource.objects.count()
        active_sources = ContentSource.objects.filter(is_active=True).count()
        healthy_sources = ContentSource.objects.filter(status='active').count()
        
        # Get recent jobs
        recent_jobs = ContentAcquisitionJob.objects.select_related('source').order_by('-created_at')[:10]
        
        # Get recent metrics
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        weekly_metrics = AcquisitionMetrics.objects.filter(
            date__gte=week_ago,
            hour__isnull=True
        ).aggregate(
            total_found=Sum('articles_found'),
            total_processed=Sum('articles_processed'),
            total_duplicated=Sum('articles_duplicated'),
            total_rejected=Sum('articles_rejected')
        )
        
        # Get source performance
        source_performance = ContentSource.objects.annotate(
            health_score=Count('id')  # Placeholder - would calculate actual health score
        ).order_by('-total_articles_fetched')[:5]
        
        context = {
            'title': 'Content Acquisition Dashboard',
            'total_sources': total_sources,
            'active_sources': active_sources,
            'healthy_sources': healthy_sources,
            'recent_jobs': recent_jobs,
            'weekly_metrics': weekly_metrics,
            'source_performance': source_performance,
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/content_acquisition_dashboard.html', context)
    
    def test_source_view(self, request, source_id):
        """Test individual source connection"""
        try:
            source = ContentSource.objects.get(id=source_id)
            
            if source.source_type == 'newsdata_api':
                from .services.newsdata_service import NewsDataService
                service = NewsDataService()
                success, message = service.test_connection(source)
            elif source.source_type == 'rss':
                from .services.rss_service import RSSProcessor
                service = RSSProcessor()
                success, message = service.test_feed_connection(source)
            else:
                success, message = False, f"Unknown source type: {source.source_type}"
            
            if success:
                messages.success(request, f"Connection test successful: {message}")
            else:
                messages.error(request, f"Connection test failed: {message}")
                
        except ContentSource.DoesNotExist:
            messages.error(request, "Source not found")
        
        return redirect('admin:verifast_app_contentsource_changelist')
    
    def trigger_acquisition_view(self, request, source_id):
        """Trigger acquisition for individual source"""
        try:
            source = ContentSource.objects.get(id=source_id)
            
            if not source.is_active:
                messages.warning(request, f"Source {source.name} is not active")
            else:
                task = acquire_content_from_source.delay(source.id, 'manual', 15)
                messages.success(request, f"Triggered acquisition for {source.name} (Task ID: {task.id})")
                
        except ContentSource.DoesNotExist:
            messages.error(request, "Source not found")
        
        return redirect('admin:verifast_app_contentsource_changelist')
    
    def source_statistics_view(self, request, source_id):
        """Show detailed statistics for a source"""
        try:
            source = ContentSource.objects.get(id=source_id)
            
            # Get recent metrics
            week_ago = timezone.now().date() - timedelta(days=7)
            metrics = AcquisitionMetrics.objects.filter(
                source=source,
                date__gte=week_ago
            ).order_by('-date')
            
            # Get recent jobs
            recent_jobs = ContentAcquisitionJob.objects.filter(
                source=source
            ).order_by('-created_at')[:10]
            
            context = {
                'title': f'Statistics for {source.name}',
                'source': source,
                'metrics': metrics,
                'recent_jobs': recent_jobs,
                'opts': self.model._meta,
            }
            
            return render(request, 'admin/source_statistics.html', context)
            
        except ContentSource.DoesNotExist:
            messages.error(request, "Source not found")
            return redirect('admin:verifast_app_contentsource_changelist')
    
    def orchestrate_view(self, request):
        """Manual orchestration interface"""
        if request.method == 'POST':
            languages = request.POST.getlist('languages')
            max_articles = int(request.POST.get('max_articles', 20))
            
            orchestrator = ContentAcquisitionOrchestrator()
            result = orchestrator.orchestrate_acquisition(
                languages=languages,
                max_articles=max_articles
            )
            
            messages.success(request, 
                f"Orchestration completed: {result['total_articles_processed']} articles processed "
                f"from {result['sources_successful']}/{result['sources_processed']} sources"
            )
            
            return redirect('admin:content_acquisition_dashboard')
        
        context = {
            'title': 'Manual Content Orchestration',
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/orchestrate_acquisition.html', context)


@admin.register(ContentAcquisitionJob)
class ContentAcquisitionJobAdmin(admin.ModelAdmin):
    """Admin interface for Content Acquisition Jobs"""
    
    list_display = [
        'id', 'job_type', 'source', 'status_indicator', 'started_at', 
        'duration_display', 'articles_processed', 'success_rate_display'
    ]
    
    list_filter = ['job_type', 'status', 'source__source_type', 'started_at']
    
    search_fields = ['source__name', 'error_message']
    
    readonly_fields = [
        'started_at', 'completed_at', 'articles_found', 'articles_processed',
        'articles_duplicated', 'articles_rejected', 'created_at', 'updated_at'
    ]
    
    def status_indicator(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'gray',
            'running': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_indicator.short_description = 'Status'
    
    def duration_display(self, obj):
        """Display job duration"""
        duration = obj.get_duration()
        if duration > 0:
            return f"{duration:.1f}s"
        return "-"
    duration_display.short_description = 'Duration'
    
    def success_rate_display(self, obj):
        """Display success rate"""
        rate = obj.get_success_rate()
        if isinstance(rate, (int, float)) and rate > 0:
            color = 'green' if rate >= 80 else 'orange' if rate >= 60 else 'red'
            formatted_rate = f"{rate:.1f}%"
            return format_html(
                '<span style="color: {};">{}</span>',
                color, formatted_rate
            )
        return "-"
    success_rate_display.short_description = 'Success Rate'


@admin.register(ContentFingerprint)
class ContentFingerprintAdmin(admin.ModelAdmin):
    """Admin interface for Content Fingerprints"""
    
    list_display = [
        'id', 'topic_category', 'language', 'source', 'first_seen', 'last_seen', 'article_link'
    ]
    
    list_filter = ['language', 'topic_category', 'source', 'first_seen']
    
    search_fields = ['topic_category', 'source__name']
    
    readonly_fields = ['url_hash', 'title_hash', 'content_hash', 'first_seen', 'last_seen']
    
    def article_link(self, obj):
        """Link to associated article"""
        if obj.article:
            return format_html(
                '<a href="{}" target="_blank">View Article</a>',
                reverse('admin:verifast_app_article_change', args=[obj.article.pk])
            )
        return "-"
    article_link.short_description = 'Article'


@admin.register(AcquisitionMetrics)
class AcquisitionMetricsAdmin(admin.ModelAdmin):
    """Admin interface for Acquisition Metrics"""
    
    list_display = [
        'date', 'hour', 'source', 'language', 'articles_processed', 
        'success_rate_display', 'avg_response_time'
    ]
    
    list_filter = ['date', 'source', 'language']
    
    readonly_fields = [
        'date', 'hour', 'articles_found', 'articles_processed', 
        'articles_duplicated', 'articles_rejected', 'total_requests',
        'successful_requests', 'failed_requests', 'created_at', 'updated_at'
    ]
    
    def success_rate_display(self, obj):
        """Display success rate"""
        rate = obj.get_success_rate()
        if isinstance(rate, (int, float)):
            color = 'green' if rate >= 80 else 'orange' if rate >= 60 else 'red'
            formatted_rate = f"{rate:.1f}%"
            return format_html(
                '<span style="color: {};">{}</span>',
                color, formatted_rate
            )
        return "-"
    success_rate_display.short_description = 'Success Rate'


# Custom admin site configuration
class ContentAcquisitionAdminSite(admin.AdminSite):
    """Custom admin site for content acquisition"""
    
    site_header = "VeriFast Content Acquisition Admin"
    site_title = "Content Acquisition"
    index_title = "Content Acquisition Management"
    
    def index(self, request, extra_context=None):
        """Custom admin index with acquisition overview"""
        extra_context = extra_context or {}
        
        # Add acquisition statistics to context
        extra_context.update({
            'total_sources': ContentSource.objects.count(),
            'active_sources': ContentSource.objects.filter(is_active=True).count(),
            'recent_jobs': ContentAcquisitionJob.objects.order_by('-created_at')[:5],
        })
        
        return super().index(request, extra_context)


# Register custom admin site
content_acquisition_admin = ContentAcquisitionAdminSite(name='content_acquisition_admin')