from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef, Q, Max
from django.views.generic import DetailView, View, ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.core.cache import cache
from django.utils.encoding import force_str
import json
import hashlib
import re
from .models import Article, Comment, CustomUser, QuizAttempt, Tag
from .forms import ArticleURLForm, CustomUserCreationForm, UserProfileForm
from .tasks import scrape_and_save_article
from .xp_system import (
    PremiumFeatureStore, InsufficientXPError, InvalidFeatureError, 
    FeatureAlreadyOwnedError, QuizResultProcessor, SocialInteractionManager
)
from .tag_analytics import get_popular_tags, get_trending_tags, get_tag_relationships

def index(request):
    """Homepage view with article list and language filtering"""
    # Get language filter from request
    language_filter = request.GET.get('lang', 'all')
    
    # Base queryset for complete articles
    articles = Article.objects.filter(processing_status='complete')
    
    # Apply language filter
    if language_filter and language_filter != 'all':
        articles = articles.filter(language=language_filter)
    
    # Apply user's preferred language if authenticated and no explicit filter
    elif request.user.is_authenticated and language_filter == 'all':
        user_lang = getattr(request.user, 'preferred_language', None)
        if user_lang and request.GET.get('show_all') != '1':
            # Show user's preferred language by default, but allow override
            articles = articles.filter(language=user_lang)
            language_filter = user_lang
    
    # Order by timestamp and limit for homepage
    articles = articles.order_by('-timestamp')[:10]
    
    # Get popular tags (filtered by language if applicable)
    from django.db.models import Count
    popular_tags_query = Tag.objects.annotate(
        num_articles=Count('article', filter=Q(article__processing_status='complete'))
    )
    
    if language_filter and language_filter != 'all':
        popular_tags_query = popular_tags_query.filter(
            article__language=language_filter
        ).distinct()
    
    popular_tags = popular_tags_query.filter(num_articles__gt=0).order_by('-num_articles')[:8]
    
    context = {
        'articles': articles,
        'popular_tags': popular_tags,
        'current_language': language_filter,
        'show_language_selector': True,
    }
    
    return render(request, 'verifast_app/index.html', context)

