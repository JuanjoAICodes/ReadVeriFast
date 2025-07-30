"""
API Views for VeriFast
REST API endpoints with Pydantic validation integration
"""

from rest_framework import generics, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

from .models import CustomUser, Article, QuizAttempt, Comment, CommentInteraction
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, ArticleListSerializer,
    ArticleDetailSerializer, ArticleSubmissionSerializer, QuizSubmissionSerializer, CommentSerializer,
    CommentInteractionSerializer
)
from .tasks import scrape_and_save_article
from .xp_system import (
    SocialInteractionManager, InsufficientXPError,
    XPTransactionManager, PremiumFeatureStore, InvalidFeatureError, FeatureAlreadyOwnedError
)

# Import Pydantic models
from .validation.pipeline import ValidationPipeline
from .validation.exceptions import ValidationException, APIRequestValidationError

logger = logging.getLogger(__name__)

# Initialize validation pipeline
validation_pipeline = ValidationPipeline(logger_name=__name__)


def api_response(success=True, data=None, message="", error=None):
    """Standardized API response format"""
    response_data = {
        'success': success,
        'meta': {
            'timestamp': timezone.now().isoformat(),
            'version': '1.0'
        }
    }
    
    if success:
        response_data['data'] = data
        if message:
            response_data['message'] = message
    else:
        response_data['error'] = error or {}
        
    return response_data


def validate_request_data(pydantic_model, request_data, endpoint=None, method=None):
    """
    Validate request data using Pydantic model.
    
    Args:
        pydantic_model: Pydantic model class for validation
        request_data: Request data to validate
        endpoint: API endpoint name for error context
        method: HTTP method for error context
        
    Returns:
        Validated model instance or raises APIRequestValidationError
    """
    try:
        return validation_pipeline.validate_and_parse(
            model_class=pydantic_model,
            data=request_data,
            context=f"{method} {endpoint}" if endpoint and method else "",
            raise_on_error=True
        )
    except ValidationException as e:
        raise APIRequestValidationError(
            errors=e.errors,
            endpoint=endpoint,
            method=method
        )


