from __future__ import annotations
from typing import Optional
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta


class CustomUser(AbstractUser):
    current_wpm: models.PositiveIntegerField = models.PositiveIntegerField(
        default=250, 
        help_text=_("User's current words-per-minute reading speed."),
        verbose_name=_("Current WPM")
    )
    max_wpm: models.PositiveIntegerField = models.PositiveIntegerField(
        default=250, 
        help_text=_("User's highest achieved words-per-minute."),
        verbose_name=_("Maximum WPM")
    )
    total_xp: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, 
        help_text=_("Total accumulated experience points (XP)."),
        verbose_name=_("Total XP")
    )
    current_xp_points: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, 
        help_text=_("Spendable experience points."),
        verbose_name=_("Current XP Points")
    )
    negative_xp_points: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, 
        help_text=_("Accumulated negative XP for admin tracking."),
        verbose_name=_("Negative XP Points")
    )
    last_successful_wpm_used: models.PositiveIntegerField = models.PositiveIntegerField(
        default=250,
        help_text=_("The WPM setting used on the last successfully completed quiz."),
        verbose_name=_("Last Successful WPM Used")
    )
    ad_free_articles_count: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, 
        help_text=_("Number of ad-free articles the user can access."),
        verbose_name=_("Ad-free Articles Count")
    )

    # Premium Font Features
    has_font_opensans: models.BooleanField = models.BooleanField(
        default=False, help_text=_("User has purchased OpenSans font option.")
    )
    has_font_opendyslexic: models.BooleanField = models.BooleanField(
        default=False,
        help_text=_("User has purchased OpenDyslexic font for dyslexia-friendly reading."),
    )
    has_font_roboto: models.BooleanField = models.BooleanField(
        default=False, help_text=_("User has purchased Roboto font option.")
    )
    has_font_merriweather: models.BooleanField = models.BooleanField(
        default=False, help_text=_("User has purchased Merriweather font option.")
    )
    has_font_playfair: models.BooleanField = models.BooleanField(
        default=False, help_text=_("User has purchased Playfair Display font option.")
    )

    # Granular Word Chunking Features
    has_2word_chunking: models.BooleanField = models.BooleanField(
        default=False, help_text=_("User has purchased 2-word chunking capability.")
    )
    has_3word_chunking: models.BooleanField = models.BooleanField(
        default=False, help_text=_("User has purchased 3-word chunking capability.")
    )
    has_4word_chunking: models.BooleanField = models.BooleanField(
        default=False, help_text=_("User has purchased 4-word chunking capability.")
    )
    has_5word_chunking: models.BooleanField = models.BooleanField(
        default=False, help_text=_("User has purchased 5-word chunking capability.")
    )

    # Smart Reading Features
    has_smart_connector_grouping: models.BooleanField = models.BooleanField(
        default=False,
        help_text=_("User has purchased smart connector grouping (groups stop words like 'the dragon')."),
    )
    has_smart_symbol_handling: models.BooleanField = models.BooleanField(
        default=False,
        help_text=_("User has purchased smart symbol handling (elegant punctuation display)."),
    )

    # XP Tracking and Statistics
    last_xp_earned: Optional[models.DateTimeField] = models.DateTimeField(
        null=True, blank=True, help_text=_("Timestamp of when user last earned XP.")
    )
    xp_earning_streak: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, help_text=_("Current streak of consecutive days earning XP.")
    )
    lifetime_xp_earned: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, help_text=_("Total XP earned throughout user's lifetime.")
    )
    lifetime_xp_spent: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, help_text=_("Total XP spent throughout user's lifetime.")
    )
    perfect_quiz_count: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, help_text=_("Number of perfect (100%) quiz scores achieved.")
    )
    quiz_attempts_count: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, help_text=_("Total number of quiz attempts made.")
    )

    # Personalization
    preferred_language: models.CharField = models.CharField(
        max_length=10,
        default="en",
        help_text=_("User's preferred language for the UI and content (e.g., 'en', 'es')."),
    )
    theme: models.CharField = models.CharField(
        max_length=20,
        default="light",
        help_text=_("User's preferred visual theme (e.g., 'light', 'dark')."),
    )

    # LLM and API Settings
    llm_api_key_encrypted: Optional[models.CharField] = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("User's encrypted API key for a preferred LLM provider."),
    )
    preferred_llm_model: Optional[models.CharField] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("The specific LLM model the user prefers to use."),
    )

    def __str__(self):
        return self.username


class TagQuerySet(models.QuerySet):
    def with_counts(self):
        return self.annotate(
            total_quiz_attempts=models.Count("article__quizattempt"),
            total_comments=models.Count("article__comments"),
            avg_quiz_score=models.Avg("article__quizattempt__score"),
            recent_activity=models.Count(
                "article__quizattempt",
                filter=models.Q(
                    article__quizattempt__timestamp__gte=timezone.now()
                    - timedelta(days=7)
                ),
            ),
        )

    def with_trend_score(self, days: int = 7):
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.annotate(
            recent_quiz_attempts=models.Count(
                "article__quizattempt",
                filter=models.Q(article__quizattempt__timestamp__gte=cutoff_date),
            ),
            recent_comments=models.Count(
                "article__comments",
                filter=models.Q(article__comments__timestamp__gte=cutoff_date),
            ),
            trend_score=models.Count(
                "article__quizattempt",
                filter=models.Q(article__quizattempt__timestamp__gte=cutoff_date),
            )
            + models.Count(
                "article__comments",
                filter=models.Q(article__comments__timestamp__gte=cutoff_date),
            ),
        )

    def with_co_occurrence_data(self, articles_with_tag_q: models.Q):
        return self.annotate(
            co_occurrence_count=models.Count("article", filter=articles_with_tag_q),
            relationship_strength=models.Count("article", filter=articles_with_tag_q)
            * 100.0
            / models.Count("article", filter=articles_with_tag_q),
        )


