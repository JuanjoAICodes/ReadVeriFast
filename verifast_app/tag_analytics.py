"""
Tag Analytics Service

This module provides analytics and statistics for the tag system,
including popularity calculations, trending analysis, and relationship mapping.
"""

import logging
from datetime import timedelta
from typing import Dict, List, Optional
from django.db.models import Count, Q, Avg, Max, Min
from django.utils import timezone
from django.core.cache import cache
from .models import Tag, Article, QuizAttempt, Comment

logger = logging.getLogger(__name__)


class TagAnalytics:
    """
    Service class for tag analytics and statistics.
    
    Provides methods for calculating tag popularity, trends, relationships,
    and user engagement metrics.
    """
    
    CACHE_TIMEOUT = 3600  # 1 hour cache timeout
    
    def get_tag_popularity_stats(self, limit: int = 50) -> List[Dict]:
        """
        Get tag popularity statistics based on article count and engagement.
        
        Args:
            limit (int): Maximum number of tags to return
            
        Returns:
            List[Dict]: List of tag statistics with popularity metrics
        """
        cache_key = f'tag_popularity_stats_{limit}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Get tags with article counts and engagement metrics
            tags = Tag.objects.filter(
                is_validated=True,
                article_count__gt=0
            ).annotate(
                total_quiz_attempts=Count('article__quizattempt'),
                total_comments=Count('article__comments'),
                avg_quiz_score=Avg('article__quizattempt__score'),
                recent_activity=Count(
                    'article__quizattempt',
                    filter=Q(article__quizattempt__timestamp__gte=timezone.now() - timedelta(days=7))
                )
            ).order_by('-article_count', '-total_quiz_attempts')[:limit]
            
            popularity_stats = []
            
            for tag in tags:
                # Calculate popularity score
                popularity_score = self._calculate_popularity_score(
                    article_count=tag.article_count,
                    quiz_attempts=tag.total_quiz_attempts,
                    comments=tag.total_comments,
                    recent_activity=tag.recent_activity
                )
                
                # Determine popularity tier
                popularity_tier = self._get_popularity_tier(popularity_score)
                
                stats = {
                    'tag': tag,
                    'article_count': tag.article_count,
                    'total_quiz_attempts': tag.total_quiz_attempts or 0,
                    'total_comments': tag.total_comments or 0,
                    'avg_quiz_score': round(tag.avg_quiz_score or 0, 1),
                    'recent_activity': tag.recent_activity or 0,
                    'popularity_score': popularity_score,
                    'popularity_tier': popularity_tier,
                    'engagement_rate': self._calculate_engagement_rate(
                        total_quiz_attempts=tag.total_quiz_attempts or 0,
                        total_comments=tag.total_comments or 0,
                        article_count=tag.article_count
                    )
                }
                
                popularity_stats.append(stats)
            
            # Sort by popularity score
            popularity_stats.sort(key=lambda x: x['popularity_score'], reverse=True)
            
            # Cache the results
            cache.set(cache_key, popularity_stats, self.CACHE_TIMEOUT)
            
            logger.info(f"Generated popularity stats for {len(popularity_stats)} tags")
            return popularity_stats
            
        except Exception as e:
            logger.error(f"Error calculating tag popularity stats: {str(e)}")
            return []
    
    def get_trending_tags(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """
        Get trending tags based on recent activity.
        
        Args:
            days (int): Number of days to look back for trending analysis
            limit (int): Maximum number of trending tags to return
            
        Returns:
            List[Dict]: List of trending tag statistics
        """
        cache_key = f'trending_tags_{days}_{limit}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Get tags with recent activity
            trending_tags = Tag.objects.filter(
                is_validated=True,
                article__quizattempt__timestamp__gte=cutoff_date
            ).annotate(
                recent_quiz_attempts=Count('article__quizattempt', 
                    filter=Q(article__quizattempt__timestamp__gte=cutoff_date)),
                recent_comments=Count('article__comments',
                    filter=Q(article__comments__timestamp__gte=cutoff_date)),
                trend_score=Count('article__quizattempt', 
                    filter=Q(article__quizattempt__timestamp__gte=cutoff_date)) +
                           Count('article__comments',
                    filter=Q(article__comments__timestamp__gte=cutoff_date))
            ).filter(
                trend_score__gt=0
            ).order_by('-trend_score')[:limit]
            
            trending_stats = []
            
            for tag in trending_tags:
                # Calculate trend velocity (activity per day)
                trend_velocity = tag.trend_score / days if days > 0 else 0
                
                stats = {
                    'tag': tag,
                    'recent_quiz_attempts': tag.recent_quiz_attempts,
                    'recent_comments': tag.recent_comments,
                    'trend_score': tag.trend_score,
                    'trend_velocity': round(trend_velocity, 2),
                    'days_analyzed': days
                }
                
                trending_stats.append(stats)
            
            # Cache the results
            cache.set(cache_key, trending_stats, self.CACHE_TIMEOUT // 2)  # Shorter cache for trending
            
            logger.info(f"Generated trending stats for {len(trending_stats)} tags")
            return trending_stats
            
        except Exception as e:
            logger.error(f"Error calculating trending tags: {str(e)}")
            return []
    
    def get_tag_relationships(self, tag: Tag, limit: int = 10) -> List[Dict]:
        """
        Get tags that frequently appear together with the given tag.
        
        Args:
            tag (Tag): The tag to find relationships for
            limit (int): Maximum number of related tags to return
            
        Returns:
            List[Dict]: List of related tags with relationship strength
        """
        cache_key = f'tag_relationships_{tag.id}_{limit}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Find articles that have this tag
            articles_with_tag = Article.objects.filter(
                tags=tag,
                processing_status='complete'
            )
            
            # Find other tags that appear in these articles
            related_tags = Tag.objects.filter(
                article__in=articles_with_tag,
                is_validated=True
            ).exclude(
                id=tag.id
            ).annotate(
                co_occurrence_count=Count('article', 
                    filter=Q(article__in=articles_with_tag)),
                relationship_strength=Count('article', 
                    filter=Q(article__in=articles_with_tag)) * 100.0 / articles_with_tag.count()
            ).filter(
                co_occurrence_count__gt=0
            ).order_by('-co_occurrence_count')[:limit]
            
            relationships = []
            
            for related_tag in related_tags:
                relationship = {
                    'tag': related_tag,
                    'co_occurrence_count': related_tag.co_occurrence_count,
                    'relationship_strength': round(related_tag.relationship_strength, 1),
                    'total_articles': related_tag.article_count
                }
                
                relationships.append(relationship)
            
            # Cache the results
            cache.set(cache_key, relationships, self.CACHE_TIMEOUT)
            
            logger.info(f"Generated {len(relationships)} relationships for tag '{tag.name}'")
            return relationships
            
        except Exception as e:
            logger.error(f"Error calculating tag relationships for '{tag.name}': {str(e)}")
            return []
    
    def get_tag_engagement_metrics(self, tag: Tag) -> Dict:
        """
        Get detailed engagement metrics for a specific tag.
        
        Args:
            tag (Tag): The tag to analyze
            
        Returns:
            Dict: Comprehensive engagement metrics
        """
        cache_key = f'tag_engagement_{tag.id}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Get articles for this tag
            tag_articles = tag.article_set.filter(processing_status='complete')
            
            # Calculate quiz metrics
            quiz_attempts = QuizAttempt.objects.filter(article__in=tag_articles)
            
            quiz_metrics = quiz_attempts.aggregate(
                total_attempts=Count('id'),
                avg_score=Avg('score'),
                avg_wpm=Avg('wpm_used'),
                total_xp_awarded=Count('xp_awarded'),
                pass_rate=Count('id', filter=Q(score__gte=60)) * 100.0 / Count('id') if quiz_attempts.exists() else 0
            )
            
            # Calculate comment metrics
            comments = Comment.objects.filter(article__in=tag_articles)
            comment_metrics = {
                'total_comments': comments.count(),
                'unique_commenters': comments.values('user').distinct().count(),
                'avg_comments_per_article': comments.count() / tag_articles.count() if tag_articles.exists() else 0
            }
            
            # Calculate reading metrics
            reading_metrics = {
                'total_articles': tag_articles.count(),
                'wikipedia_articles': tag_articles.filter(article_type='wikipedia').count(),
                'regular_articles': tag_articles.filter(article_type='regular').count(),
                'avg_reading_level': tag_articles.aggregate(Avg('reading_level'))['reading_level__avg'] or 0,
                'total_word_count': sum(article.word_count or 0 for article in tag_articles)
            }
            
            # Calculate time-based metrics
            now = timezone.now()
            time_metrics = {
                'activity_last_7_days': quiz_attempts.filter(
                    timestamp__gte=now - timedelta(days=7)
                ).count(),
                'activity_last_30_days': quiz_attempts.filter(
                    timestamp__gte=now - timedelta(days=30)
                ).count(),
                'comments_last_7_days': comments.filter(
                    timestamp__gte=now - timedelta(days=7)
                ).count()
            }
            
            # Combine all metrics
            engagement_metrics = {
                'tag': tag,
                'quiz_metrics': quiz_metrics,
                'comment_metrics': comment_metrics,
                'reading_metrics': reading_metrics,
                'time_metrics': time_metrics,
                'engagement_score': self._calculate_engagement_score(
                    quiz_metrics, comment_metrics, time_metrics
                ),
                'last_updated': now
            }
            
            # Cache the results
            cache.set(cache_key, engagement_metrics, self.CACHE_TIMEOUT)
            
            logger.info(f"Generated engagement metrics for tag '{tag.name}'")
            return engagement_metrics
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics for '{tag.name}': {str(e)}")
            return {
                'tag': tag,
                'quiz_metrics': {},
                'comment_metrics': {},
                'reading_metrics': {},
                'time_metrics': {},
                'engagement_score': 0,
                'last_updated': timezone.now()
            }
    
    def get_system_wide_stats(self) -> Dict:
        """
        Get system-wide tag statistics.
        
        Returns:
            Dict: System-wide statistics
        """
        cache_key = 'system_wide_tag_stats'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Basic counts
            total_tags = Tag.objects.filter(is_validated=True).count()
            total_articles = Article.objects.filter(processing_status='complete').count()
            wikipedia_articles = Article.objects.filter(
                article_type='wikipedia',
                processing_status='complete'
            ).count()
            
            # Tag distribution
            tag_distribution = Tag.objects.filter(is_validated=True).aggregate(
                avg_articles_per_tag=Avg('article_count'),
                max_articles_per_tag=Max('article_count'),
                min_articles_per_tag=Min('article_count')
            )
            
            # Activity metrics
            total_quiz_attempts = QuizAttempt.objects.count()
            total_comments = Comment.objects.count()
            
            # Recent activity (last 7 days)
            cutoff_date = timezone.now() - timedelta(days=7)
            recent_activity = {
                'quiz_attempts_7d': QuizAttempt.objects.filter(
                    timestamp__gte=cutoff_date
                ).count(),
                'comments_7d': Comment.objects.filter(
                    timestamp__gte=cutoff_date
                ).count(),
                'new_tags_7d': Tag.objects.filter(
                    created_at__gte=cutoff_date,
                    is_validated=True
                ).count()
            }
            
            stats = {
                'total_tags': total_tags,
                'total_articles': total_articles,
                'wikipedia_articles': wikipedia_articles,
                'regular_articles': total_articles - wikipedia_articles,
                'tag_distribution': tag_distribution,
                'total_quiz_attempts': total_quiz_attempts,
                'total_comments': total_comments,
                'recent_activity': recent_activity,
                'last_updated': timezone.now()
            }
            
            # Cache the results
            cache.set(cache_key, stats, self.CACHE_TIMEOUT)
            
            logger.info("Generated system-wide tag statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating system-wide stats: {str(e)}")
            return {}
    
    def _calculate_popularity_score(self, article_count: int, quiz_attempts: int, 
                                  comments: int, recent_activity: int) -> float:
        """Calculate a popularity score based on various metrics."""
        # Weighted scoring system
        score = (
            article_count * 10 +           # Articles are worth 10 points each
            quiz_attempts * 2 +            # Quiz attempts are worth 2 points each
            comments * 5 +                 # Comments are worth 5 points each
            recent_activity * 15           # Recent activity is worth 15 points each
        )
        
        return round(score, 2)
    
    def _get_popularity_tier(self, popularity_score: float) -> str:
        """Determine popularity tier based on score."""
        if popularity_score >= 1000:
            return 'legendary'
        elif popularity_score >= 500:
            return 'popular'
        elif popularity_score >= 100:
            return 'trending'
        elif popularity_score >= 50:
            return 'growing'
        else:
            return 'emerging'
    
    def _calculate_engagement_rate(self, total_quiz_attempts: int, total_comments: int, article_count: int) -> float:
        """Calculate engagement rate for a tag."""
        if not article_count:
            return 0.0
        
        # Engagement rate = (quiz attempts + comments) / articles
        total_engagement = (total_quiz_attempts or 0) + (total_comments or 0)
        return round(total_engagement / article_count, 2)
    
    def _calculate_engagement_score(self, quiz_metrics: Dict, comment_metrics: Dict, 
                                  time_metrics: Dict) -> float:
        """Calculate overall engagement score."""
        score = 0
        
        # Quiz engagement
        if quiz_metrics.get('total_attempts', 0) > 0:
            score += quiz_metrics['total_attempts'] * 2
            score += (quiz_metrics.get('avg_score', 0) / 100) * 50
            score += (quiz_metrics.get('pass_rate', 0) / 100) * 30
        
        # Comment engagement
        score += comment_metrics.get('total_comments', 0) * 5
        score += comment_metrics.get('unique_commenters', 0) * 10
        
        # Recent activity bonus
        score += time_metrics.get('activity_last_7_days', 0) * 3
        score += time_metrics.get('comments_last_7_days', 0) * 8
        
        return round(score, 2)
    
    def clear_cache(self, tag_id: Optional[int] = None):
        """Clear analytics cache for a specific tag or all tags."""
        if tag_id:
            # Clear specific tag caches
            cache.delete(f'tag_engagement_{tag_id}')
            cache.delete(f'tag_relationships_{tag_id}_10')
        else:
            # Clear all tag analytics caches
            cache.delete('tag_popularity_stats_50')
            cache.delete('trending_tags_7_10')
            cache.delete('system_wide_tag_stats')
            logger.info("Cleared all tag analytics caches")


# Convenience functions for easy access
def get_popular_tags(limit: int = 10) -> List[Dict]:
    """Get popular tags with statistics."""
    analytics = TagAnalytics()
    return analytics.get_tag_popularity_stats(limit=limit)


def get_trending_tags(days: int = 7, limit: int = 10) -> List[Dict]:
    """Get trending tags."""
    analytics = TagAnalytics()
    return analytics.get_trending_tags(days=days, limit=limit)


def get_tag_relationships(tag: Tag, limit: int = 10) -> List[Dict]:
    """Get related tags for a given tag."""
    analytics = TagAnalytics()
    return analytics.get_tag_relationships(tag=tag, limit=limit)


def get_tag_analytics(tag: Tag) -> Dict:
    """Get comprehensive analytics for a tag."""
    analytics = TagAnalytics()
    return analytics.get_tag_engagement_metrics(tag)


def get_system_stats() -> Dict:
    """Get system-wide tag statistics."""
    analytics = TagAnalytics()
    return analytics.get_system_wide_stats()


def refresh_tag_cache(tag_id: Optional[int] = None):
    """Refresh analytics cache."""
    analytics = TagAnalytics()
    analytics.clear_cache(tag_id=tag_id)