def handle_validation_error(error, default_message="Validation failed"):
    """
    Handle validation errors and return standardized API response.
    
    Args:
        error: ValidationException or APIRequestValidationError
        default_message: Default error message
        
    Returns:
        Response object with validation error details
    """
    if isinstance(error, APIRequestValidationError):
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid request data',
                    'details': error.errors,
                    'endpoint': error.endpoint,
                    'method': error.method
                }
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    elif isinstance(error, ValidationException):
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': default_message,
                    'details': error.errors,
                    'context': error.context
                }
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    else:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': str(error)
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view with user profile data"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Add user profile data to successful login
            username = request.data.get('username')
            user = CustomUser.objects.get(username=username)
            profile_data = UserProfileSerializer(user).data
            
            response.data = api_response(
                success=True,
                data={
                    'tokens': response.data,
                    'user': profile_data
                },
                message=_("Login successful")
            )
        else:
            response.data = api_response(
                success=False,
                error={
                    'code': 'AUTHENTICATION_FAILED',
                    'message': 'Invalid credentials',
                    'details': response.data
                }
            )
        
        return response


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            profile_data = UserProfileSerializer(user).data
            
            return Response(
                api_response(
                    success=True,
                    data={'user': profile_data},
                    message="Registration successful"
                ),
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                api_response(
                    success=False,
                    error={
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid registration data',
                        'details': serializer.errors
                    }
                ),
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile management endpoint"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response(
            api_response(
                success=True,
                data=serializer.data,
                message="Profile retrieved successfully"
            )
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                api_response(
                    success=True,
                    data=serializer.data,
                    message="Profile updated successfully"
                )
            )
        else:
            return Response(
                api_response(
                    success=False,
                    error={
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid profile data',
                        'details': serializer.errors
                    }
                ),
                status=status.HTTP_400_BAD_REQUEST
            )


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Article management endpoints"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Article.objects.filter(processing_status='complete')
        
        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        # Filter by reading level
        min_level = self.request.query_params.get('min_reading_level')
        max_level = self.request.query_params.get('max_reading_level')
        if min_level:
            queryset = queryset.filter(reading_level__gte=float(min_level))
        if max_level:
            queryset = queryset.filter(reading_level__lte=float(max_level))
        
        # Search in title and content
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        
        return queryset.order_by('-publication_date', '-timestamp')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleDetailSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            
            return Response(
                api_response(
                    success=True,
                    data={
                        'results': serializer.data,
                        'pagination': {
                            'count': paginated_response.data['count'],
                            'next': paginated_response.data['next'],
                            'previous': paginated_response.data['previous'],
                            'page_size': self.paginator.page_size,
                        }
                    },
                    message="Articles retrieved successfully"
                )
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            api_response(
                success=True,
                data=serializer.data,
                message="Articles retrieved successfully"
            )
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        
        return Response(
            api_response(
                success=True,
                data=serializer.data,
                message="Article retrieved successfully"
            )
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_article(request):
    """Submit article URL for processing"""
    serializer = ArticleSubmissionSerializer(data=request.data)
    
    if serializer.is_valid():
        url = serializer.validated_data['url']
        
        try:
            # Start async processing
            task = scrape_and_save_article.delay(url, request.user.id)
            
            return Response(
                api_response(
                    success=True,
                    data={
                        'task_id': task.id,
                        'url': url,
                        'status': 'processing'
                    },
                    message="Article submitted for processing"
                ),
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            logger.error(f"Error submitting article: {str(e)}")
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
    else:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid article submission data',
                    'details': serializer.errors
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_questions(request, article_id):
    """Get quiz questions for an article"""
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
    
    # Return questions without correct answers
    questions = []
    quiz_questions = article.quiz_data.get('questions', []) if isinstance(article.quiz_data, dict) else article.quiz_data
    
    for q in quiz_questions:
        if isinstance(q, dict):
            questions.append({
                'question': q.get('question', ''),
                'options': q.get('options', [])
            })
    
    return Response(
        api_response(
            success=True,
            data={
                'article_id': article.id,
                'article_title': article.title,
                'questions': questions
            },
            message="Quiz questions retrieved successfully"
        )
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request, article_id):
    """Submit quiz answers and get results"""
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
    
    serializer = QuizSubmissionSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        user = request.user

        # Calculate score before creating the attempt
        # Handle both list and dict formats for quiz_data
        if isinstance(article.quiz_data, list):
            correct_answers = [q.get('correct_answer', 0) for q in article.quiz_data]
        else:
            correct_answers = [q.get('correct_answer', 0) for q in article.quiz_data.get('questions', [])]
        correct_count = sum(1 for i, answer in enumerate(data['answers']) if i < len(correct_answers) and answer == correct_answers[i])
        score_percentage = (correct_count / len(correct_answers)) * 100 if correct_answers else 0

        # Calculate XP award
        base_xp = 50  # Base XP for attempting quiz
        score_bonus = int(score_percentage * 2)  # 2 XP per percentage point
        speed_bonus = max(0, (data['wmp_used'] - 200) // 50 * 10)  # Bonus for higher WPM
        total_xp = base_xp + score_bonus + speed_bonus
        
        # Create QuizAttempt object
        QuizAttempt.objects.create(
            user=user,
            article=article,
            score=score_percentage,
            wpm_used=data['wmp_used'],
            reading_time_seconds=data.get('reading_time_seconds'),
            quiz_time_seconds=data.get('quiz_time_seconds'),
            xp_awarded=total_xp,
            result={'answers': data['answers'], 'correct_answers': correct_answers}
        )

        # Update user XP
        user.total_xp += total_xp
        user.current_xp_points += total_xp
        user.save()

        # Simple response to avoid serialization issues
        response_data = {
            'score': score_percentage,
            'xp_awarded': total_xp,
            'correct_count': correct_count,
            'total_questions': len(correct_answers),
            'passed': score_percentage >= 60
        }

        return Response(api_response(success=True, data=response_data, message="Quiz completed successfully."), status=status.HTTP_201_CREATED)
    else:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid quiz submission data',
                    'details': serializer.errors
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_article_comments(request, article_id):
    """Get comments for an article"""
    article = get_object_or_404(Article, id=article_id)
    
    # Get top-level comments (no parent)
    comments = Comment.objects.filter(
        article=article, 
        parent_comment=None
    ).order_by('-timestamp')
    
    serializer = CommentSerializer(
        comments, 
        many=True, 
        context={'request': request}
    )
    
    return Response(
        api_response(
            success=True,
            data=serializer.data,
            message="Comments retrieved successfully"
        )
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_article_comment(request, article_id):
    """Post a comment on an article"""
    article = get_object_or_404(Article, id=article_id)
    
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
    
    content = request.data.get('content', '').strip()
    parent_comment_id = request.data.get('parent_comment')
    
    if not content:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Comment content is required'
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    parent_comment = None
    if parent_comment_id:
        parent_comment = get_object_or_404(Comment, id=parent_comment_id, article=article)

    # Check for perfect score privilege
    perfect_score_privilege = QuizAttempt.objects.filter(
        user=request.user, article=article, score__gte=100
    ).exists()

    try:
        comment = SocialInteractionManager.post_comment(
            user=request.user,
            article=article,
            content=content,
            parent_comment=parent_comment,
            is_perfect_score_free=perfect_score_privilege
        )
        serializer = CommentSerializer(comment, context={'request': request})
        return Response(api_response(success=True, data=serializer.data, message="Comment posted successfully"), status=status.HTTP_201_CREATED)
    except InsufficientXPError as e:
        return Response(api_response(success=False, error={'code': 'INSUFFICIENT_XP', 'message': str(e)}), status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error posting comment: {e}", exc_info=True)
        return Response(api_response(success=False, error={'code': 'SERVER_ERROR', 'message': 'An unexpected error occurred.'}), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def interact_with_comment_view(request, comment_id):
    """Interact with a comment using the new XP system."""
    comment = get_object_or_404(Comment, id=comment_id)
    
    serializer = CommentInteractionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(api_response(success=False, error={'code': 'VALIDATION_ERROR', 'message': 'Invalid interaction data', 'details': serializer.errors}), status=status.HTTP_400_BAD_REQUEST)

    interaction_type = serializer.validated_data['interaction_type']

    try:
        SocialInteractionManager.add_interaction(
            user=request.user,
            comment=comment,
            interaction_type=interaction_type
        )
        return Response(api_response(success=True, data={'interaction_type': interaction_type, 'comment_id': comment.id}, message=f"{interaction_type.title()} interaction recorded"))
    except InsufficientXPError as e:
        return Response(api_response(success=False, error={'code': 'INSUFFICIENT_XP', 'message': str(e)}), status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error interacting with comment: {e}", exc_info=True)
        return Response(api_response(success=False, error={'code': 'SERVER_ERROR', 'message': 'An unexpected error occurred.'}), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """Get detailed user statistics"""
    user = request.user
    
    # Calculate various statistics
    quiz_attempts = QuizAttempt.objects.filter(user=user)
    successful_attempts = quiz_attempts.filter(score__gte=60)
    comments = Comment.objects.filter(user=user)
    interactions_given = CommentInteraction.objects.filter(user=user)
    interactions_received = CommentInteraction.objects.filter(comment__user=user)
    
    stats = {
        'total_xp': user.total_xp,
        'current_xp_points': user.current_xp_points,
        'current_wpm': user.current_wpm,
        'max_wpm': user.max_wpm,
        'articles_read': successful_attempts.count(),
        'total_quiz_attempts': quiz_attempts.count(),
        'average_score': quiz_attempts.aggregate(avg=Avg('score'))['avg'] or 0,
        'reading_streak': 0,  # Simplified for now
        'comments_posted': comments.count(),
        'interactions_given': interactions_given.count(),
        'interactions_received': interactions_received.count(),
    }
    
    return Response(
        api_response(
            success=True,
            data=stats,
            message="User statistics retrieved successfully"
        )
    )


# XP Management API Endpoints

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_xp_balance(request):
    """Get user's XP balance and recent transactions"""
    user = request.user
    
    # Get XP balance summary
    balance_summary = XPTransactionManager.get_xp_balance_summary(user)
    
    return Response(
        api_response(
            success=True,
            data=balance_summary,
            message="XP balance retrieved successfully"
        )
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_xp_transaction_history(request):
    """Get user's XP transaction history with pagination and filtering"""
    user = request.user
    
    # Get query parameters
    transaction_type = request.query_params.get('type')  # 'EARN' or 'SPEND'
    limit = request.query_params.get('limit', 20)
    offset = request.query_params.get('offset', 0)
    
    try:
        limit = int(limit)
        offset = int(offset)
    except ValueError:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid limit or offset parameters'
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get transactions with filtering
    transactions = XPTransactionManager.get_user_transaction_history(
        user=user,
        transaction_type=transaction_type
    )
    
    # Apply pagination
    total_count = transactions.count()
    transactions = transactions[offset:offset + limit]
    
    # Serialize transaction data
    transaction_data = []
    for transaction in transactions:
        transaction_data.append({
            'id': transaction.id,
            'transaction_type': transaction.transaction_type,
            'amount': transaction.amount,
            'source': transaction.get_source_display(),
            'description': transaction.description,
            'balance_after': transaction.balance_after,
            'timestamp': transaction.timestamp.isoformat(),
            'quiz_attempt_id': transaction.quiz_attempt.id if transaction.quiz_attempt else None,
            'comment_id': transaction.comment.id if transaction.comment else None,
            'feature_purchased': transaction.feature_purchased
        })
    
    return Response(
        api_response(
            success=True,
            data={
                'transactions': transaction_data,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_next': offset + limit < total_count,
                    'has_previous': offset > 0
                }
            },
            message="Transaction history retrieved successfully"
        )
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feature_store(request):
    """Get available premium features and user's ownership status"""
    user = request.user
    
    features = []
    for key, feature in PremiumFeatureStore.FEATURES.items():
        features.append({
            'key': key,
            'name': feature['name'],
            'description': feature['description'],
            'cost': feature['cost'],
            'category': feature['category'],
            'subcategory': feature.get('subcategory', ''),
            'benefits': feature.get('benefits', []),
            'difficulty_level': feature.get('difficulty_level', 'beginner'),
            'preview_text': feature.get('preview_text', ''),
            'owned': PremiumFeatureStore.user_owns_feature(user, key),
            'can_afford': user.current_xp_points >= feature['cost']
        })
    
    # Group features by category
    categorized_features = {}
    for feature in features:
        category = feature['category']
        if category not in categorized_features:
            categorized_features[category] = []
        categorized_features[category].append(feature)
    
    return Response(
        api_response(
            success=True,
            data={
                'features': features,
                'categorized_features': categorized_features,
                'user_balance': user.current_xp_points,
                'pricing_tiers': PremiumFeatureStore.PRICING_TIERS
            },
            message="Feature store retrieved successfully"
        )
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_feature(request):
    """Purchase a premium feature with XP"""
    user = request.user
    feature_key = request.data.get('feature_key')
    
    if not feature_key:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'VALIDATION_ERROR',
                    'message': 'feature_key is required'
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Attempt to purchase the feature
        PremiumFeatureStore.purchase_feature(user, feature_key)
        
        # Get updated feature info
        feature = PremiumFeatureStore.FEATURES.get(feature_key, {})
        
        return Response(
            api_response(
                success=True,
                data={
                    'feature_key': feature_key,
                    'feature_name': feature.get('name', ''),
                    'cost': feature.get('cost', 0),
                    'remaining_balance': user.current_xp_points
                },
                message=_("Successfully purchased %(feature_name)s") % {'feature_name': feature.get('name', feature_key)}
            ),
            status=status.HTTP_201_CREATED
        )
        
    except InsufficientXPError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'INSUFFICIENT_XP',
                    'message': str(e),
                    'required_xp': PremiumFeatureStore.FEATURES.get(feature_key, {}).get('cost', 0),
                    'current_balance': user.current_xp_points
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except InvalidFeatureError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'INVALID_FEATURE',
                    'message': str(e)
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except FeatureAlreadyOwnedError as e:
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'FEATURE_ALREADY_OWNED',
                    'message': str(e)
                }
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except Exception as e:
        logger.error(f"Error purchasing feature: {e}", exc_info=True)
        return Response(
            api_response(
                success=False,
                error={
                    'code': 'SERVER_ERROR',
                    'message': _('An unexpected error occurred during purchase')
                }
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )