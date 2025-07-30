"""
Content Acquisition Models for VeriFast
Models for managing automated content sources and acquisition
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class ContentSource(models.Model):
    """Model for managing content sources (RSS feeds, APIs, etc.)"""
    
    SOURCE_TYPES = [
        ('rss', 'RSS Feed'),
        ('newsdata_api', 'NewsData.io API'),
        ('scraper', 'Web Scraper'),
        ('manual', 'Manual Submission')
    ]
    
    LANGUAGES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('both', 'Both Languages')
    ]
    
    PRIORITIES = [
        ('low', 'Low Priority'),
        ('normal', 'Normal Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical Priority')
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('rate_limited', 'Rate Limited'),
        ('maintenance', 'Maintenance')
    ]
    
    # Basic Information
    name = models.CharField(max_length=100, unique=True, help_text="Unique name for the content source")
    description = models.TextField(blank=True, help_text="Description of the content source")
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, help_text="Type of content source")
    url = models.URLField(help_text="Primary URL for the content source")
    language = models.CharField(max_length=10, choices=LANGUAGES, default='en', help_text="Language(s) supported by this source")
    
    # Configuration
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='normal', help_text="Priority level for content acquisition")
    is_active = models.BooleanField(default=True, help_text="Whether this source is currently active")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text="Current operational status")
    
    # Rate Limiting and Quotas
    requests_per_hour = models.PositiveIntegerField(default=60, help_text="Maximum requests per hour for this source")
    requests_per_day = models.PositiveIntegerField(default=1000, help_text="Maximum requests per day for this source")
    current_hour_requests = models.PositiveIntegerField(default=0, help_text="Requests made in current hour")
    current_day_requests = models.PositiveIntegerField(default=0, help_text="Requests made in current day")
    last_request_time = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last request")
    
    # Health Monitoring
    last_successful_fetch = models.DateTimeField(null=True, blank=True, help_text="Last successful content fetch")
    last_error = models.TextField(blank=True, help_text="Last error message encountered")
    consecutive_failures = models.PositiveIntegerField(default=0, help_text="Number of consecutive failures")
    total_articles_fetched = models.PositiveIntegerField(default=0, help_text="Total articles successfully fetched")
    
    # Configuration Data
    config_data = models.JSONField(default=dict, blank=True, help_text="Source-specific configuration data")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'content_sources'
        verbose_name = 'Content Source'
        verbose_name_plural = 'Content Sources'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
    
    def can_make_request(self):
        """Check if source can make a request based on rate limits"""
        now = timezone.now()
        
        # Reset hourly counter if needed
        if self.last_request_time and (now - self.last_request_time).total_seconds() >= 3600:
            self.current_hour_requests = 0
        
        # Reset daily counter if needed
        if self.last_request_time and (now - self.last_request_time).days >= 1:
            self.current_day_requests = 0
        
        # Check rate limits
        if self.current_hour_requests >= self.requests_per_hour:
            return False, "Hourly rate limit exceeded"
        
        if self.current_day_requests >= self.requests_per_day:
            return False, "Daily rate limit exceeded"
        
        # Check if source is active and healthy
        if not self.is_active:
            return False, "Source is inactive"
        
        if self.status in ['error', 'maintenance']:
            return False, f"Source status: {self.status}"
        
        if self.consecutive_failures >= 5:
            return False, "Too many consecutive failures"
        
        return True, "OK"
    
    def record_request(self, success=True, error_message=""):
        """Record a request attempt and update counters"""
        now = timezone.now()
        
        # Update request counters
        self.current_hour_requests += 1
        self.current_day_requests += 1
        self.last_request_time = now
        
        if success:
            self.last_successful_fetch = now
            self.consecutive_failures = 0
            self.status = 'active'
            self.last_error = ""
            self.total_articles_fetched += 1
        else:
            self.consecutive_failures += 1
            self.last_error = error_message
            
            # Update status based on failure count
            if self.consecutive_failures >= 5:
                self.status = 'error'
            elif self.consecutive_failures >= 3:
                self.status = 'rate_limited'
        
        self.save(update_fields=[
            'current_hour_requests', 'current_day_requests', 'last_request_time',
            'last_successful_fetch', 'consecutive_failures', 'status', 'last_error',
            'total_articles_fetched', 'updated_at'
        ])
    
    def get_health_score(self):
        """Calculate health score (0-100) based on recent performance"""
        if not self.last_successful_fetch:
            return 0
        
        now = timezone.now()
        hours_since_success = (now - self.last_successful_fetch).total_seconds() / 3600
        
        # Base score starts at 100
        score = 100
        
        # Reduce score based on time since last success
        if hours_since_success > 24:
            score -= 50
        elif hours_since_success > 12:
            score -= 25
        elif hours_since_success > 6:
            score -= 10
        
        # Reduce score based on consecutive failures
        score -= (self.consecutive_failures * 10)
        
        # Reduce score if inactive
        if not self.is_active:
            score -= 30
        
        # Reduce score based on status
        if self.status == 'error':
            score -= 40
        elif self.status == 'rate_limited':
            score -= 20
        elif self.status == 'maintenance':
            score -= 15
        
        return max(0, min(100, score))


class ContentAcquisitionJob(models.Model):
    """Model for tracking content acquisition jobs"""
    
    JOB_TYPES = [
        ('scheduled', 'Scheduled Acquisition'),
        ('manual', 'Manual Trigger'),
        ('retry', 'Retry Failed'),
        ('backfill', 'Backfill Historical')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]
    
    # Job Information
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, help_text="Type of acquisition job")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current job status")
    source = models.ForeignKey(ContentSource, on_delete=models.CASCADE, help_text="Content source for this job")
    
    # Execution Details
    started_at = models.DateTimeField(null=True, blank=True, help_text="Job start time")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="Job completion time")
    error_message = models.TextField(blank=True, help_text="Error message if job failed")
    
    # Results
    articles_found = models.PositiveIntegerField(default=0, help_text="Number of articles found")
    articles_processed = models.PositiveIntegerField(default=0, help_text="Number of articles successfully processed")
    articles_duplicated = models.PositiveIntegerField(default=0, help_text="Number of duplicate articles skipped")
    articles_rejected = models.PositiveIntegerField(default=0, help_text="Number of articles rejected by quality filters")
    
    # Configuration
    config_data = models.JSONField(default=dict, blank=True, help_text="Job-specific configuration")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'content_acquisition_jobs'
        verbose_name = 'Content Acquisition Job'
        verbose_name_plural = 'Content Acquisition Jobs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.source.name} ({self.status})"
    
    def start_job(self):
        """Mark job as started"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])
    
    def complete_job(self, articles_found=0, articles_processed=0, articles_duplicated=0, articles_rejected=0):
        """Mark job as completed with results"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.articles_found = articles_found
        self.articles_processed = articles_processed
        self.articles_duplicated = articles_duplicated
        self.articles_rejected = articles_rejected
        self.save(update_fields=[
            'status', 'completed_at', 'articles_found', 'articles_processed',
            'articles_duplicated', 'articles_rejected', 'updated_at'
        ])
    
    def fail_job(self, error_message):
        """Mark job as failed with error message"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message', 'updated_at'])
    
    def get_duration(self):
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (timezone.now() - self.started_at).total_seconds()
        return 0
    
    def get_success_rate(self):
        """Get success rate as percentage"""
        if self.articles_found == 0:
            return 0
        return (self.articles_processed / self.articles_found) * 100


class ContentFingerprint(models.Model):
    """Model for storing content fingerprints to detect duplicates"""
    
    # Content Identification
    url_hash = models.CharField(max_length=64, db_index=True, help_text="Hash of the article URL")
    title_hash = models.CharField(max_length=64, db_index=True, help_text="Hash of the article title")
    content_hash = models.CharField(max_length=64, db_index=True, help_text="Hash of the article content")
    
    # Metadata
    language = models.CharField(max_length=10, db_index=True, help_text="Article language")
    topic_category = models.CharField(max_length=50, blank=True, db_index=True, help_text="Detected topic category")
    source = models.ForeignKey(ContentSource, on_delete=models.CASCADE, help_text="Source that provided this content")
    article = models.ForeignKey('Article', on_delete=models.CASCADE, null=True, blank=True, help_text="Associated article if processed")
    
    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True, help_text="When this content was first seen")
    last_seen = models.DateTimeField(auto_now=True, help_text="When this content was last encountered")
    
    class Meta:
        db_table = 'content_fingerprints'
        verbose_name = 'Content Fingerprint'
        verbose_name_plural = 'Content Fingerprints'
        indexes = [
            models.Index(fields=['url_hash', 'language']),
            models.Index(fields=['title_hash', 'language']),
            models.Index(fields=['content_hash', 'language']),
            models.Index(fields=['topic_category', 'language', 'first_seen']),
        ]
        unique_together = [
            ('url_hash', 'title_hash', 'content_hash')
        ]
    
    def __str__(self):
        return f"Fingerprint {self.id} - {self.topic_category} ({self.language})"
    
    @classmethod
    def create_fingerprint(cls, url, title, content, language, topic_category="", source=None):
        """Create a content fingerprint from article data"""
        import hashlib
        
        # Create hashes
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Create or update fingerprint
        fingerprint, created = cls.objects.get_or_create(
            url_hash=url_hash,
            title_hash=title_hash,
            content_hash=content_hash,
            defaults={
                'language': language,
                'topic_category': topic_category,
                'source': source
            }
        )
        
        if not created:
            # Update last_seen timestamp
            fingerprint.last_seen = timezone.now()
            fingerprint.save(update_fields=['last_seen'])
        
        return fingerprint, created
    
    @classmethod
    def is_duplicate(cls, url, title, content, language, topic_category=""):
        """Check if content is a duplicate"""
        import hashlib
        
        # Create hashes
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Check for exact matches
        exact_match = cls.objects.filter(
            url_hash=url_hash,
            title_hash=title_hash,
            content_hash=content_hash
        ).exists()
        
        if exact_match:
            return True, "Exact duplicate found"
        
        # Check for URL duplicates
        url_duplicate = cls.objects.filter(url_hash=url_hash).exists()
        if url_duplicate:
            return True, "URL duplicate found"
        
        # Check for topic saturation (4 articles per topic per day per language)
        if topic_category:
            from django.utils import timezone
            today = timezone.now().date()
            
            topic_count = cls.objects.filter(
                topic_category=topic_category,
                language=language,
                first_seen__date=today
            ).count()
            
            if topic_count >= 4:
                return True, f"Topic saturation: {topic_count} articles for {topic_category} today"
        
        return False, "Not a duplicate"


class AcquisitionMetrics(models.Model):
    """Model for storing acquisition metrics and statistics"""
    
    # Time Period
    date = models.DateField(db_index=True, help_text="Date for these metrics")
    hour = models.PositiveIntegerField(null=True, blank=True, help_text="Hour (0-23) for hourly metrics")
    
    # Source Information
    source = models.ForeignKey(ContentSource, on_delete=models.CASCADE, null=True, blank=True, help_text="Specific source (null for aggregate)")
    language = models.CharField(max_length=10, blank=True, help_text="Language (empty for all languages)")
    
    # Acquisition Metrics
    articles_found = models.PositiveIntegerField(default=0, help_text="Articles found from sources")
    articles_processed = models.PositiveIntegerField(default=0, help_text="Articles successfully processed")
    articles_duplicated = models.PositiveIntegerField(default=0, help_text="Duplicate articles skipped")
    articles_rejected = models.PositiveIntegerField(default=0, help_text="Articles rejected by quality filters")
    
    # Performance Metrics
    total_requests = models.PositiveIntegerField(default=0, help_text="Total API/RSS requests made")
    successful_requests = models.PositiveIntegerField(default=0, help_text="Successful requests")
    failed_requests = models.PositiveIntegerField(default=0, help_text="Failed requests")
    avg_response_time = models.FloatField(default=0.0, help_text="Average response time in seconds")
    
    # Quality Metrics
    avg_content_length = models.PositiveIntegerField(default=0, help_text="Average content length in characters")
    avg_reading_level = models.FloatField(default=0.0, help_text="Average reading level")
    quiz_generation_success_rate = models.FloatField(default=0.0, help_text="Quiz generation success rate")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'acquisition_metrics'
        verbose_name = 'Acquisition Metrics'
        verbose_name_plural = 'Acquisition Metrics'
        unique_together = [
            ('date', 'hour', 'source', 'language')
        ]
        indexes = [
            models.Index(fields=['date', 'source']),
            models.Index(fields=['date', 'language']),
            models.Index(fields=['date', 'hour']),
        ]
    
    def __str__(self):
        source_name = self.source.name if self.source else "All Sources"
        lang_name = self.language if self.language else "All Languages"
        hour_str = f" {self.hour}:00" if self.hour is not None else ""
        return f"{source_name} - {lang_name} - {self.date}{hour_str}"
    
    def get_success_rate(self):
        """Get overall success rate as percentage"""
        if self.articles_found == 0:
            return 0
        return (self.articles_processed / self.articles_found) * 100
    
    def get_request_success_rate(self):
        """Get request success rate as percentage"""
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100