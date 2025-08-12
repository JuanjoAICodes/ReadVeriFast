from django.urls import path
from . import views
from . import views_health

app_name = 'verifast_app'  # <-- THIS LINE IS THE FIX

urlpatterns = [
    path('', views.index, name='index'),
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('scrape/', views.scrape_article_view, name='scrape_article'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/edit/', views.UserProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/save-features/', views.UserProfileView.as_view(), name='save_feature_preferences'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('articles/<int:article_id>/comments/add/', views.AddCommentView.as_view(), name='add_comment'),
    path('comments/<int:comment_id>/interact/', views.CommentInteractView.as_view(), name='comment_interact'),
    path('purchase-feature/', views.PurchaseFeatureView.as_view(), name='purchase_feature'),
    path('premium-store/', views.PremiumStoreView.as_view(), name='premium_store'),
    path('api/quiz/submit/', views.QuizSubmissionAPIView.as_view(), name='quiz_submit_api'),
    path('quiz/init/<int:article_id>/', views.QuizInitView.as_view(), name='quiz_init'),
    path('reading/complete/<int:article_id>/', views.ReadingCompleteView.as_view(), name='reading_complete'),
    path('health/', views_health.health_check, name='health_check'),
    
    # Tag System URLs
    path('tags/', views.TagSearchView.as_view(), name='tag_search'),
    path('tags/<str:tag_name>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('wikipedia/<int:pk>/', views.WikipediaArticleView.as_view(), name='wikipedia_article'),
    
    # Language System URLs
    path('language/update/', views.update_language_preference, name='update_language_preference'),
    path('articles/filter/', views.language_filter_articles, name='language_filter_articles'),

    # HTMX endpoints for Speed Reader and Quiz
    path('speed-reader/init/<int:article_id>/', views.speed_reader_init, name='speed_reader_init'),
    path('speed-reader/complete/<int:article_id>/', views.speed_reader_complete, name='speed_reader_complete'),
    path('quiz/start/<int:article_id>/', views.QuizStartView.as_view(), name='quiz_start'),
]