class Tag(models.Model):
    objects = TagQuerySet.as_manager()

    name: models.CharField = models.CharField(max_length=50, unique=True)
    slug: models.SlugField = models.SlugField(max_length=50, unique=True, blank=True)
    description: Optional[models.TextField] = models.TextField(null=True, blank=True)

    # Wikipedia integration
    wikipedia_url: Optional[models.URLField] = models.URLField(null=True, blank=True)
    wikipedia_content: Optional[models.TextField] = models.TextField(
        null=True, blank=True
    )
    is_validated: models.BooleanField = models.BooleanField(default=False)

    # Statistics
    article_count: models.PositiveIntegerField = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    last_updated: models.DateTimeField = models.DateTimeField(auto_now=True)

    # Annotated fields (for mypy)
    total_quiz_attempts: int
    total_comments: int
    avg_quiz_score: float
    recent_activity: int
    recent_quiz_attempts: int
    recent_comments: int
    trend_score: float
    co_occurrence_count: int
    relationship_strength: float
    id: int
    article_set: "models.Manager[Article]"

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_validated"]),
            models.Index(fields=["-article_count"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("verifast_app:tag_detail", kwargs={"tag_name": self.name})

    def update_article_count(self):
        """Update the cached article count"""
        self.article_count = self.article_set.filter(
            processing_status="complete"
        ).count()
        self.save(update_fields=["article_count"])

    def __str__(self):
        return self.name


class Article(models.Model):
    url: Optional[models.URLField] = models.URLField(
        max_length=500, unique=True, null=True
    )
    title: models.CharField = models.CharField(max_length=200)
    content: models.TextField = models.TextField()
    image_url: Optional[models.URLField] = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL of the article's main image.",
    )
    language: models.CharField = models.CharField(max_length=10, default="en")
    processing_status: models.CharField = models.CharField(
        max_length=20, default="pending"
    )
    quiz_data: Optional[models.JSONField] = models.JSONField(null=True, blank=True)
    raw_content: Optional[models.TextField] = models.TextField(
        blank=True,
        null=True,
        help_text="Original raw content of the article before processing.",
    )
    source: models.CharField = models.CharField(
        max_length=100, default="user_submission"
    )
    publication_date: Optional[models.DateTimeField] = models.DateTimeField(
        null=True, blank=True
    )

    # Article type for Wikipedia integration
    ARTICLE_TYPE_CHOICES = [
        ("regular", "Regular Article"),
        ("wikipedia", "Wikipedia Article"),
    ]
    article_type: models.CharField = models.CharField(
        max_length=20,
        choices=ARTICLE_TYPE_CHOICES,
        default="regular",
        help_text="Type of article: regular user submission or Wikipedia article",
    )

    # Additional fields for content analysis
    word_count: Optional[models.PositiveIntegerField] = models.PositiveIntegerField(
        null=True, blank=True
    )
    letter_count: Optional[models.PositiveIntegerField] = models.PositiveIntegerField(
        null=True, blank=True
    )
    summary: Optional[models.TextField] = models.TextField(
        blank=True, null=True, help_text="Article summary or excerpt"
    )

    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    user: Optional[models.ForeignKey] = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    llm_model_used: Optional[models.CharField] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The LLM model used for processing this article.",
    )
    reading_level: Optional[models.FloatField] = models.FloatField(
        null=True, blank=True
    )
    tags: models.ManyToManyField = models.ManyToManyField("Tag", blank=True)
    
    # New fields for automated content acquisition
    ACQUISITION_SOURCE_CHOICES = [
        ('manual', 'Manual Submission'),
        ('rss', 'RSS Feed'),
        ('newsdata_api', 'NewsData.io API'),
        ('scraping', 'Web Scraping'),
    ]
    acquisition_source: models.CharField = models.CharField(
        max_length=50,
        choices=ACQUISITION_SOURCE_CHOICES,
        default='manual',
        help_text=_("Source method used to acquire this article."),
        verbose_name=_("Acquisition Source")
    )
    
    source_url: Optional[models.URLField] = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text=_("Original URL where the article was acquired from."),
        verbose_name=_("Source URL")
    )
    
    topic_category: models.CharField = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Automatically detected topic category (politics, business, etc.)."),
        verbose_name=_("Topic Category")
    )
    
    geographic_focus: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Geographic region or country focus of the article."),
        verbose_name=_("Geographic Focus")
    )
    
    acquisition_timestamp: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        help_text=_("Timestamp when the article was acquired by the system."),
        verbose_name=_("Acquisition Timestamp")
    )
    
    content_quality_score: models.FloatField = models.FloatField(
        default=0.0,
        help_text=_("Automated quality score for the article content (0.0-1.0)."),
        verbose_name=_("Content Quality Score")
    )
    
    duplicate_check_hash: models.CharField = models.CharField(
        max_length=64,
        blank=True,
        help_text=_("Hash for duplicate detection based on content similarity."),
        verbose_name=_("Duplicate Check Hash")
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.article_type == "wikipedia":
            return reverse("verifast_app:wikipedia_article", kwargs={"pk": self.pk})
        return reverse("verifast_app:article_detail", kwargs={"pk": self.pk})

    def is_wikipedia_article(self):
        """Check if this is a Wikipedia article."""
        return self.article_type == "wikipedia"

    def get_display_title(self):
        """Get display title with Wikipedia prefix if applicable."""
        if self.is_wikipedia_article():
            return f"Wikipedia: {self.title.replace('Wikipedia: ', '')}"
        return self.title

    def get_source_display(self):
        """Get formatted source display."""
        if self.is_wikipedia_article():
            return "Wikipedia"
        return self.source or "User Submission"

    def can_generate_quiz(self):
        """Check if article can have a quiz generated."""
        return (
            self.processing_status == "complete"
            and self.content
            and len(self.content.split()) >= 50  # Minimum word count for quiz
        )

    def get_reading_time_estimate(self, wpm=250):
        """Estimate reading time in minutes."""
        if self.word_count:
            return max(1, round(self.word_count / wpm))
        elif self.content:
            word_count = len(self.content.split())
            return max(1, round(word_count / wpm))
        return 1


class Comment(models.Model):
    article: models.ForeignKey = models.ForeignKey(
        "Article", on_delete=models.CASCADE, related_name="comments"
    )
    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    content: models.TextField = models.TextField()
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    parent_comment: Optional[models.ForeignKey] = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )

    def __str__(self):
        return f"Comment by {self.user} on {self.article.title}"


class QuizAttempt(models.Model):
    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    article: models.ForeignKey = models.ForeignKey("Article", on_delete=models.CASCADE)
    score: models.FloatField = models.FloatField()
    wpm_used: models.IntegerField = models.IntegerField()
    xp_awarded: models.IntegerField = models.IntegerField()
    result: Optional[models.JSONField] = models.JSONField(
        null=True, blank=True, help_text="Detailed results of the quiz attempt."
    )
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    reading_time_seconds: Optional[models.PositiveIntegerField] = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
            help_text="Time spent reading the article in seconds.",
        )
    )
    quiz_time_seconds: Optional[models.PositiveIntegerField] = (
        models.PositiveIntegerField(
            null=True, blank=True, help_text="Time spent taking the quiz in seconds."
        )
    )
    quiz_rating: Optional[models.PositiveSmallIntegerField] = (
        models.PositiveSmallIntegerField(
            null=True,
            blank=True,
            help_text="User's rating of the quiz (e.g., 1-5 stars).",
        )
    )
    quiz_feedback: Optional[models.TextField] = models.TextField(
        blank=True, null=True, help_text="User's feedback on the quiz."
    )

    def __str__(self):
        return f"{self.user.username} - {self.article.title} - {self.xp_awarded} XP"


