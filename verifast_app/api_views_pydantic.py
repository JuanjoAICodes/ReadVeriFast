"""
Pydantic-integrated API Views for VeriFast
New API endpoints that fully utilize Pydantic validation
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from .models import Article, QuizAttempt, Comment
from .pydantic_models.api import (
    ArticleSubmissionRequest, QuizSubmissionRequest, UserProfileUpdateRequest,
    CommentSubmissionRequest, XPPurchaseRequest, SearchRequest
)
from .validation.pipeline import ValidationPipeline
from .validation.exceptions import APIRequestValidationError
from .tasks import scrape_and_save_article
from .xp_system import QuizResultProcessor, SocialInteractionManager, PremiumFeatureStore

logger = logging.getLogger(__name__)
validation_pipeline = ValidationPipeline(logger_name=__name__)


def api_response(success=True, data=None, message="", error=None):
    """Standardized API response format"""
    return {
        'success': success,
        'data': data if success else None,
        'error': error if not success else None,
        'message': message,
        'timestamp': timezone.now().isoformat(),
        'version': '2.0'
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_article_v2(request):
    """Submit article URL for processing with Pydantic validation"""
    try:
        # Validate request data using Pydantic
        validated_data = validation_pipeline.validate_and_parse(
            model_class=ArticleSubmissionRequest,
            data=request.data,
            context="POST /api/v2/articles/submit/",
            raise_on_error=True
        )
        
        # Start async processing
        task = scrape_and_save_article.delay(
            str(validated_data.url), 
            request.user.id,
            title=validated_data.title,
            language=validated_data.language,
            priority=validated_data.priority or 'normal'
        )
        
        return Response(
            api_response(
                success=True,
                data={
                    'task_id': task.id,
                    'url': str(validated_data.url),
                    'title': validated_data.title,
                    'language': validated_data.language,
                    'priority': validated_data.priority,
                    'status': 'processing'
                },
                message="Article submitted for processing successfully"
            ),
            status=status.HTTP_202_ACCEPTED
        )
        
    except APIRequestValidationError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid article submission data',
                    'details': e.errors,
                    'endpoint': e.endpoint,
                    'method': e.method
                }
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        logger.error(f"Error submitting article: {str(e)}", exc_info=True)
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'PROCESSING_ERROR',
                    'message': 'Failed to submit article for processing',
                    'details': str(e)
                }
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz_v2(request, article_id):
    """Submit quiz answers with Pydantic validation"""
    try:
        # Get article
        article = get_object_or_404(Article, id=article_id, processing_status='complete')
        
        if not article.quiz_data:
            return Response(
                api_response(
                    success=False,
                    error={
                        'code': 'QUIZ_NOT_AVAILABLE',
                        'message': 'Quiz not available for this article'
                    }
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate request data using Pydantic
        validated_data = validation_pipeline.validate_and_parse(
            model_class=QuizSubmissionRequest,
            data=request.data,
            context=f"POST /api/v2/articles/{article_id}/quiz/submit/",
            raise_on_error=True
        )
        
        # Ensure article_id matches
        if validated_data.article_id != article_id:
            return Response(
                api_response(
                    success=False,
                    error={
                        'code': 'VALIDATION_ERROR',
                        'message': 'Article ID in request body does not match URL parameter'
                    }
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process quiz using the enhanced quiz processor
        result = QuizResultProcessor.process_submission(
            user=request.user,
            article=article,
            answers=validated_data.answers,
            wpm_used=validated_data.wpm or request.user.current_wpm,
            reading_time_seconds=validated_data.reading_time_seconds,
            start_time=validated_data.start_time,
            user_agent=validated_data.user_agent
        )
        
        return Response(
            api_response(
                success=True,
                data={
                    'quiz_attempt_id': result['quiz_attempt_id'],
                    'score': result['score'],
                    'xp_awarded': result['xp_awarded'],
                    'correct_count': result['correct_count'],
                    'total_questions': result['total_questions'],
                    'passed': result['passed'],
                    'performance_metrics': result.get('performance_metrics', {}),
                    'achievements': result.get('achievements', [])
                },
                message="Quiz completed successfully"
            ),
            status=status.HTTP_201_CREATED
        )
        
    except APIRequestValidationError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid quiz submission data',
                    'details': e.errors,
                    'endpoint': e.endpoint,
                    'method': e.method
                }
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        logger.error(f"Error processing quiz submission: {str(e)}", exc_info=True)
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'PROCESSING_ERROR',
                    'message': 'Failed to process quiz submission',
                    'details': str(e)
                }
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile_v2(request):
    """Update user profile with Pydantic validation"""
    try:
        # Validate request data using Pydantic
        validated_data = validation_pipeline.validate_and_parse(
            model_class=UserProfileUpdateRequest,
            data=request.data,
            context="PATCH /api/v2/profile/",
            raise_on_error=True
        )
        
        user = request.user
        updated_fields = []
        
        # Update fields that were provided
        if validated_data.current_wpm is not None:
            user.current_wpm = validated_data.current_wpm
            updated_fields.append('current_wpm')
        
        if validated_data.preferred_language is not None:
            user.preferred_language = validated_data.preferred_language
            updated_fields.append('preferred_language')
        
        if validated_data.theme is not None:
            user.theme_preference = validated_data.theme
            updated_fields.append('theme')
        
        if validated_data.email_notifications is not None:
            user.email_notifications = validated_data.email_notifications
            updated_fields.append('email_notifications')
        
        if validated_data.difficulty_preference is not None:
            user.difficulty_preference = validated_data.difficulty_preference
            updated_fields.append('difficulty_preference')
        
        user.save(update_fields=updated_fields + ['updated_at'])
        
        return Response(
            api_response(
                success=True,
                data={
                    'user_id': user.id,
                    'updated_fields': updated_fields,
                    'current_wpm': user.current_wpm,
                    'preferred_language': user.preferred_language,
                    'theme': getattr(user, 'theme_preference', 'light'),
                    'email_notifications': getattr(user, 'email_notifications', True),
                    'difficulty_preference': getattr(user, 'difficulty_preference', 'medium')
                },
                message="Profile updated successfully"
            ),
            status=status.HTTP_200_OK
        )
        
    except APIRequestValidationError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid profile update data',
                    'details': e.errors,
                    'endpoint': e.endpoint,
                    'method': e.method
                }
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}", exc_info=True)
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'UPDATE_ERROR',
                    'message': 'Failed to update user profile',
                    'details': str(e)
                }
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_comment_v2(request, article_id):
    """Post a comment with Pydantic validation"""
    try:
        # Get article
        article = get_object_or_404(Article, id=article_id)
        
        # Validate request data using Pydantic
        validated_data = validation_pipeline.validate_and_parse(
            model_class=CommentSubmissionRequest,
            data=request.data,
            context=f"POST /api/v2/articles/{article_id}/comments/",
            raise_on_error=True
        )
        
        # Ensure article_id matches
        if validated_data.article_id != article_id:
            return Response(
                api_response(
                    success=False,
                    error={
                        'code': 'VALIDATION_ERROR',
                        'message': 'Article ID in request body does not match URL parameter'
                    }
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get parent comment if specified
        parent_comment = None
        if validated_data.parent_comment_id:
            parent_comment = get_object_or_404(
                Comment, 
                id=validated_data.parent_comment_id, 
                article=article
            )
        
        # Check if user has completed quiz for this article
        has_completed_quiz = QuizAttempt.objects.filter(
            user=request.user,
            article=article,
            score__gte=60
        ).exists()
        
        if not has_completed_quiz:
            return Response(
                api_response(
                    success=False,
                    error={
                        'code': 'QUIZ_REQUIRED',
                        'message': 'You must complete the quiz with 60% or higher to comment'
                    }
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check for perfect score privilege
        perfect_score_privilege = QuizAttempt.objects.filter(
            user=request.user, 
            article=article, 
            score__gte=100
        ).exists()
        
        # Post comment using social interaction manager
        comment = SocialInteractionManager.post_comment(
            user=request.user,
            article=article,
            content=validated_data.content,
            parent_comment=parent_comment,
            is_perfect_score_free=perfect_score_privilege
        )
        
        return Response(
            api_response(
                success=True,
                data={
                    'comment_id': comment.id,
                    'content': comment.content,
                    'article_id': article.id,
                    'parent_comment_id': parent_comment.id if parent_comment else None,
                    'xp_cost': 0 if perfect_score_privilege else (5 if parent_comment else 10),
                    'timestamp': comment.timestamp.isoformat(),
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username
                    }
                },
                message="Comment posted successfully"
            ),
            status=status.HTTP_201_CREATED
        )
        
    except APIRequestValidationError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid comment data',
                    'details': e.errors,
                    'endpoint': e.endpoint,
                    'method': e.method
                }
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        logger.error(f"Error posting comment: {str(e)}", exc_info=True)
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'COMMENT_ERROR',
                    'message': 'Failed to post comment',
                    'details': str(e)
                }
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_feature_v2(request):
    """Purchase premium feature with Pydantic validation"""
    try:
        # Validate request data using Pydantic
        validated_data = validation_pipeline.validate_and_parse(
            model_class=XPPurchaseRequest,
            data=request.data,
            context="POST /api/v2/features/purchase/",
            raise_on_error=True
        )
        
        # Verify expected cost matches actual cost
        feature = PremiumFeatureStore.FEATURES.get(validated_data.feature_id)
        if not feature:
            return Response(
                api_response(
                    success=False,
                    error={
                        'code': 'INVALID_FEATURE',
                        'message': f'Feature "{validated_data.feature_id}" does not exist'
                    }
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        if feature['cost'] != validated_data.expected_cost:
            return Response(
                api_response(
                    success=False,
                    error={
                        'code': 'PRICE_MISMATCH',
                        'message': f'Expected cost {validated_data.expected_cost} does not match actual cost {feature["cost"]}',
                        'actual_cost': feature['cost']
                    }
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Attempt to purchase the feature
        PremiumFeatureStore.purchase_feature(request.user, validated_data.feature_id)
        
        return Response(
            api_response(
                success=True,
                data={
                    'feature_id': validated_data.feature_id,
                    'feature_name': feature['name'],
                    'cost': feature['cost'],
                    'remaining_balance': request.user.current_xp_points,
                    'purchase_timestamp': timezone.now().isoformat()
                },
                message=f"Successfully purchased {feature['name']}"
            ),
            status=status.HTTP_201_CREATED
        )
        
    except APIRequestValidationError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid purchase request data',
                    'details': e.errors,
                    'endpoint': e.endpoint,
                    'method': e.method
                }
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        logger.error(f"Error purchasing feature: {str(e)}", exc_info=True)
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'PURCHASE_ERROR',
                    'message': 'Failed to purchase feature',
                    'details': str(e)
                }
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_articles_v2(request):
    """Search articles with Pydantic validation"""
    try:
        # Validate query parameters using Pydantic
        query_params = dict(request.query_params)
        
        # Convert single-item lists to strings for Pydantic
        for key, value in query_params.items():
            if isinstance(value, list) and len(value) == 1:
                query_params[key] = value[0]
        
        validated_data = validation_pipeline.validate_and_parse(
            model_class=SearchRequest,
            data=query_params,
            context="GET /api/v2/articles/search/",
            raise_on_error=True
        )
        
        # Build queryset based on validated parameters
        queryset = Article.objects.filter(processing_status='complete')
        
        # Apply search query
        if validated_data.query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=validated_data.query) |
                Q(content__icontains=validated_data.query) |
                Q(tags__name__icontains=validated_data.query)
            ).distinct()
        
        # Apply filters
        if validated_data.filters:
            filters = validated_data.filters
            
            if 'language' in filters:
                queryset = queryset.filter(language=filters['language'])
            
            if 'tags' in filters:
                tag_names = filters['tags']
                if isinstance(tag_names, list):
                    queryset = queryset.filter(tags__name__in=tag_names)
                else:
                    queryset = queryset.filter(tags__name=tag_names)
            
            if 'difficulty' in filters:
                # Map difficulty to reading level ranges
                difficulty_ranges = {
                    'easy': (0, 40),
                    'medium': (40, 70),
                    'hard': (70, 100)
                }
                if filters['difficulty'] in difficulty_ranges:
                    min_level, max_level = difficulty_ranges[filters['difficulty']]
                    queryset = queryset.filter(
                        reading_level__gte=min_level,
                        reading_level__lte=max_level
                    )
        
        # Apply sorting
        if validated_data.sort_by == 'date':
            queryset = queryset.order_by('-publication_date', '-timestamp')
        elif validated_data.sort_by == 'popularity':
            from django.db import models as django_models
            queryset = queryset.annotate(
                quiz_count=django_models.Count('quizattempt')
            ).order_by('-quiz_count', '-timestamp')
        else:  # relevance (default)
            queryset = queryset.order_by('-timestamp')
        
        # Apply pagination
        total_count = queryset.count()
        start_index = (validated_data.page - 1) * validated_data.per_page
        end_index = start_index + validated_data.per_page
        articles = queryset[start_index:end_index]
        
        # Serialize results
        results = []
        for article in articles:
            results.append({
                'id': article.id,
                'title': article.title,
                'url': article.url,
                'language': article.language,
                'reading_level': article.reading_level,
                'word_count': article.word_count,
                'publication_date': article.publication_date.isoformat() if article.publication_date else None,
                'timestamp': article.timestamp.isoformat(),
                'tags': [tag.name for tag in article.tags.all()],
                'has_quiz': bool(article.quiz_data)
            })
        
        return Response(
            api_response(
                success=True,
                data={
                    'results': results,
                    'pagination': {
                        'total_count': total_count,
                        'page': validated_data.page,
                        'per_page': validated_data.per_page,
                        'total_pages': (total_count + validated_data.per_page - 1) // validated_data.per_page,
                        'has_next': end_index < total_count,
                        'has_previous': validated_data.page > 1
                    },
                    'search_params': {
                        'query': validated_data.query,
                        'filters': validated_data.filters,
                        'sort_by': validated_data.sort_by
                    }
                },
                message=f"Found {total_count} articles matching search criteria"
            ),
            status=status.HTTP_200_OK
        )
        
    except APIRequestValidationError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid search parameters',
                    'details': e.errors,
                    'endpoint': e.endpoint,
                    'method': e.method
                }
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        logger.error(f"Error searching articles: {str(e)}", exc_info=True)
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'SEARCH_ERROR',
                    'message': 'Failed to search articles',
                    'details': str(e)
                }
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )