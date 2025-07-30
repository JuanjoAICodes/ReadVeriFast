"""
API Serializers for VeriFast
Handles serialization/deserialization for REST API endpoints
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Article, QuizAttempt, Comment, CommentInteraction, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    class Meta:
        model = Tag
        fields = ['id', 'name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password_confirm', 
            'preferred_language', 'theme'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(_("Passwords don't match"))
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""
    reading_stats = serializers.SerializerMethodField()
    premium_features = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'current_wpm', 'max_wpm',
            'total_xp', 'current_xp_points', 'preferred_language',
            'theme', 'reading_stats', 'premium_features',
            # XP tracking fields
            'last_xp_earned', 'xp_earning_streak', 'lifetime_xp_earned',
            'lifetime_xp_spent', 'perfect_quiz_count', 'quiz_attempts_count'
        ]
        read_only_fields = [
            'id', 'total_xp', 'last_xp_earned', 'xp_earning_streak',
            'lifetime_xp_earned', 'lifetime_xp_spent', 'perfect_quiz_count',
            'quiz_attempts_count'
        ]
    
    def get_reading_stats(self, obj):
        """Get user reading statistics"""
        quiz_attempts = QuizAttempt.objects.filter(user=obj)
        successful_attempts = quiz_attempts.filter(score__gte=60)
        
        return {
            'articles_read': successful_attempts.count(),
            'total_quiz_attempts': quiz_attempts.count(),
            'average_score': quiz_attempts.aggregate(
                avg_score=serializers.models.Avg('score')
            )['avg_score'] or 0,
            'total_reading_time': sum(
                attempt.reading_time_seconds or 0 
                for attempt in quiz_attempts
            ),
            'reading_streak': self._calculate_reading_streak(obj)
        }
    
    def _calculate_reading_streak(self, user):
        """Calculate current reading streak"""
        # Simple implementation - can be enhanced
        recent_attempts = QuizAttempt.objects.filter(
            user=user, 
            score__gte=60
        ).order_by('-timestamp')[:7]
        return len(recent_attempts)
    
    def get_premium_features(self, obj):
        """Get user's premium feature ownership status"""
        return {
            # Premium fonts
            'fonts': {
                'opensans': obj.has_font_opensans,
                'opendyslexic': obj.has_font_opendyslexic,
                'roboto': obj.has_font_roboto,
                'merriweather': obj.has_font_merriweather,
                'playfair': obj.has_font_playfair,
            },
            # Word chunking capabilities
            'chunking': {
                '2_words': obj.has_2word_chunking,
                '3_words': obj.has_3word_chunking,
                '4_words': obj.has_4word_chunking,
                '5_words': obj.has_5word_chunking,
            },
            # Smart reading features
            'smart_features': {
                'connector_grouping': obj.has_smart_connector_grouping,
                'symbol_handling': obj.has_smart_symbol_handling,
            }
        }


class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer for article list view"""
    tags = TagSerializer(many=True, read_only=True)
    quiz_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'source', 'publication_date',
            'reading_level', 'language', 'tags', 'quiz_available',
            'processing_status'
        ]
    
    def get_quiz_available(self, obj):
        return bool(obj.quiz_data and obj.processing_status == 'complete')


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Serializer for article detail view"""
    tags = TagSerializer(many=True, read_only=True)
    quiz_data = serializers.JSONField(read_only=True)
    user_has_completed_quiz = serializers.SerializerMethodField()
    user_best_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'image_url', 'source',
            'publication_date', 'reading_level', 'language',
            'tags', 'quiz_data', 'user_has_completed_quiz',
            'user_best_score', 'processing_status'
        ]
    
    def get_user_has_completed_quiz(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return QuizAttempt.objects.filter(
                user=request.user, 
                article=obj,
                score__gte=60
            ).exists()
        return False
    
    def get_user_best_score(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            best_attempt = QuizAttempt.objects.filter(
                user=request.user, 
                article=obj
            ).order_by('-score').first()
            return best_attempt.score if best_attempt else None
        return None


class ArticleSubmissionSerializer(serializers.Serializer):
    """Serializer for article URL submission"""
    url = serializers.URLField()
    
    def validate_url(self, value):
        # Check if article already exists
        if Article.objects.filter(url=value).exists():
            raise serializers.ValidationError("Article with this URL already exists")
        return value


class QuizQuestionSerializer(serializers.Serializer):
    """Serializer for quiz questions (without correct answers)"""
    question = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())


class QuizSubmissionSerializer(serializers.Serializer):
    """Serializer for quiz submission"""
    answers = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=3),
        min_length=5,
        max_length=5
    )
    wmp_used = serializers.IntegerField(min_value=50, max_value=1000)
    reading_time_seconds = serializers.IntegerField(min_value=1, required=False)
    quiz_time_seconds = serializers.IntegerField(min_value=1, required=False)


class QuizResultSerializer(serializers.ModelSerializer):
    """Serializer for quiz results"""
    xp_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'score', 'wmp_used', 'xp_awarded', 'timestamp',
            'reading_time_seconds', 'quiz_time_seconds', 'xp_breakdown'
        ]
    
    def get_xp_breakdown(self, obj):
        """Provide XP calculation breakdown"""
        if obj.article and obj.article.reading_level:
            complexity_factor = obj.article.reading_level
            score_xp = obj.score * 0.5  # 50% of score as XP
            speed_xp = obj.wmp_used * 2 * complexity_factor
            return {
                'score_xp': int(score_xp),
                'speed_xp': int(speed_xp),
                'complexity_factor': complexity_factor,
                'total_xp': obj.xp_awarded
            }
        return {'total_xp': obj.xp_awarded}


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for comments"""
    class Meta:
        model = CustomUser
        fields = ['id', 'username']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments"""
    user = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    user_interaction = serializers.SerializerMethodField()
    interaction_counts = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'timestamp', 'user', 'parent_comment',
            'replies', 'user_interaction', 'interaction_counts'
        ]
        read_only_fields = ['id', 'timestamp', 'user']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(
                obj.replies.all(), 
                many=True, 
                context=self.context
            ).data
        return []
    
    def get_user_interaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            interaction = CommentInteraction.objects.filter(
                user=request.user,
                comment=obj
            ).first()
            return interaction.interaction_type if interaction else None
        return None
    
    def get_interaction_counts(self, obj):
        interactions = CommentInteraction.objects.filter(comment=obj)
        return {
            'bronze': interactions.filter(interaction_type='BRONZE').count(),
            'silver': interactions.filter(interaction_type='SILVER').count(),
            'gold': interactions.filter(interaction_type='GOLD').count(),
            'reports': interactions.filter(interaction_type='REPORT').count(),
        }


class CommentInteractionSerializer(serializers.Serializer):
    """Serializer for comment interactions"""
    interaction_type = serializers.ChoiceField(
        choices=['BRONZE', 'SILVER', 'GOLD', 'REPORT']
    )


class UserStatsSerializer(serializers.Serializer):
    """Serializer for detailed user statistics"""
    total_xp = serializers.IntegerField()
    current_xp_points = serializers.IntegerField()
    current_wpm = serializers.IntegerField()
    max_wpm = serializers.IntegerField()
    articles_read = serializers.IntegerField()
    total_quiz_attempts = serializers.IntegerField()
    average_score = serializers.FloatField()
    reading_streak = serializers.IntegerField()
    comments_posted = serializers.IntegerField()
    interactions_given = serializers.IntegerField()
    interactions_received = serializers.IntegerField()