class CommentInteraction(models.Model):
    class InteractionType(models.TextChoices):
        BRONZE = "BRONZE", "Bronze"
        SILVER = "SILVER", "Silver"
        GOLD = "GOLD", "Gold"
        REPORT_TROLL = "REPORT_TROLL", "Report: Troll"
        REPORT_BAD = "REPORT_BAD", "Report: Bad"
        REPORT_SHIT = "REPORT_SHIT", "Report: Shit"

    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The user who performed the interaction.",
    )
    comment: models.ForeignKey = models.ForeignKey(
        "Comment",
        on_delete=models.CASCADE,
        help_text="The comment being interacted with.",
    )
    interaction_type: models.CharField = models.CharField(
        max_length=15,
        choices=InteractionType.choices,
        help_text="Type of interaction (e.g., Bronze, Silver, Gold, Report Tiers).",
    )
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    xp_cost: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0, help_text="XP cost incurred by the user for this interaction."
    )

    class Meta:
        unique_together = ("user", "comment", "interaction_type")

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} on {self.comment.id}"


class AdminCorrectionDataset(models.Model):
    original_article_url: Optional[models.URLField] = models.URLField(
        max_length=500,
        help_text="The URL of the original article.",
        null=True,
        blank=True,
    )
    original_content_hash: Optional[models.CharField] = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of the original content to ensure integrity.",
        null=True,
        blank=True,
    )
    corrected_content: Optional[models.TextField] = models.TextField(
        help_text="The corrected version of the text content.", null=True, blank=True
    )
    correction_type: Optional[models.CharField] = models.CharField(
        max_length=100,
        help_text="Type of correction (e.g., 'summary', 'quiz', 'content').",
        null=True,
        blank=True,
    )
    admin_user: Optional[models.ForeignKey] = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"is_staff": True},
        help_text="The admin user who made the correction.",
    )
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Correction for {self.original_article_url} by {self.admin_user}"


class XPTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("EARN", "Earned"),
        ("SPEND", "Spent"),
    ]

    SOURCES = [
        ("quiz_completion", "Quiz Completion"),
        ("perfect_score_bonus", "Perfect Score Bonus"),
        ("wpm_improvement", "WPM Improvement"),
        ("reading_streak", "Reading Streak"),
        ("comment_post", "Comment Posted"),
        ("comment_reply", "Comment Reply"),
        ("interaction_bronze", "Bronze Interaction"),
        ("interaction_silver", "Silver Interaction"),
        ("interaction_gold", "Gold Interaction"),
        ("interaction_reward", "Interaction Reward"),
        ("feature_purchase", "Feature Purchase"),
        ("admin_adjustment", "Admin Adjustment"),
    ]

    user: models.ForeignKey = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="xp_transactions",
        help_text="The user involved in this XP transaction.",
    )
    transaction_type: models.CharField = models.CharField(
        max_length=5,
        choices=TRANSACTION_TYPES,
        help_text="Whether this transaction earned or spent XP.",
    )
    amount: models.IntegerField = models.IntegerField(
        help_text="XP amount (positive for earn, negative for spend)."
    )
    source: models.CharField = models.CharField(
        max_length=20,
        choices=SOURCES,
        help_text="The source/reason for this XP transaction.",
    )
    description: models.TextField = models.TextField(
        help_text="Detailed description of the transaction."
    )
    balance_after: models.PositiveIntegerField = models.PositiveIntegerField(
        help_text="User's spendable XP balance after this transaction."
    )
    timestamp: models.DateTimeField = models.DateTimeField(
        auto_now_add=True, help_text="When this transaction occurred."
    )

    # Optional references to related objects
    quiz_attempt: Optional[models.ForeignKey] = models.ForeignKey(
        "QuizAttempt",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Quiz attempt that triggered this transaction (if applicable).",
    )
    comment: Optional[models.ForeignKey] = models.ForeignKey(
        "Comment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Comment that triggered this transaction (if applicable).",
    )
    feature_purchased: Optional[models.CharField] = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Name of feature purchased (if applicable).",
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["transaction_type", "-timestamp"]),
            models.Index(fields=["source", "-timestamp"]),
        ]
        verbose_name = "XP Transaction"
        verbose_name_plural = "XP Transactions"

    def __str__(self):
        sign = "+" if self.amount > 0 else ""
        return f"{self.user.username}: {sign}{self.amount} XP ({self.get_source_display()})"


class FeaturePurchase(models.Model):
    user: models.ForeignKey = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="feature_purchases",
        help_text="The user who purchased the feature.",
    )
    feature_name: models.CharField = models.CharField(
        max_length=50, help_text="Internal name of the purchased feature."
    )
    feature_display_name: models.CharField = models.CharField(
        max_length=100, help_text="Human-readable name of the purchased feature."
    )
    xp_cost: models.PositiveIntegerField = models.PositiveIntegerField(
        help_text="XP cost of the feature at time of purchase."
    )
    purchase_date: models.DateTimeField = models.DateTimeField(
        auto_now_add=True, help_text="When the feature was purchased."
    )
    transaction: models.ForeignKey = models.ForeignKey(
        "XPTransaction",
        on_delete=models.CASCADE,
        help_text=_("The XP transaction record for this purchase."),
    )

    class Meta:
        ordering = ["-purchase_date"]
        unique_together = ("user", "feature_name")
        indexes = [
            models.Index(fields=["user", "-purchase_date"]),
            models.Index(fields=["feature_name", "-purchase_date"]),
        ]
        verbose_name = "Feature Purchase"
        verbose_name_plural = "Feature Purchases"

    def __str__(self):
        return f"{self.user.username} purchased {self.feature_display_name} for {self.xp_cost} XP"


class ContentAcquisitionLog(models.Model):
    """Log entries for automated content acquisition cycles"""
    
    ACQUISITION_TYPES = [
        ('rss', 'RSS Feed'),
        ('newsdata_api', 'NewsData.io API'),
        ('scraping', 'Web Scraping'),
        ('full_cycle', 'Full Acquisition Cycle'),
    ]
    
    timestamp: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When this acquisition cycle started."),
        verbose_name=_("Timestamp")
    )
    acquisition_type: models.CharField = models.CharField(
        max_length=20,
        choices=ACQUISITION_TYPES,
        help_text=_("Type of acquisition performed."),
        verbose_name=_("Acquisition Type")
    )
    source_name: models.CharField = models.CharField(
        max_length=100,
        help_text=_("Name of the specific source (e.g., 'BBC News', 'NewsData.io')."),
        verbose_name=_("Source Name")
    )
    articles_acquired: models.IntegerField = models.IntegerField(
        default=0,
        help_text=_("Number of articles successfully acquired."),
        verbose_name=_("Articles Acquired")
    )
    articles_processed: models.IntegerField = models.IntegerField(
        default=0,
        help_text=_("Number of articles successfully processed and stored."),
        verbose_name=_("Articles Processed")
    )
    articles_rejected: models.IntegerField = models.IntegerField(
        default=0,
        help_text=_("Number of articles rejected due to quality or duplication."),
        verbose_name=_("Articles Rejected")
    )
    api_calls_used: models.IntegerField = models.IntegerField(
        default=0,
        help_text=_("Number of API calls consumed during this acquisition."),
        verbose_name=_("API Calls Used")
    )
    errors_encountered: models.JSONField = models.JSONField(
        default=list,
        help_text=_("List of errors encountered during acquisition."),
        verbose_name=_("Errors Encountered")
    )
    processing_time_seconds: models.FloatField = models.FloatField(
        help_text=_("Total time taken for this acquisition cycle in seconds."),
        verbose_name=_("Processing Time (seconds)")
    )
    
    # Additional metadata
    language_distribution: models.JSONField = models.JSONField(
        default=dict,
        help_text=_("Distribution of articles by language (e.g., {'en': 10, 'es': 5})."),
        verbose_name=_("Language Distribution")
    )
    topic_distribution: models.JSONField = models.JSONField(
        default=dict,
        help_text=_("Distribution of articles by topic category."),
        verbose_name=_("Topic Distribution")
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['acquisition_type', '-timestamp']),
            models.Index(fields=['source_name', '-timestamp']),
        ]
        verbose_name = _("Content Acquisition Log")
        verbose_name_plural = _("Content Acquisition Logs")
    
    def __str__(self):
        return f"{self.acquisition_type} - {self.source_name} ({self.articles_processed} articles)"
    
    @property
    def success_rate(self):
        """Calculate the success rate of article processing"""
        if self.articles_acquired == 0:
            return 0.0
        return (self.articles_processed / self.articles_acquired) * 100