class ArticleListView(ListView):
    model = Article
    template_name = 'verifast_app/article_list.html'
    context_object_name = 'articles'
    paginate_by = 15

    def get_queryset(self):
        """
        Customizes the queryset to sort articles with language filtering.
        Unread articles for the current user are shown first, sorted by newest.
        Then, read articles are shown, also sorted by newest.
        """
        queryset = Article.objects.filter(processing_status='complete')
        
        # Apply language filter
        language_filter = self.request.GET.get('lang', 'all')
        
        if language_filter and language_filter != 'all':
            queryset = queryset.filter(language=language_filter)
        elif self.request.user.is_authenticated and language_filter == 'all':
            # Apply user's preferred language if no explicit filter
            user_lang = getattr(self.request.user, 'preferred_language', None)
            if user_lang and self.request.GET.get('show_all') != '1':
                queryset = queryset.filter(language=user_lang)

        if self.request.user.is_authenticated:
            # Annotate each article with a boolean indicating if the current user
            # has a QuizAttempt for it.
            read_articles = QuizAttempt.objects.filter(
                user=self.request.user,
                article=OuterRef('pk')
            )
            queryset = queryset.annotate(
                is_read_by_user=Exists(read_articles)
            )
            # Sort by the new 'is_read_by_user' field (False comes before True),
            # and then by timestamp descending.
            return queryset.order_by('is_read_by_user', '-timestamp')
        
        # For anonymous users, just show the newest articles.
        return queryset.order_by('-timestamp')

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'verifast_app/article_detail.html'
    context_object_name = 'article'

    def calculate_word_count(self, content):
        """Calculate word count from article content."""
        if not content:
            return 0
        words = re.findall(r'\b\w+\b', content)
        return len(words)

    def calculate_reading_level(self, content):
        """Calculate reading level using simplified Flesch-Kincaid formula."""
        if not content:
            return 0.0
        
        # Count sentences (approximate by counting sentence-ending punctuation)
        sentences = re.split(r'[.!?]+', content)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Count syllables (approximate by counting vowel groups)
        words = re.findall(r'\b\w+\b', content.lower())
        word_count = len(words)
        
        if sentence_count == 0 or word_count == 0:
            return 0.0
        
        syllable_count = 0
        for word in words:
            # Simple syllable counting: count vowel groups
            vowel_groups = re.findall(r'[aeiouy]+', word)
            syllables = len(vowel_groups) if vowel_groups else 1
            syllable_count += syllables
        
        # Flesch-Kincaid Grade Level formula
        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count
        
        grade_level = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        return max(0.0, round(grade_level, 1))

    def get_related_articles(self, article):
        """Get articles with shared tags."""
        if not article.tags.exists():
            return Article.objects.none()
        
        return Article.objects.filter(
            tags__in=article.tags.all(),
            processing_status='complete'
        ).exclude(
            id=article.id
        ).distinct().select_related('user').prefetch_related('tags')[:6]

    def user_can_comment(self, user, article):
        """Check if user can comment (completed quiz with passing score)."""
        if not user.is_authenticated:
            return False
        
        return QuizAttempt.objects.filter(
            user=user,
            article=article,
            score__gte=70  # Passing score for commenting
        ).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        user = self.request.user
        
        # Calculate missing fields if needed
        fields_to_update = {}
        
        if not article.word_count:
            article.word_count = self.calculate_word_count(article.content)
            fields_to_update['word_count'] = article.word_count
        
        if not article.reading_level:
            article.reading_level = self.calculate_reading_level(article.content)
            fields_to_update['reading_level'] = article.reading_level
        
        # Save calculated fields
        if fields_to_update:
            article.save(update_fields=list(fields_to_update.keys()))
        
        # User-specific context
        if user.is_authenticated:
            context['user_wpm'] = user.current_wpm
            
            # Check quiz completion status
            passing_quiz = QuizAttempt.objects.filter(
                user=user, 
                article=article, 
                score__gte=60
            ).exists()
            context['user_has_completed_quiz'] = passing_quiz
            context['user_xp'] = user.total_xp
            context['user_can_comment'] = self.user_can_comment(user, article)

            # Add owned features for the speed reader
            owned_features = {
                'has_2word_chunking': user.has_2word_chunking,
                'has_3word_chunking': user.has_3word_chunking,
                'has_4word_chunking': user.has_4word_chunking,
                'has_5word_chunking': user.has_5word_chunking,
                'has_smart_connector_grouping': user.has_smart_connector_grouping,
                'has_smart_symbol_handling': user.has_smart_symbol_handling,
            }
            context['owned_features'] = json.dumps(owned_features)
        else:
            # For anonymous users, provide default WPM and session data
            context['user_wpm'] = self.request.session.get('current_wpm', 250)
            
            if 'total_xp' not in self.request.session:
                self.request.session['total_xp'] = 0
                self.request.session.set_expiry(60 * 24 * 60 * 60)  # 60 days in seconds
            
            session_quiz_attempts = self.request.session.get('quiz_attempts', {})
            article_key = str(article.id)
            context['user_has_completed_quiz'] = (
                article_key in session_quiz_attempts and 
                session_quiz_attempts[article_key].get('score', 0) >= 60
            )
            context['user_xp'] = self.request.session.get('total_xp', 0)
            context['user_can_comment'] = False
        
        # Article-specific context
        context['related_articles'] = self.get_related_articles(article)
        
        # Comments context
        context['comments'] = Comment.objects.filter(
            article=article,
            parent_comment__isnull=True  # Top-level comments only
        ).select_related('user').prefetch_related('replies__user').order_by('-timestamp')
        
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user

        if 'submit_quiz' in request.POST:
            score_percentage = float(request.POST.get('score_percentage', 0))
            wpm = int(request.POST.get('wpm', 0))
            quiz_time_seconds = int(request.POST.get('quiz_time_seconds', 0))
            user_answers = request.POST.get('user_answers', '[]')

            if user.is_authenticated:
                # Create the QuizAttempt object first
                quiz_attempt = QuizAttempt.objects.create(
                    user=user,
                    article=self.object,
                    score=score_percentage,
                    wpm_used=wpm,
                    quiz_time_seconds=quiz_time_seconds,
                    result={'user_answers': user_answers, 'quiz_data': self.object.quiz_data}
                )

                # Process the result using the new centralized processor
                result_data = QuizResultProcessor.process_quiz_completion(
                    quiz_attempt=quiz_attempt,
                    article=self.object,
                    user=user
                )

                # Use the rich data from the processor to show messages
                if result_data['result_type'] == 'failed':
                    messages.info(request, result_data['messages']['main_message'])
                else:
                    xp_earned = result_data['xp_breakdown']['total_xp']
                    messages.success(request, _("%(title)s You earned %(xp_earned)d XP.") % {'title': result_data['messages']['title'], 'xp_earned': xp_earned})
            else:
                # Handle anonymous users (session-based)
                # Note: The full functionality of the new XP system is not available for anonymous users,
                # but we can still provide a basic experience.
                xp_earned = int((score_percentage * 50) + (wpm * 2 * (self.object.reading_level or 1.0)))

                if 'quiz_attempts' not in request.session:
                    request.session['quiz_attempts'] = {}
                if 'total_xp' not in request.session:
                    request.session['total_xp'] = 0
                
                request.session.set_expiry(60 * 24 * 60 * 60)  # 60 days
                
                article_key = str(self.object.id)
                request.session['quiz_attempts'][article_key] = {
                    'score': score_percentage,
                    'wpm_used': wpm,
                    'xp_awarded': xp_earned,
                    'quiz_time_seconds': quiz_time_seconds,
                    'user_answers': user_answers,
                    'article_title': self.object.title
                }
                request.session['total_xp'] += xp_earned
                request.session['current_wpm'] = wpm
                request.session.modified = True
                
                if score_percentage >= 60:
                    messages.success(request, _("Quiz passed! You earned %(xp)d XP. Register to save your progress and unlock commenting!") % {'xp': xp_earned})
                else:
                    messages.info(request, _("Quiz completed with %(score).0f%%. You earned %(xp)d XP. Register to save your progress!") % {'score': score_percentage, 'xp': xp_earned})

        elif 'post_comment' in request.POST:
            if not user.is_authenticated:
                messages.error(request, _("Please register or login to post comments."))
                return redirect(self.object.get_absolute_url())

            content = request.POST.get('comment_content')
            parent_id = request.POST.get('parent_comment_id')
            parent_comment = get_object_or_404(Comment, id=parent_id) if parent_id else None

            # Check for perfect score privilege
            perfect_score_privilege = QuizAttempt.objects.filter(
                user=user, article=self.object, score__gte=100
            ).exists()

            try:
                SocialInteractionManager.post_comment(
                    user=user,
                    article=self.object,
                    content=content,
                    parent_comment=parent_comment,
                    is_perfect_score_free=perfect_score_privilege
                )
                messages.success(request, _("Your comment has been posted."))
            except InsufficientXPError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, _("An unexpected error occurred: %(error)s") % {'error': e})

        return redirect(self.object.get_absolute_url())

class UserProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'verifast_app/user_profile.html'
    context_object_name = 'user_profile'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get quiz attempts for this user
        quiz_attempts = QuizAttempt.objects.filter(user=user).order_by('-timestamp')
        context['quiz_attempts_count'] = quiz_attempts.count()
        context['recent_quiz_attempts'] = quiz_attempts[:5]  # Last 5 attempts
        
        # Calculate statistics
        if quiz_attempts.exists():
            scores = [attempt.score for attempt in quiz_attempts]
            context['average_score'] = sum(scores) / len(scores)
            context['total_xp_earned'] = sum(attempt.xp_awarded for attempt in quiz_attempts)
        else:
            context['average_score'] = 0
            context['total_xp_earned'] = 0
        
        # Add XP transaction data for transaction history component
        from .models import XPTransaction
        
        # Get base queryset for calculations
        all_transactions = XPTransaction.objects.filter(user=user).order_by('-timestamp')
        
        # Get limited transactions for display
        context['transactions'] = all_transactions[:20]
        
        # Calculate transaction summary using separate queries
        earned_transactions = all_transactions.filter(transaction_type='EARN')
        spent_transactions = all_transactions.filter(transaction_type='SPEND')
        
        context['total_earned'] = sum(t.amount for t in earned_transactions)
        context['total_spent'] = abs(sum(t.amount for t in spent_transactions))  # Make positive for display
        context['net_xp'] = context['total_earned'] - context['total_spent']
        context['has_more_transactions'] = all_transactions.count() > 20

        # Add feature store data
        context['features_by_category'] = PremiumFeatureStore.get_features_by_category(user)

        # Add UserProfileForm for feature controls
        context['form'] = UserProfileForm(instance=user)
            
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = UserProfileForm(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your feature preferences have been updated successfully!'))
            return redirect('verifast_app:user_profile')
        else:
            messages.error(request, _('There was an error updating your feature preferences.'))
            # Re-render the page with form errors
            context = self.get_context_data(object=self.object)
            context['form'] = form # Pass the form with errors back to the template
            return self.render_to_response(context)

def scrape_article_view(request):
    if request.method == 'POST':
        form = ArticleURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            
            if Article.objects.filter(url=url).exists():
                messages.warning(request, _('This article from URL %(url)s is already in our database.') % {'url': url})
                return redirect('verifast_app:article_list')

            scrape_and_save_article.delay(url)
            messages.success(request, _('Your article has been submitted and is being processed in the background!'))
            return redirect('verifast_app:article_list')
    else:
        form = ArticleURLForm()
    
    return render(request, 'verifast_app/scrape_article.html', {'form': form})

class CommentInteractView(LoginRequiredMixin, View):
    def post(self, request, comment_id):
        user = request.user
        comment = get_object_or_404(Comment, id=comment_id)
        interaction_type = request.POST.get('interaction_type')

        try:
            SocialInteractionManager.add_interaction(
                user=user,
                comment=comment,
                interaction_type=interaction_type
            )
            messages.success(request, _('Your %(interaction_type)s interaction has been recorded.') % {'interaction_type': interaction_type.lower()})
        except InsufficientXPError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, _("An unexpected error occurred: %(error)s") % {'error': e})

        return redirect(comment.article.get_absolute_url())

