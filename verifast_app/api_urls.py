"""
API URL Configuration for VeriFast
Defines all REST API endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import (
    CustomTokenObtainPairView, UserRegistrationView, UserProfileView,
    ArticleViewSet, submit_article, get_quiz_questions, submit_quiz,
    get_article_comments, post_article_comment, interact_with_comment_view,
    get_user_stats, get_xp_balance, get_xp_transaction_history, 
    get_feature_store, purchase_feature
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')

app_name = 'api'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    
    # Article endpoints
    path('', include(router.urls)),
    path('articles/submit/', submit_article, name='submit_article'),
    path('articles/<int:article_id>/quiz/', get_quiz_questions, name='get_quiz_questions'),
    path('articles/<int:article_id>/quiz/submit/', submit_quiz, name='submit_quiz'),
    
    # Comment endpoints
    path('articles/<int:article_id>/comments/', get_article_comments, name='get_article_comments'),
    path('articles/<int:article_id>/comments/post/', post_article_comment, name='post_article_comment'),
    path('comments/<int:comment_id>/interact/', interact_with_comment_view, name='interact_with_comment'),
    
    # User statistics
    path('users/me/stats/', get_user_stats, name='get_user_stats'),
    
    # XP Management endpoints
    path('xp/balance/', get_xp_balance, name='get_xp_balance'),
    path('xp/transactions/', get_xp_transaction_history, name='get_xp_transaction_history'),
    path('xp/features/', get_feature_store, name='get_feature_store'),
    path('xp/features/purchase/', purchase_feature, name='purchase_feature'),
]