class UserRegistrationView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('verifast_app:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in after successful registration
        login(self.request, self.object)
        
        # Transfer session data to user account
        session_xp = self.request.session.get('total_xp', 0)
        session_wpm = self.request.session.get('current_wpm', 250)
        session_quiz_attempts = self.request.session.get('quiz_attempts', {})
        
        if session_xp > 0 or session_quiz_attempts:
            # Update user stats with session data
            self.object.total_xp += session_xp
            self.object.current_wpm = session_wpm
            self.object.save()
            
            # Transfer quiz attempts to database
            transferred_attempts = 0
            for article_id, attempt_data in session_quiz_attempts.items():
                try:
                    article = Article.objects.get(id=int(article_id))
                    QuizAttempt.objects.create(
                        user=self.object,
                        article=article,
                        score=attempt_data['score'],
                        wpm_used=attempt_data['wpm_used'],
                        xp_awarded=attempt_data['xp_awarded'],
                        quiz_time_seconds=attempt_data.get('quiz_time_seconds', 0),
                        result={'user_answers': attempt_data.get('user_answers', '[]'), 'quiz_data': article.quiz_data}
                    )
                    transferred_attempts += 1
                except (Article.DoesNotExist, ValueError, KeyError):
                    continue
            
            # Clear session data
            self.request.session.pop('total_xp', None)
            self.request.session.pop('current_wpm', None)
            self.request.session.pop('quiz_attempts', None)
            self.request.session.modified = True
            
            if transferred_attempts > 0:
                messages.success(self.request, _('Welcome to VeriFast, %(username)s! Your progress has been saved: %(xp)d XP and %(attempts)d quiz attempts transferred to your account.') % {'username': self.object.username, 'xp': session_xp, 'attempts': transferred_attempts})
            else:
                messages.success(self.request, _('Welcome to VeriFast, %(username)s! Your %(xp)d XP has been added to your account.') % {'username': self.object.username, 'xp': session_xp})
        else:
            messages.success(self.request, _('Welcome to VeriFast, %(username)s! You start with 0 XP and 250 WPM reading speed.') % {'username': self.object.username})
        
        return response

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'verifast_app/profile_edit.html'
    success_url = reverse_lazy('verifast_app:user_profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _('Your profile has been updated successfully!'))
        return super().form_valid(form)


class QuizSubmissionAPIView(LoginRequiredMixin, View):
    """
    API endpoint for submitting quiz answers, grading, and awarding XP.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

        try:
            data = json.loads(request.body)
            article_id = data.get('article_id')
            user_answers = data.get('user_answers')
            wpm_used = data.get('wpm_used')
            quiz_time_seconds = data.get('quiz_time_seconds')

            article = get_object_or_404(Article, id=article_id)

            # Grade the quiz and process completion
            quiz_attempt = QuizAttempt.objects.create(
                user=request.user,
                article=article,
                score=0, # Placeholder, will be updated by processor
                wpm_used=wpm_used,
                xp_awarded=0, # Placeholder, will be updated by processor
                quiz_time_seconds=quiz_time_seconds,
                result={'user_answers': user_answers, 'quiz_data': article.quiz_data}
            )

            result_data = QuizResultProcessor.process_quiz_completion(
                quiz_attempt=quiz_attempt,
                article=article,
                user=request.user
            )

            return JsonResponse({
                'success': True,
                'score': result_data['score'],
                'xp_earned': result_data['xp_breakdown']['total_xp'],
                'messages': result_data['messages'],
                'result_type': result_data['result_type'],
                'new_xp_balance': request.user.current_xp_points,
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Article.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Article not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class PurchaseFeatureView(LoginRequiredMixin, View):
    """
    Handle premium feature purchases via AJAX requests.
    """
    
    def post(self, request):
        try:
            # Parse JSON data from request
            data = json.loads(request.body)
            feature_key = data.get('feature_key')
            
            if not feature_key:
                return JsonResponse({
                    'success': False,
                    'error': 'Feature key is required'
                }, status=400)
            
            # Attempt to purchase the feature
            with transaction.atomic():
                feature_purchase = PremiumFeatureStore.purchase_feature(
                    user=request.user,
                    feature_key=feature_key
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully purchased {feature_purchase.feature_display_name}!',
                    'new_balance': request.user.current_xp_points,
                    'feature_name': feature_purchase.feature_display_name
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
            
        except InsufficientXPError as e:
            return JsonResponse({
                'success': False,
                'error': f'Insufficient XP: {str(e)}'
            }, status=400)
            
        except InvalidFeatureError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid feature: {str(e)}'
            }, status=400)
            
        except FeatureAlreadyOwnedError as e:
            return JsonResponse({
                'success': False,
                'error': f'Feature already owned: {str(e)}'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'An unexpected error occurred: {str(e)}'
            }, status=500)


class PremiumStoreView(LoginRequiredMixin, View):
    """
    Display the premium feature store where users can purchase premium features with XP.
    """
    
    def get(self, request):
        # Get available premium features from the store (organized by category)
        features_by_category = PremiumFeatureStore.get_features_by_category(request.user)
        
        # Flatten features for template display
        available_features = {}
        user_owned_features = []
        
        for category, features in features_by_category.items():
            for feature in features:
                feature_key = feature['key']
                available_features[feature_key] = {
                    'display_name': feature['name'],
                    'description': feature['description'],
                    'cost': feature['cost'],
                    'category': category
                }
                if feature['owned']:
                    user_owned_features.append(feature_key)
        
        context = {
            'available_features': available_features,
            'user_owned_features': user_owned_features,
            'user_xp': request.user.current_xp_points,
            'is_admin': request.user.is_superuser,
        }
        
        return render(request, 'verifast_app/premium_store.html', context)


# Tag System Views

class QuizInitView(LoginRequiredMixin, View):
    """
    HTMX endpoint to initialize quiz interface.
    """
    def get(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        
        # Check if user has completed reading (this should be tracked by reading completion)
        context = {
            'article': article,
            'quiz_data': article.quiz_data,
            'user_wpm': request.user.current_wmp if request.user.is_authenticated else 250
        }
        
        return render(request, 'verifast_app/partials/quiz_interface.html', context)


class ReadingCompleteView(LoginRequiredMixin, View):
    """
    HTMX endpoint to handle reading completion and unlock quiz.
    """
    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        
        # Mark reading as complete for this user (could store in session or user model)
        # For now, just return the unlocked quiz button
        
        context = {
            'article': article,
            'reading_completed': True
        }
        
        return render(request, 'verifast_app/partials/quiz_unlock.html', context)


def speed_reader_complete(request, article_id, article_type='regular'):
    """Handle reading completion and unlock quiz"""
    if request.user.is_authenticated:
        # The following line is a placeholder. The actual implementation will require a function to calculate XP.
        xp_awarded = 10
        request.user.total_xp += xp_awarded
        request.user.current_xp_points += xp_awarded
        request.user.save()
    
    return render(request, 'verifast_app/partials/quiz_unlock.html', {
        'article_id': article_id,
        'article_type': article_type,
        'xp_awarded': xp_awarded if request.user.is_authenticated else 0
    })

def speed_reader_init(request, article_id, article_type='regular'):
    """Initialize speed reader with preprocessed content"""
    if article_type == 'wikipedia':
        article = get_object_or_404(WikipediaArticle, id=article_id)
    else:
        article = get_object_or_404(Article, id=article_id)
    
    user = request.user if request.user.is_authenticated else None
    # The following line is a placeholder. The actual implementation will require a SpeedReaderService.
    content_data = {'word_chunks': article.content.split(), 'font_settings': {}, 'reading_settings': {}}
    
    return render(request, 'verifast_app/partials/speed_reader_active.html', {
        'word_chunks_json': json.dumps(content_data['word_chunks']),
        'font_settings': content_data['font_settings'],
        'reading_settings': content_data['reading_settings'],
        'article_id': article_id,
        'article_type': article_type,
        'total_words': len(content_data['word_chunks'])
    })

def speed_reader_complete(request, article_id, article_type='regular'):
    """Handle reading completion and unlock quiz"""
    if request.method == 'POST':
        if article_type == 'wikipedia':
            article = get_object_or_404(WikipediaArticle, id=article_id)
        else:
            article = get_object_or_404(Article, id=article_id)
        
        user = request.user
        xp_awarded = 0
        
        if user.is_authenticated:
            # Award reading XP (placeholder logic)
            xp_awarded = 25  # Base reading XP
            user.total_xp += xp_awarded
            user.current_xp_points += xp_awarded
            user.save()
        
        return render(request, 'verifast_app/partials/quiz_unlock.html', {
            'article': article,
            'xp_awarded': xp_awarded,
        })

class QuizSubmitView(View):
    def post(self, request, article_id):
        # This view is a placeholder. The actual implementation will require more logic.
        article = get_object_or_404(Article, id=article_id)
        context = {
            'article': article,
            'quiz_data': article.quiz_data,
            'user_wpm': request.user.current_wpm if request.user.is_authenticated else 250
        }
        return render(request, 'verifast_app/partials/quiz_interface.html', context)


class QuizNextQuestionView(View):
    def post(self, request, article_id):
        # This view is a placeholder. The actual implementation will require more logic.
        article = get_object_or_404(Article, id=article_id)
        context = {
            'article': article,
            'quiz_data': article.quiz_data,
            'user_wpm': request.user.current_wpm if request.user.is_authenticated else 250
        }
        return render(request, 'verifast_app/partials/quiz_interface.html', context)


class QuizStartView(View):
    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        context = {
            'article': article,
            'quiz_data': article.quiz_data,
            'user_wpm': request.user.current_wpm if request.user.is_authenticated else 250
        }
        return render(request, 'verifast_app/partials/quiz_interface.html', context)


class AddCommentView(LoginRequiredMixin, View):
    """
    HTMX endpoint to add comments with XP validation.
    """
    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Comment content is required'})
        
        # Check if user can comment (passed quiz)
        if not self.user_can_comment(request.user, article):
            return JsonResponse({'success': False, 'error': 'Complete the quiz with passing score to comment'})
        
        try:
            SocialInteractionManager.post_comment(
                user=request.user,
                article=article,
                content=content,
                parent_comment=None
            )
            
            # Return updated comments section
            comments = Comment.objects.filter(
                article=article,
                parent_comment__isnull=True
            ).select_related('user').prefetch_related('replies__user').order_by('-timestamp')
            
            context = {
                'comments': comments,
                'article': article,
                'user_can_comment': True
            }
            
            return render(request, 'verifast_app/partials/comments_list.html', context)
            
        except InsufficientXPError as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def user_can_comment(self, user, article):
        """Check if user can comment (completed quiz with passing score)."""
        if not user.is_authenticated:
            return False
        
        return QuizAttempt.objects.filter(
            user=user,
            article=article,
            score__gte=70
        ).exists()


class TagSearchView(ListView):
    """
    Tag search and discovery page with filtering and search functionality.
    """
    model = Tag
    template_name = 'verifast_app/tag_search.html'
    context_object_name = 'tags'
    paginate_by = 20
    
    def get_queryset(self):
        """Get filtered tags based on search query and filters with caching."""
        # Get search parameters
        query = self.request.GET.get('q', '').strip()
        search_type = self.request.GET.get('type', 'all')  # 'tags', 'articles', 'all'
        
        # Create cache key based on search parameters
        cache_key_data = f"tag_search_{search_type}_{query}"
        cache_key = hashlib.md5(force_str(cache_key_data).encode()).hexdigest()
        
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # If not in cache, perform the query
        queryset = Tag.objects.filter(is_validated=True).order_by('-article_count', 'name')
        
        if query:
            if search_type == 'tags':
                # Search only in tag names and descriptions
                queryset = queryset.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query)
                )
            elif search_type == 'articles':
                # Find tags that have articles matching the query
                matching_articles = Article.objects.filter(
                    Q(title__icontains=query) |
                    Q(content__icontains=query),
                    processing_status='complete'
                )
                queryset = queryset.filter(article__in=matching_articles).distinct()
            else:  # 'all'
                # Search in both tags and articles
                tag_matches = Q(name__icontains=query) | Q(description__icontains=query)
                article_matches = Q(
                    article__title__icontains=query
                ) | Q(
                    article__content__icontains=query
                )
                queryset = queryset.filter(
                    tag_matches | article_matches
                ).filter(
                    article__processing_status='complete'
                ).distinct()
        
        # Cache the result for 15 minutes
        cache.set(cache_key, queryset, 60 * 15)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get search parameters
        context['search_query'] = self.request.GET.get('q', '')
        context['search_type'] = self.request.GET.get('type', 'all')
        
        # Get popular tags using analytics service
        popular_tag_stats = get_popular_tags(limit=10)
        context['popular_tags'] = [stat['tag'] for stat in popular_tag_stats]
        
        # Get trending tags using analytics service
        trending_tag_stats = get_trending_tags(days=7, limit=10)
        context['trending_tags'] = [stat['tag'] for stat in trending_tag_stats]
        
        # Get recent tags (fallback)
        context['recent_tags'] = Tag.objects.filter(
            is_validated=True
        ).order_by('-created_at')[:10]
        
        # Get tag statistics
        context['total_tags'] = Tag.objects.filter(is_validated=True).count()
        context['total_articles'] = Article.objects.filter(processing_status='complete').count()
        
        # If searching articles, get matching articles
        if context['search_query'] and context['search_type'] in ['articles', 'all']:
            context['matching_articles'] = Article.objects.filter(
                Q(title__icontains=context['search_query']) |
                Q(content__icontains=context['search_query']),
                processing_status='complete'
            ).select_related('user').prefetch_related('tags')[:10]
        
        return context


class TagDetailView(DetailView):
    """
    Individual tag detail page showing Wikipedia article and related articles.
    """
    model = Tag
    template_name = 'verifast_app/tag_detail.html'
    context_object_name = 'tag'
    slug_field = 'name'
    slug_url_kwarg = 'tag_name'
    
    def get_object(self, queryset=None):
        """Get tag by name (case-insensitive)."""
        tag_name = self.kwargs.get('tag_name')
        return get_object_or_404(Tag, name__iexact=tag_name)
    
    def get_context_data(self, **kwargs):
        """Add related articles and tag statistics."""
        context = super().get_context_data(**kwargs)
        tag = self.object
        
        # Get all articles for this tag
        all_articles = tag.article_set.filter(
            processing_status='complete'
        ).select_related('user').order_by('-timestamp')
        
        # Separate Wikipedia articles from regular articles
        wikipedia_articles = all_articles.filter(article_type='wikipedia')
        regular_articles = all_articles.filter(article_type='regular')
        
        context['wikipedia_articles'] = wikipedia_articles
        context['regular_articles'] = regular_articles
        context['total_articles'] = all_articles.count()
        
        # Get the main Wikipedia article (first one if multiple exist)
        context['main_wikipedia_article'] = wikipedia_articles.first()
        
        # Get related tags using analytics service
        related_tag_relationships = get_tag_relationships(tag, limit=10)
        context['related_tags'] = [rel['tag'] for rel in related_tag_relationships]
        
        # Pagination for regular articles
        from django.core.paginator import Paginator
        paginator = Paginator(regular_articles, 10)
        page_number = self.request.GET.get('page')
        context['articles_page'] = paginator.get_page(page_number)
        
        # Tag statistics
        context['tag_stats'] = {
            'total_articles': all_articles.count(),
            'wikipedia_articles': wikipedia_articles.count(),
            'regular_articles': regular_articles.count(),
            'last_updated': tag.last_updated,
        }
        
        return context


class WikipediaArticleView(DetailView):
    """
    View for displaying Wikipedia articles with full VeriFast functionality.
    """
    model = Article
    template_name = 'verifast_app/wikipedia_article.html'
    context_object_name = 'article'
    
    def get_queryset(self):
        """Only allow Wikipedia articles."""
        return Article.objects.filter(
            article_type='wikipedia',
            processing_status='complete'
        )
    
    def get_context_data(self, **kwargs):
        """Add Wikipedia-specific context."""
        context = super().get_context_data(**kwargs)
        article = self.object
        
        # Check if user has taken quiz for this article
        if self.request.user.is_authenticated:
            context['user_quiz_attempts'] = QuizAttempt.objects.filter(
                user=self.request.user,
                article=article
            ).order_by('-timestamp')
            
            context['has_taken_quiz'] = context['user_quiz_attempts'].exists()
            context['best_score'] = context['user_quiz_attempts'].aggregate(
                Max('score')
            )['score__max'] if context['has_taken_quiz'] else None
        
        # Get article comments
        context['comments'] = Comment.objects.filter(
            article=article
        ).select_related('user').prefetch_related('replies').order_by('-timestamp')
        
        # Get related articles through shared tags
        shared_tags = article.tags.all()
        context['related_articles'] = Article.objects.filter(
            tags__in=shared_tags,
            processing_status='complete'
        ).exclude(id=article.id).distinct()[:5]
        
        # Wikipedia-specific context
        context['is_wikipedia'] = True
        context['wikipedia_url'] = article.url
        context['source_tag'] = article.tags.first()  # The tag this Wikipedia article represents
        
        return context


@login_required
def update_language_preference(request):
    """Update user's language preference"""
    if request.method == 'POST':
        preferred_language = request.POST.get('preferred_language')
        
        if preferred_language in ['en', 'es']:
            request.user.preferred_language = preferred_language
            request.user.save(update_fields=['preferred_language'])
            messages.success(request, _('Language preference updated successfully!'))
        else:
            messages.error(request, _('Invalid language selection.'))
    
    return redirect(request.META.get('HTTP_REFERER', 'verifast_app:index'))


def language_filter_articles(request):
    """HTMX endpoint for filtering articles by language"""
    language_filter = request.GET.get('lang', 'all')
    
    # Base queryset for complete articles
    articles = Article.objects.filter(processing_status='complete')
    
    # Apply language filter
    if language_filter and language_filter != 'all':
        articles = articles.filter(language=language_filter)
    
    # Apply user's preferred language if authenticated and no explicit filter
    elif request.user.is_authenticated and language_filter == 'all':
        user_lang = getattr(request.user, 'preferred_language', None)
        if user_lang and request.GET.get('show_all') != '1':
            articles = articles.filter(language=user_lang)
            language_filter = user_lang
    
    # Handle sorting and pagination
    if request.user.is_authenticated:
        # Annotate with read status
        read_articles = QuizAttempt.objects.filter(
            user=request.user,
            article=OuterRef('pk')
        )
        articles = articles.annotate(
            is_read_by_user=Exists(read_articles)
        ).order_by('is_read_by_user', '-timestamp')
    else:
        articles = articles.order_by('-timestamp')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_language': language_filter,
        'is_htmx': True,
    }
    
    return render(request, 'verifast_app/partials/article_list_content.html', context)