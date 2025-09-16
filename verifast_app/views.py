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
from django.utils import timezone
from .models import Article, Comment, CustomUser, QuizAttempt, Tag
from .forms import ArticleURLForm, CustomUserCreationForm, UserProfileForm, FeatureControlForm
from .tasks import scrape_and_save_article
from .xp_system import (
    PremiumFeatureStore,
    InsufficientXPError,
    InvalidFeatureError,
    FeatureAlreadyOwnedError,
    QuizResultProcessor,
    SocialInteractionManager,
)
from .tag_analytics import get_popular_tags, get_trending_tags, get_tag_relationships


def index(request):
    """Homepage view with article list and language filtering"""
    # Get language filter from request
    language_filter = request.GET.get("lang", "all")

    # Base queryset for complete articles
    articles = Article.objects.filter(processing_status="complete")

    # Apply language filter
    if language_filter and language_filter != "all":
        articles = articles.filter(language=language_filter)

    # Order by timestamp and limit for homepage
    articles = articles.order_by("-timestamp")[:10]

    # Get popular tags (filtered by language if applicable)
    from django.db.models import Count

    popular_tags_query = Tag.objects.annotate(
        num_articles=Count("article", filter=Q(article__processing_status="complete"))
    )

    if language_filter and language_filter != "all":
        popular_tags_query = popular_tags_query.filter(
            article__language=language_filter
        ).distinct()

    popular_tags = popular_tags_query.filter(num_articles__gt=0).order_by(
        "-num_articles"
    )[:8]

    context = {
        "articles": articles,
        "popular_tags": popular_tags,
        "current_language": language_filter,
        "show_language_selector": True,
    }

    return render(request, "verifast_app/index.html", context)


class ArticleListView(ListView):
    model = Article
    template_name = "verifast_app/article_list.html"
    context_object_name = "articles"
    paginate_by = 15

    def get_queryset(self):
        """
        Customizes the queryset to sort articles with language filtering.
        Unread articles for the current user are shown first, sorted by newest.
        Then, read articles are shown, also sorted by newest.
        """
        queryset = Article.objects.filter(processing_status="complete")

        # Apply language filter
        language_filter = self.request.GET.get("lang", "all")

        if language_filter and language_filter != "all":
            queryset = queryset.filter(language=language_filter)
        if self.request.user.is_authenticated:
            # Annotate each article with a boolean indicating if the current user
            # has a QuizAttempt for it.
            read_articles = QuizAttempt.objects.filter(
                user=self.request.user, article=OuterRef("pk")
            )
            queryset = queryset.annotate(is_read_by_user=Exists(read_articles))
            # Sort by the new 'is_read_by_user' field (False comes before True),
            # and then by timestamp descending.
            return queryset.order_by("is_read_by_user", "-timestamp")

        # For anonymous users, just show the newest articles.
        return queryset.order_by("-timestamp")


class ArticleDetailView(DetailView):
    model = Article
    template_name = "verifast_app/article_detail.html"
    context_object_name = "article"

    def calculate_word_count(self, content):
        """Calculate word count from article content."""
        if not content:
            return 0
        words = re.findall(r"\b\w+\b", content)
        return len(words)

    def calculate_reading_level(self, content):
        """Calculate reading level using simplified Flesch-Kincaid formula."""
        if not content:
            return 0.0

        # Count sentences (approximate by counting sentence-ending punctuation)
        sentences = re.split(r"[.!?]+", content)
        sentence_count = len([s for s in sentences if s.strip()])

        # Count syllables (approximate by counting vowel groups)
        words = re.findall(r"\b\w+\b", content.lower())
        word_count = len(words)

        if sentence_count == 0 or word_count == 0:
            return 0.0

        syllable_count = 0
        for word in words:
            # Simple syllable counting: count vowel groups
            vowel_groups = re.findall(r"[aeiouy]+", word)
            syllables = len(vowel_groups) if vowel_groups else 1
            syllable_count += syllables

        # Flesch-Kincaid Grade Level formula
        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count

        grade_level = (
            (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        )
        return max(0.0, round(grade_level, 1))

    def get_related_articles(self, article):
        """Get articles with shared tags."""
        if not article.tags.exists():
            return Article.objects.none()

        return (
            Article.objects.filter(
                tags__in=article.tags.all(), processing_status="complete"
            )
            .exclude(id=article.id)
            .distinct()
            .select_related("user")
            .prefetch_related("tags")[:6]
        )

    def user_can_comment(self, user, article):
        """Check if user can comment (completed quiz with passing score)."""
        if not user.is_authenticated:
            return False

        return QuizAttempt.objects.filter(
            user=user,
            article=article,
            score__gte=60,  # Passing score for commenting (aligned to 60%)
        ).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        user = self.request.user

        # Calculate missing fields if needed
        fields_to_update = {}

        if not article.word_count:
            article.word_count = self.calculate_word_count(article.content)
            fields_to_update["word_count"] = article.word_count

        if not article.reading_level:
            article.reading_level = self.calculate_reading_level(article.content)
            fields_to_update["reading_level"] = article.reading_level

        # Save calculated fields
        if fields_to_update:
            article.save(update_fields=list(fields_to_update.keys()))

        # User-specific context
        if user.is_authenticated:
            context["user_wpm"] = user.current_wpm

            # Calculate estimated reading time based on user's WPM
            context["estimated_reading_time"] = article.get_reading_time_estimate(
                user.current_wpm
            )

            # Check quiz completion status
            passing_quiz = QuizAttempt.objects.filter(
                user=user, article=article, score__gte=60
            ).exists()
            context["user_has_completed_quiz"] = passing_quiz
            context["user_xp"] = user.total_xp
            context["user_can_comment"] = self.user_can_comment(user, article)

            # Add owned features for the speed reader
            owned_features = {
                "has_2word_chunking": user.has_2word_chunking,
                "has_3word_chunking": user.has_3word_chunking,
                "has_4word_chunking": user.has_4word_chunking,
                "has_5word_chunking": user.has_5word_chunking,
                "has_smart_connector_grouping": user.has_smart_connector_grouping,
                "has_smart_symbol_handling": user.has_smart_symbol_handling,
            }
            context["owned_features"] = json.dumps(owned_features)
        else:
            # For anonymous users, provide default WPM and session data
            user_wpm = self.request.session.get("current_wpm", 250)
            context["user_wpm"] = user_wpm

            # Calculate estimated reading time based on session WPM or default
            context["estimated_reading_time"] = article.get_reading_time_estimate(
                user_wpm
            )

            if "total_xp" not in self.request.session:
                self.request.session["total_xp"] = 0
                self.request.session.set_expiry(60 * 24 * 60 * 60)  # 60 days in seconds

            session_quiz_attempts = self.request.session.get("quiz_attempts", {})
            article_key = str(article.id)
            user_has_completed_quiz = (
                article_key in session_quiz_attempts
                and session_quiz_attempts[article_key].get("score", 0) >= 60
            )
            context["user_has_completed_quiz"] = user_has_completed_quiz
            context["user_xp"] = self.request.session.get("total_xp", 0)
            context["user_can_comment"] = user_has_completed_quiz

        # Article-specific context
        context["related_articles"] = self.get_related_articles(article)

        # Comments context - Optimized to prevent N+1 queries
        from django.db.models import Count, Q

        context["comments"] = (
            Comment.objects.filter(
                article=article,
                parent_comment__isnull=True,  # Top-level comments only
            )
            .select_related("user")
            .prefetch_related("replies__user")
            .annotate(
                bronze_count=Count(
                    "commentinteraction",
                    filter=Q(commentinteraction__interaction_type="BRONZE"),
                ),
                silver_count=Count(
                    "commentinteraction",
                    filter=Q(commentinteraction__interaction_type="SILVER"),
                ),
                gold_count=Count(
                    "commentinteraction",
                    filter=Q(commentinteraction__interaction_type="GOLD"),
                ),
            )
            .order_by("-timestamp")
        )

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user

        if "submit_quiz" in request.POST:
            score_percentage = float(request.POST.get("score_percentage", 0))
            wpm = int(request.POST.get("wpm", 0))
            quiz_time_seconds = int(request.POST.get("quiz_time_seconds", 0))
            user_answers = request.POST.get("user_answers", "[]")

            if user.is_authenticated:
                # Create the QuizAttempt object first
                quiz_attempt = QuizAttempt.objects.create(
                    user=user,
                    article=self.object,
                    score=score_percentage,
                    wpm_used=wpm,
                    quiz_time_seconds=quiz_time_seconds,
                    result={
                        "user_answers": user_answers,
                        "quiz_data": self.object.quiz_data,
                    },
                )

                # Process the result using the new centralized processor
                result_data = QuizResultProcessor.process_quiz_completion(
                    quiz_attempt=quiz_attempt, article=self.object, user=user
                )

                # Use the rich data from the processor to show messages
                if result_data["result_type"] == "failed":
                    messages.info(request, result_data["messages"]["main_message"])
                else:
                    xp_earned = result_data["xp_breakdown"]["total_xp"]
                    messages.success(
                        request,
                        _("%(title)s You earned %(xp_earned)d XP.")
                        % {
                            "title": result_data["messages"]["title"],
                            "xp_earned": xp_earned,
                        },
                    )
            else:
                # Handle anonymous users (session-based)
                # Note: The full functionality of the new XP system is not available for anonymous users,
                # but we can still provide a basic experience.
                xp_earned = int(
                    (score_percentage * 50)
                    + (wpm * 2 * (self.object.reading_level or 1.0))
                )

                if "quiz_attempts" not in request.session:
                    request.session["quiz_attempts"] = {}
                if "total_xp" not in request.session:
                    request.session["total_xp"] = 0

                request.session.set_expiry(60 * 24 * 60 * 60)  # 60 days

                article_key = str(self.object.id)
                request.session["quiz_attempts"][article_key] = {
                    "score": score_percentage,
                    "wpm_used": wpm,
                    "xp_awarded": xp_earned,
                    "quiz_time_seconds": quiz_time_seconds,
                    "user_answers": user_answers,
                    "article_title": self.object.title,
                }
                request.session["total_xp"] += xp_earned
                request.session["current_wpm"] = wpm
                request.session.modified = True

                if score_percentage >= 60:
                    messages.success(
                        request,
                        _(
                            "Quiz passed! You earned %(xp)d XP. Register to save your progress and unlock commenting!"
                        )
                        % {"xp": xp_earned},
                    )
                else:
                    messages.info(
                        request,
                        _(
                            "Quiz completed with %(score).0f%%. You earned %(xp)d XP. Register to save your progress!"
                        )
                        % {"score": score_percentage, "xp": xp_earned},
                    )

        elif "post_comment" in request.POST:
            if not user.is_authenticated:
                messages.error(request, _("Please register or login to post comments."))
                return redirect(self.object.get_absolute_url())

            content = request.POST.get("comment_content")
            parent_id = request.POST.get("parent_comment_id")
            parent_comment = (
                get_object_or_404(Comment, id=parent_id) if parent_id else None
            )

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
                    is_perfect_score_free=perfect_score_privilege,
                )
                messages.success(request, _("Your comment has been posted."))
            except InsufficientXPError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(
                    request, _("An unexpected error occurred: %(error)s") % {"error": e}
                )

        return redirect(self.object.get_absolute_url())


class UserProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = "verifast_app/user_profile.html"
    context_object_name = "user_profile"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        # Get quiz attempts for this user
        quiz_attempts = QuizAttempt.objects.filter(user=user).order_by("-timestamp")
        context["quiz_attempts_count"] = quiz_attempts.count()
        context["recent_quiz_attempts"] = quiz_attempts[:5]  # Last 5 attempts

        # Calculate statistics
        if quiz_attempts.exists():
            scores = [attempt.score for attempt in quiz_attempts]
            context["average_score"] = sum(scores) / len(scores)
            context["total_xp_earned"] = sum(
                attempt.xp_awarded for attempt in quiz_attempts
            )
        else:
            context["average_score"] = 0
            context["total_xp_earned"] = 0

        # Add XP transaction data for transaction history component
        from .models import XPTransaction

        # Get base queryset for calculations
        all_transactions = XPTransaction.objects.filter(user=user).order_by(
            "-timestamp"
        )

        # Get limited transactions for display
        context["transactions"] = all_transactions[:20]

        # Calculate transaction summary using separate queries
        earned_transactions = all_transactions.filter(transaction_type="EARN")
        spent_transactions = all_transactions.filter(transaction_type="SPEND")

        context["total_earned"] = sum(t.amount for t in earned_transactions)
        context["total_spent"] = abs(
            sum(t.amount for t in spent_transactions)
        )  # Make positive for display
        context["net_xp"] = context["total_earned"] - context["total_spent"]
        context["has_more_transactions"] = all_transactions.count() > 20

        # Add feature store data
        context["features_by_category"] = PremiumFeatureStore.get_features_by_category(
            user
        )

        # Add FeatureControlForm for feature controls
        if 'form' not in kwargs:
             context["form"] = FeatureControlForm(instance=user)

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = FeatureControlForm(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            messages.success(
                request, _("Your feature preferences have been updated successfully!")
            )
            return redirect("verifast_app:user_profile")
        else:
            messages.error(
                request, _("There was an error updating your feature preferences.")
            )
            # Re-render the page with form errors
            context = self.get_context_data(object=self.object)
            context["form"] = form  # Pass the form with errors back to the template
            return self.render_to_response(context)


@login_required
def scrape_article_view(request):
    if request.method == "POST":
        form = ArticleURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]

            if Article.objects.filter(url=url).exists():
                messages.warning(
                    request,
                    _("This article from URL %(url)s is already in our database.")
                    % {"url": url},
                )
                return redirect("verifast_app:article_list")

            scrape_and_save_article.apply_async(args=[url], queue='acquisition')
            messages.success(
                request,
                _(
                    "Your article has been submitted and is being processed in the background!"
                ),
            )
            return redirect("verifast_app:article_list")
    else:
        form = ArticleURLForm()

    return render(request, "verifast_app/scrape_article.html", {"form": form})


class AddCommentView(View):
    """Handle adding new comments via HTMX"""

    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)

        content = request.POST.get("content", "").strip()

        if not content:
            messages.error(request, _("Comment content cannot be empty."))
            return self.render_comments_list(article, request.user)

        if request.user.is_authenticated:
            # Determine if commenter has passed the quiz
            passed = QuizAttempt.objects.filter(user=request.user, article=article, score__gte=60).exists()
            if not passed:
                messages.error(request, _("You must pass the quiz with a score of 60% or higher to comment."))
                return self.render_comments_list(article, request.user)

            # Check for perfect score privilege (free commenting)
            perfect_score_privilege = QuizAttempt.objects.filter(user=request.user, article=article, score__gte=100).exists()

            try:
                SocialInteractionManager.post_comment(
                    user=request.user,
                    article=article,
                    content=content,
                    parent_comment=None,
                    is_perfect_score_free=perfect_score_privilege,
                )
                messages.success(request, _("Your comment has been posted successfully."))
            except InsufficientXPError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(
                    request,
                    _("An unexpected error occurred: %(error)s") % {"error": str(e)},
                )
        else:
            # Anonymous user logic
            attempts = request.session.get("quiz_attempts", {})
            art_key = str(article.id)
            passed = art_key in attempts and attempts[art_key].get("score", 0) >= 60

            if not passed:
                messages.error(request, _("You must pass the quiz with a score of 60% or higher to comment."))
                return self.render_comments_list(article, request.user)

            # Anonymous comment: store under a dedicated 'guest' user (create if missing)
            from django.contrib.auth import get_user_model
            from django.utils.crypto import get_random_string
            from django.core.signing import Signer
            User = get_user_model()
            guest_user, created = User.objects.get_or_create(
                username="guest",
                defaults={
                    "email": "guest@example.com",
                    "is_staff": False,
                    "is_superuser": False,
                    "password": get_random_string(32),
                },
            )
            display_name = request.POST.get('guest_name','Anonymous').strip() or 'Anonymous'
            try:
                SocialInteractionManager.post_comment(
                    user=guest_user,
                    article=article,
                    content=f"[Guest: {display_name}] {content}",
                    parent_comment=None,
                    is_perfect_score_free=True,  # Guests do not spend XP
                )
                # Set signed cookie for guest_name (30 days)
                signer = Signer()
                signed_name = signer.sign(display_name)
                self.response = self.render_comments_list(article, request.user)
                self.response.set_cookie('vf_guest_name', signed_name, max_age=60*60*24*30, samesite='Lax')
                messages.success(request, _("Your comment has been posted successfully."))
                return self.response
            except Exception as e:
                messages.error(
                    request,
                    _("An unexpected error occurred: %(error)s") % {"error": str(e)},
                )

        # Simple throttling for anonymous posts (max 5 per 10 minutes per session)
        if not request.user.is_authenticated:
            key = f"guest_comment_count_{article_id}"
            count = request.session.get(key, 0)
            if count >= 5:
                messages.error(request, _("You are commenting too frequently. Please try again later."))
                return self.render_comments_list(article, request.user)
            request.session[key] = count + 1
            # Set expiry sliding window (~10 minutes)
            request.session.set_expiry(600)

        return self.render_comments_list(article, request.user)

    def render_comments_list(self, article, user):
        """Render updated comments list for HTMX response"""
        comments = (
            Comment.objects.filter(article=article, parent_comment__isnull=True)
            .select_related("user")
            .prefetch_related("replies__user")
            .order_by("-timestamp")
        )

        return render(
            self.request,
            "verifast_app/partials/comments_list.html",
            {"comments": comments, "user": user, "article": article},
        )


class CommentsSectionView(View):
    """Return the refreshed comments section (form + list) for HTMX reload after quiz pass."""
    def get(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        user = request.user
        # Determine if user can comment now
        user_can_comment = False
        if user.is_authenticated:
            user_can_comment = QuizAttempt.objects.filter(
                user=user, article=article, score__gte=60
            ).exists()
        # Prepare comments queryset
        comments = (
            Comment.objects.filter(article=article, parent_comment__isnull=True)
            .select_related("user")
            .prefetch_related("replies__user")
            .order_by("-timestamp")
        )
        # Pre-fill guest name from signed cookie if present
        from django.core.signing import Signer, BadSignature
        signer = Signer()
        guest_name = None
        cookie_val = request.COOKIES.get('vf_guest_name')
        if cookie_val:
            try:
                guest_name = signer.unsign(cookie_val)
            except BadSignature:
                guest_name = None

        response = render(
            request,
            "verifast_app/partials/comments_section.html",
            {"article": article, "comments": comments, "user": user, "user_can_comment": user_can_comment, "guest_name": guest_name},
        )
        return response


class CommentInteractView(LoginRequiredMixin, View):
    def post(self, request, comment_id):
        user = request.user
        comment = get_object_or_404(Comment, id=comment_id)
        interaction_type = request.POST.get(
            "type"
        )  # Fixed: template sends 'type', not 'interaction_type'

        try:
            SocialInteractionManager.add_interaction(
                user=user, comment=comment, interaction_type=interaction_type
            )
            messages.success(
                request,
                _("Your %(interaction_type)s interaction has been recorded.")
                % {"interaction_type": interaction_type.lower()},
            )
        except InsufficientXPError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(
                request, _("An unexpected error occurred: %(error)s") % {"error": e}
            )

        # Return updated comments list for HTMX
        comments = (
            Comment.objects.filter(article=comment.article, parent_comment__isnull=True)
            .select_related("user")
            .prefetch_related("replies__user")
            .order_by("-timestamp")
        )

        return render(
            request,
            "verifast_app/partials/comments_list.html",
            {"comments": comments, "user": user},
        )


class UserRegistrationView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("verifast_app:index")

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in after successful registration
        login(self.request, self.object)

        # Transfer session data to user account
        session_xp = self.request.session.get("total_xp", 0)
        session_wpm = self.request.session.get("current_wpm", 250)
        session_quiz_attempts = self.request.session.get("quiz_attempts", {})

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
                        score=attempt_data["score"],
                        wpm_used=attempt_data["wpm_used"],
                        xp_awarded=attempt_data["xp_awarded"],
                        quiz_time_seconds=attempt_data.get("quiz_time_seconds", 0),
                        result={
                            "user_answers": attempt_data.get("user_answers", "[]"),
                            "quiz_data": article.quiz_data,
                        },
                    )
                    transferred_attempts += 1
                except (Article.DoesNotExist, ValueError, KeyError):
                    continue

            # Clear session data
            self.request.session.pop("total_xp", None)
            self.request.session.pop("current_wpm", None)
            self.request.session.pop("quiz_attempts", None)
            self.request.session.modified = True

            if transferred_attempts > 0:
                messages.success(
                    self.request,
                    _(
                        "Welcome to VeriFast, %(username)s! Your progress has been saved: %(xp)d XP and %(attempts)d quiz attempts transferred to your account."
                    )
                    % {
                        "username": self.object.username,
                        "xp": session_xp,
                        "attempts": transferred_attempts,
                    },
                )
            else:
                messages.success(
                    self.request,
                    _(
                        "Welcome to VeriFast, %(username)s! Your %(xp)d XP has been added to your account."
                    )
                    % {"username": self.object.username, "xp": session_xp},
                )
        else:
            messages.success(
                self.request,
                _(
                    "Welcome to VeriFast, %(username)s! You start with 0 XP and 250 WPM reading speed."
                )
                % {"username": self.object.username},
            )

        return response


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = "verifast_app/profile_edit.html"
    success_url = reverse_lazy("verifast_app:user_profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _("Your profile has been updated successfully!"))
        return super().form_valid(form)


class QuizSubmissionAPIView(View):
    """
    API endpoint for submitting quiz answers, grading, and awarding XP.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            # Handle both HTMX form data and JSON data
            if request.content_type == "application/json":
                data = json.loads(request.body)
                article_id = data.get("article_id")
                wpm_used = data.get("wpm_used")
                quiz_time_seconds = data.get("quiz_time_seconds")
                user_answers = data.get("user_answers")
            else:
                # HTMX form submission
                article_id = request.POST.get("article_id")
                wpm_used = request.POST.get("wpm_used")
                quiz_time_seconds = request.POST.get("quiz_time_seconds")

                # Collect answers from form fields
                user_answers = []
                question_index = 0
                while f"question_{question_index}" in request.POST:
                    answer = request.POST.get(f"question_{question_index}")
                    user_answers.append(int(answer) if answer else -1)
                    question_index += 1

            article = get_object_or_404(Article, id=article_id)
            user = request.user

            if user.is_authenticated:
                # Handle authenticated users
                quiz_attempt = QuizAttempt.objects.create(
                    user=user,
                    article=article,
                    score=0,  # Will be updated by processor
                    wpm_used=int(wpm_used) if wpm_used else 250,
                    xp_awarded=0,  # Will be updated by processor
                    quiz_time_seconds=int(quiz_time_seconds)
                    if quiz_time_seconds
                    else 0,
                    result={
                        "user_answers": user_answers,
                        "quiz_data": article.quiz_data,
                    },
                )

                result_data = QuizResultProcessor.process_quiz_completion(
                    quiz_attempt=quiz_attempt, article=article, user=user
                )

                # For HTMX requests, return HTML template
                if "HX-Request" in request.headers:
                    response = render(
                        request,
                        "verifast_app/partials/quiz_results.html",
                        {
                            "article": article,
                            "score": result_data["score"],
                            "xp_earned": result_data["xp_breakdown"]["total_xp"],
                            "messages": result_data["messages"],
                            "result_type": result_data["result_type"],
                            "user_can_comment": result_data["score"] >= 60,
                            "feedback": result_data.get("feedback", []),
                        },
                    )
                    # Trigger a client-side event so the comments section can refresh via HTMX
                    if result_data["score"] >= 60:
                        response["HX-Trigger"] = json.dumps({"quiz-passed": True})
                    return response
                else:
                    # JSON response for API calls
                    return JsonResponse(
                        {
                            "success": True,
                            "score": result_data["score"],
                            "xp_earned": result_data["xp_breakdown"]["total_xp"],
                            "messages": result_data["messages"],
                            "result_type": result_data["result_type"],
                            "new_xp_balance": user.current_xp_points,
                        }
                    )
            else:
                # Handle anonymous users with session-based scoring
                from collections import namedtuple
                QuizAttemptMock = namedtuple('QuizAttemptMock', ['result'])
                mock_attempt = QuizAttemptMock(result={'user_answers': user_answers, 'quiz_data': article.quiz_data})

                # Use the robust grader from QuizResultProcessor
                score = QuizResultProcessor.grade_quiz(mock_attempt, article)
                
                xp_earned = max(10, int(score * 0.5))  # Basic XP for anonymous users

                # Store in session
                if "quiz_attempts" not in request.session:
                    request.session["quiz_attempts"] = {}

                request.session["quiz_attempts"][str(article.id)] = {
                    "score": score,
                    "xp_earned": xp_earned,
                    "timestamp": timezone.now().isoformat(),
                }
                if wpm_used:
                    try:
                        request.session["current_wpm"] = int(wpm_used)
                    except (ValueError, TypeError):
                        pass # Ignore if wpm_used is not a valid integer
                request.session.modified = True

                feedback = []
                if score >= 60:
                    feedback = QuizResultProcessor.build_incorrect_feedback(mock_attempt, article)

                if "HX-Request" in request.headers:
                    return render(
                        request,
                        "verifast_app/partials/quiz_results.html",
                        {
                            "article": article,
                            "score": score,
                            "xp_earned": xp_earned,
                            "messages": {
                                "main_message": f"Quiz completed with {score}% score!"
                            },
                            "result_type": "passed" if score >= 60 else "failed",
                            "user_can_comment": False,  # Anonymous users can't comment
                            "feedback": feedback,
                        },
                    )
                else:
                    return JsonResponse(
                        {
                            "success": True,
                            "score": score,
                            "xp_earned": xp_earned,
                            "messages": {
                                "main_message": f"Quiz completed with {score}% score!"
                            },
                            "result_type": "passed" if score >= 60 else "failed",
                            "feedback": feedback,
                        }
                    )

        except json.JSONDecodeError:
            if "HX-Request" in request.headers:
                return render(
                    request,
                    "verifast_app/partials/quiz_error.html",
                    {"error_message": "Invalid quiz data format"},
                )
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Article.DoesNotExist:
            if "HX-Request" in request.headers:
                return render(
                    request,
                    "verifast_app/partials/quiz_error.html",
                    {"error_message": "Article not found"},
                )
            return JsonResponse(
                {"success": False, "error": "Article not found"}, status=404
            )
        except Exception as e:
            if "HX-Request" in request.headers:
                return render(
                    request,
                    "verifast_app/partials/quiz_error.html",
                    {"error_message": str(e)},
                )
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class PurchaseFeatureView(LoginRequiredMixin, View):
    """
    Handle premium feature purchases via AJAX requests.
    """

    def post(self, request):
        try:
            # Parse JSON data from request
            data = json.loads(request.body)
            feature_key = data.get("feature_key")

            if not feature_key:
                return JsonResponse(
                    {"success": False, "error": "Feature key is required"}, status=400
                )

            # Attempt to purchase the feature
            with transaction.atomic():
                feature_purchase = PremiumFeatureStore.purchase_feature(
                    user=request.user, feature_key=feature_key
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Successfully purchased {feature_purchase.feature_display_name}!",
                        "new_balance": request.user.current_xp_points,
                        "feature_name": feature_purchase.feature_display_name,
                    }
                )

        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON data"}, status=400
            )

        except InsufficientXPError as e:
            return JsonResponse(
                {"success": False, "error": f"Insufficient XP: {str(e)}"}, status=400
            )

        except InvalidFeatureError as e:
            return JsonResponse(
                {"success": False, "error": f"Invalid feature: {str(e)}"}, status=400
            )

        except FeatureAlreadyOwnedError as e:
            return JsonResponse(
                {"success": False, "error": f"Feature already owned: {str(e)}"},
                status=400,
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"An unexpected error occurred: {str(e)}"},
                status=500,
            )


class PremiumStoreView(LoginRequiredMixin, View):
    """
    Display the premium feature store where users can purchase premium features with XP.
    """

    def get(self, request):
        # Get available premium features from the store (organized by category)
        features_by_category = PremiumFeatureStore.get_features_by_category(
            request.user
        )

        # Flatten features for template display
        available_features = {}
        user_owned_features = []

        for category, features in features_by_category.items():
            for feature in features:
                feature_key = feature["key"]
                available_features[feature_key] = {
                    "display_name": feature["name"],
                    "description": feature["description"],
                    "cost": feature["cost"],
                    "category": category,
                }
                if feature["owned"]:
                    user_owned_features.append(feature_key)

        context = {
            "available_features": available_features,
            "user_owned_features": user_owned_features,
            "user_xp": request.user.current_xp_points,
            "is_admin": request.user.is_superuser,
        }

        return render(request, "verifast_app/premium_store.html", context)


# Tag System Views


class QuizInitView(LoginRequiredMixin, View):
    """
    HTMX endpoint to initialize quiz interface.
    """

    def get(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)

        # Check if user has completed reading (this should be tracked by reading completion)
        context = {
            "article": article,
            "quiz_data": article.quiz_data,
            "user_wpm": request.user.current_wpm
            if request.user.is_authenticated
            else 250,
        }

        return render(request, "verifast_app/partials/quiz_interface.html", context)


class ReadingCompleteView(LoginRequiredMixin, View):
    """
    HTMX endpoint to handle reading completion and unlock quiz.
    """

    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)

        # Mark reading as complete for this user (could store in session or user model)
        # For now, just return the unlocked quiz button

        context = {"article": article, "reading_completed": True}

        return render(request, "verifast_app/partials/quiz_unlock.html", context)


def speed_reader_init(request, article_id):
    """Initialize speed reader with preprocessed content and user power-ups"""
    article = get_object_or_404(Article, id=article_id)
    user = request.user if request.user.is_authenticated else None

    # Server-side content processing with user power-ups
    word_chunks = process_content_with_powerups(article.content, user)
    settings = get_user_reading_settings(user, request=request)

    # Add validation for empty content
    if not word_chunks:
        return render(
            request,
            "verifast_app/partials/speed_reader_error.html",
            {
                "error_message": "No readable content found in this article.",
                "article_id": article.id,
            },
        )

    return render(
        request,
        "verifast_app/partials/speed_reader_active.html",
        {
            "word_chunks_json": json.dumps(word_chunks),
            "user_wpm": settings.get("wpm", 250),
            "font_family": settings.get("font_family", "default"),
            "article_id": article.id,
            "article_type": "wikipedia" if article.is_wikipedia_article else "regular",
        },
    )


def process_content_with_powerups(content, user):
    """Process article content with user's purchased power-ups applied"""
    if not content:
        return []

    # Import strip_tags for HTML content cleaning
    from django.utils.html import strip_tags
    import logging

    logger = logging.getLogger(__name__)

    # Clean HTML tags and normalize whitespace
    # Check if content seems to contain HTML tags before stripping
    if '<' in content and '>' in content:
        logger.info("Content appears to be HTML, stripping tags.")
        clean_content = strip_tags(content).strip()
    else:
        logger.info("Content appears to be plain text, no need to strip tags.")
        clean_content = content.strip()

    if not clean_content:
        logger.warning("Content is empty after cleaning.")
        return []

    # Improved word splitting to handle various punctuation and contractions
    words = re.findall(r"[\w']+|[.,!?;:()\"\“\”\[\]{}]", clean_content)
    logger.info(f"Split content into {len(words)} words/tokens.")

    if not user or not user.is_authenticated:
        return words


    # Respect explicit user profile selections rather than auto-owning features (especially for staff)
    # Use the user's boolean fields set via profile for chunking and smart features.
    has_5 = getattr(user, 'has_5word_chunking', False)
    has_4 = getattr(user, 'has_4word_chunking', False)
    has_3 = getattr(user, 'has_3word_chunking', False)
    has_2 = getattr(user, 'has_2word_chunking', False)
    use_conn = getattr(user, 'has_smart_connector_grouping', False)
    use_sym = getattr(user, 'has_smart_symbol_handling', False)

    # Apply chunking based on user's selected features (highest wins)
    fixed_chunk_size = None
    if has_5:
        fixed_chunk_size = 5
    elif has_4:
        fixed_chunk_size = 4
    elif has_3:
        fixed_chunk_size = 3
    elif has_2:
        fixed_chunk_size = 2

    if fixed_chunk_size:
        # Respect fixed chunking and skip connector grouping to avoid conflicts
        chunks = create_word_chunks(words, fixed_chunk_size)
    else:
        # Default to single words, then allow smart grouping if enabled
        chunks = words
        if use_conn:
            chunks = apply_smart_connector_grouping(chunks)

    # Apply smart symbol handling if enabled
    if use_sym:
        chunks = apply_smart_symbol_handling(chunks)

    return chunks


def create_word_chunks(words, chunk_size):
    """Create word chunks of specified size"""
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
    return chunks


def apply_smart_connector_grouping(chunks):
    """Group common connectors and stop words with adjacent words"""
    connectors = {
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
    }
    processed_chunks = []

    i = 0
    while i < len(chunks):
        current_chunk = chunks[i]

        # Check if current chunk starts with a connector
        first_word = current_chunk.split()[0].lower() if current_chunk.split() else ""

        if first_word in connectors and i > 0:
            # Merge with previous chunk
            processed_chunks[-1] = processed_chunks[-1] + " " + current_chunk
        else:
            processed_chunks.append(current_chunk)

        i += 1

    return processed_chunks


def apply_smart_symbol_handling(chunks):
    """Apply elegant punctuation and symbol display with a robust regex approach."""
    import re
    processed_chunks = []

    # Regex: remove space before punctuation, fix quotes spacing
    space_before_punct = re.compile(r"\s+([,.!?;:])")

    for chunk in chunks:
        # Remove spaces before punctuation
        chunk = space_before_punct.sub(r"\1", chunk)
        # Normalize quotes spacing
        chunk = chunk.replace(' "', '"').replace('" ', '"')
        processed_chunks.append(chunk)

    return processed_chunks


def get_user_reading_settings(user, request=None):
    """Get user's reading settings and preferences"""
    if not user or not user.is_authenticated:
        if request:
            return {"wpm": request.session.get("current_wpm", 250), "font_family": "default", "theme": "light"}
        return {"wpm": 250, "font_family": "default", "theme": "light"}

    return {
        "wpm": user.current_wpm,
        "font_family": get_user_font_preference(user),
        "theme": getattr(user, "theme", "light"),
    }


def get_user_font_preference(user):
    """Determine user's font preference based on purchased features.
    Returns one of: 'opendyslexic', 'opensans', 'roboto', 'merriweather', 'playfair', 'default'.
    Only one should be active at a time via the profile form, but we check all to be safe.
    """
    if getattr(user, 'has_font_opendyslexic', False):
        return 'opendyslexic'
    if getattr(user, 'has_font_opensans', False):
        return 'opensans'
    if getattr(user, 'has_font_roboto', False):
        return 'roboto'
    if getattr(user, 'has_font_merriweather', False):
        return 'merriweather'
    if getattr(user, 'has_font_playfair', False):
        return 'playfair'
    return 'default'


from django.views.decorators.http import require_POST


def speed_reader_complete(request, article_id):
    """Handle reading completion and unlock quiz via HTMX"""
    if request.method == "POST":
        article = get_object_or_404(Article, id=article_id)
        user = request.user
        xp_awarded = 0
        
        wpm = request.POST.get("wpm")
        if wpm:
            if user.is_authenticated:
                try:
                    user.current_wpm = int(wpm)
                    user.save(update_fields=['current_wpm'])
                except (ValueError, TypeError):
                    pass
            else:
                try:
                    request.session["current_wpm"] = int(wpm)
                    request.session.modified = True
                except (ValueError, TypeError):
                    pass

        if user.is_authenticated:
            # Award reading XP using the XP system
            from .xp_system import XPTransactionManager

            # Calculate reading XP based on article difficulty and length
            base_xp = 25
            difficulty_multiplier = (
                article.reading_level / 10.0 if article.reading_level else 1.0
            )
            length_bonus = (
                min(article.word_count / 1000 * 5, 20) if article.word_count else 0
            )

            xp_awarded = int(base_xp * difficulty_multiplier + length_bonus)

            # Create XP transaction (this will automatically update user's XP)
            XPTransactionManager.earn_xp(
                user=user,
                amount=xp_awarded,
                source="reading_completion",
                description=f"Completed reading: {article.title}",
                reference_obj=article,
            )

        else:
            # Handle anonymous users with session-based XP
            if "total_xp" not in request.session:
                request.session["total_xp"] = 0

            # Calculate XP for anonymous users
            base_xp = 15  # Lower XP for anonymous users
            xp_awarded = base_xp

            request.session["total_xp"] += xp_awarded
            request.session.modified = True

        return render(
            request,
            "verifast_app/partials/quiz_unlock.html",
            {
                "article": article,
                "xp_awarded": xp_awarded,
            },
        )


class QuizSubmitView(View):
    def post(self, request, article_id):
        # This view is a placeholder. The actual implementation will require more logic.
        article = get_object_or_404(Article, id=article_id)
        context = {
            "article": article,
            "quiz_data": article.quiz_data,
            "user_wpm": request.user.current_wpm
            if request.user.is_authenticated
            else 250,
        }
        return render(request, "verifast_app/partials/quiz_interface.html", context)


@require_POST
def update_reading_wpm(request):
    """Persist user's reading speed (WPM) to profile or session."""
    wpm = request.POST.get("wpm") or request.body.decode() if request.body else None
    try:
        # If JSON body like {"wpm": 300}
        if request.content_type == "application/json" and request.body:
            import json as _json
            data = _json.loads(request.body)
            wpm = data.get("wpm", wpm)
        wpm_val = int(str(wpm).strip()) if wpm is not None else None
    except Exception:
        return JsonResponse({"success": False, "error": "invalid_wpm"}, status=400)

    if wpm_val is None or wpm_val < 50 or wpm_val > 2000:
        return JsonResponse({"success": False, "error": "out_of_range"}, status=400)

    if request.user.is_authenticated:
        try:
            request.user.current_wpm = wpm_val
            request.user.save(update_fields=["current_wpm"]) 
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    else:
        request.session["current_wpm"] = wpm_val
        # Persist for 60 days so anonymous users keep their speed between articles
        request.session.set_expiry(60 * 24 * 60 * 60)
        request.session.modified = True

    return JsonResponse({"success": True, "wpm": wpm_val})


class QuizNextQuestionView(View):
    def post(self, request, article_id):
        # This view is a placeholder. The actual implementation will require more logic.
        article = get_object_or_404(Article, id=article_id)
        context = {
            "article": article,
            "quiz_data": article.quiz_data,
            "user_wpm": request.user.current_wpm
            if request.user.is_authenticated
            else 250,
        }
        return render(request, "verifast_app/partials/quiz_interface.html", context)


class QuizStartView(View):
    def get(self, request, article_id):
        """HTMX endpoint to start quiz interface."""
        article = get_object_or_404(Article, id=article_id)

        # Check if quiz data exists
        if not article.quiz_data:
            return render(
                request,
                "verifast_app/partials/quiz_unavailable.html",
                {"article": article},
            )

        # Parse quiz data and prepare for server-side rendering
        try:
            raw = (
                json.loads(article.quiz_data)
                if isinstance(article.quiz_data, str)
                else article.quiz_data
            )
            # Normalize quiz structure to a list of question dicts
            if isinstance(raw, dict):
                if isinstance(raw.get('quiz'), list):
                    quiz_questions_raw = raw.get('quiz')
                elif isinstance(raw.get('questions'), list):
                    quiz_questions_raw = raw.get('questions')
                else:
                    quiz_questions_raw = []
            elif isinstance(raw, list):
                quiz_questions_raw = raw
            else:
                quiz_questions_raw = []

            # Normalize options: accept both strings and {"text": "..."}
            quiz_questions = []
            for q in quiz_questions_raw:
                if not isinstance(q, dict):
                    continue
                opts = q.get('options', [])
                norm_opts = [o.get('text') if isinstance(o, dict) else o for o in opts]
                # Support 'correct_answer' index or text, or 'answer'
                correct_val = q.get('correct_answer', q.get('answer', 0))
                if isinstance(correct_val, int):
                    correct_idx = correct_val
                elif isinstance(correct_val, str) and correct_val in norm_opts:
                    correct_idx = norm_opts.index(correct_val)
                else:
                    correct_idx = 0
                quiz_questions.append({
                    'question': q.get('question', ''),
                    'options': norm_opts,
                    'correct_answer': correct_idx
                })
        except (json.JSONDecodeError, TypeError):
            return render(
                request,
                "verifast_app/partials/quiz_unavailable.html",
                {"article": article},
            )

        context = {
            "article": article,
            "quiz_questions": quiz_questions,
            "user_wpm": request.user.current_wpm
            if request.user.is_authenticated
            else request.session.get("current_wpm", 250),
            "total_questions": len(quiz_questions) if quiz_questions else 0,
        }
        return render(request, "verifast_app/partials/quiz_interface.html", context)


class TagSearchView(ListView):
    """
    Tag search and discovery page with filtering and search functionality.
    """

    model = Tag
    template_name = "verifast_app/tag_search.html"
    context_object_name = "tags"
    paginate_by = 20

    def get_queryset(self):
        """Get filtered tags based on search query and filters with caching."""
        # Get search parameters
        query = self.request.GET.get("q", "").strip()
        search_type = self.request.GET.get("type", "all")  # 'tags', 'articles', 'all'

        # Create cache key based on search parameters
        cache_key_data = f"tag_search_{search_type}_{query}"
        cache_key = hashlib.md5(force_str(cache_key_data).encode()).hexdigest()

        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # If not in cache, perform the query
        queryset = Tag.objects.filter(is_validated=True).order_by(
            "-article_count", "name"
        )

        if query:
            if search_type == "tags":
                # Search only in tag names and descriptions
                queryset = queryset.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )
            elif search_type == "articles":
                # Find tags that have articles matching the query
                matching_articles = Article.objects.filter(
                    Q(title__icontains=query) | Q(content__icontains=query),
                    processing_status="complete",
                )
                queryset = queryset.filter(article__in=matching_articles).distinct()
            else:  # 'all'
                # Search in both tags and articles
                tag_matches = Q(name__icontains=query) | Q(description__icontains=query)
                article_matches = Q(article__title__icontains=query) | Q(
                    article__content__icontains=query
                )
                queryset = (
                    queryset.filter(tag_matches | article_matches)
                    .filter(article__processing_status="complete")
                    .distinct()
                )

        # Cache the result for 15 minutes
        cache.set(cache_key, queryset, 60 * 15)

        return queryset

    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)

        # Get search parameters
        context["search_query"] = self.request.GET.get("q", "")
        context["search_type"] = self.request.GET.get("type", "all")

        # Get popular tags using analytics service
        popular_tag_stats = get_popular_tags(limit=10)
        context["popular_tags"] = [stat["tag"] for stat in popular_tag_stats]

        # Get trending tags using analytics service
        trending_tag_stats = get_trending_tags(days=7, limit=10)
        context["trending_tags"] = [stat["tag"] for stat in trending_tag_stats]

        # Get recent tags (fallback)
        context["recent_tags"] = Tag.objects.filter(is_validated=True).order_by(
            "-created_at"
        )[:10]

        # Get tag statistics
        context["total_tags"] = Tag.objects.filter(is_validated=True).count()
        context["total_articles"] = Article.objects.filter(
            processing_status="complete"
        ).count()

        # If searching articles, get matching articles
        if context["search_query"] and context["search_type"] in ["articles", "all"]:
            context["matching_articles"] = (
                Article.objects.filter(
                    Q(title__icontains=context["search_query"])
                    | Q(content__icontains=context["search_query"]),
                    processing_status="complete",
                )
                .select_related("user")
                .prefetch_related("tags")[:10]
            )

        return context


class TagDetailView(DetailView):
    """
    Individual tag detail page showing Wikipedia article and related articles.
    """

    model = Tag
    template_name = "verifast_app/tag_detail.html"
    context_object_name = "tag"
    slug_field = "name"
    slug_url_kwarg = "tag_name"

    def get_object(self, queryset=None):
        """Get tag by name (case-insensitive)."""
        tag_name = self.kwargs.get("tag_name")
        return get_object_or_404(Tag, name__iexact=tag_name)

    def get_context_data(self, **kwargs):
        """Add related articles and tag statistics."""
        context = super().get_context_data(**kwargs)
        tag = self.object

        # Get all articles for this tag
        all_articles = (
            tag.article_set.filter(processing_status="complete")
            .select_related("user")
            .order_by("-timestamp")
        )

        # Separate Wikipedia articles from regular articles
        wikipedia_articles = all_articles.filter(article_type="wikipedia")
        regular_articles = all_articles.filter(article_type="regular")

        context["wikipedia_articles"] = wikipedia_articles
        context["regular_articles"] = regular_articles
        context["total_articles"] = all_articles.count()

        # Get the main Wikipedia article (first one if multiple exist)
        context["main_wikipedia_article"] = wikipedia_articles.first()

        # Get related tags using analytics service
        related_tag_relationships = get_tag_relationships(tag, limit=10)
        context["related_tags"] = [rel["tag"] for rel in related_tag_relationships]

        # Pagination for regular articles
        from django.core.paginator import Paginator

        paginator = Paginator(regular_articles, 10)
        page_number = self.request.GET.get("page")
        context["articles_page"] = paginator.get_page(page_number)

        # Tag statistics
        context["tag_stats"] = {
            "total_articles": all_articles.count(),
            "wikipedia_articles": wikipedia_articles.count(),
            "regular_articles": regular_articles.count(),
            "last_updated": tag.last_updated,
        }

        return context


class WikipediaArticleView(DetailView):
    """
    View for displaying Wikipedia articles with full VeriFast functionality.
    """

    model = Article
    template_name = "verifast_app/wikipedia_article.html"
    context_object_name = "article"

    def get_queryset(self):
        """Only allow Wikipedia articles."""
        return Article.objects.filter(
            article_type="wikipedia", processing_status="complete"
        )

    def get_context_data(self, **kwargs):
        """Add Wikipedia-specific context."""
        context = super().get_context_data(**kwargs)
        article = self.object

        # Check if user has taken quiz for this article
        if self.request.user.is_authenticated:
            context["user_quiz_attempts"] = QuizAttempt.objects.filter(
                user=self.request.user, article=article
            ).order_by("-timestamp")

            context["has_taken_quiz"] = context["user_quiz_attempts"].exists()
            context["best_score"] = (
                context["user_quiz_attempts"].aggregate(Max("score"))["score__max"]
                if context["has_taken_quiz"]
                else None
            )

        # Get article comments
        context["comments"] = (
            Comment.objects.filter(article=article)
            .select_related("user")
            .prefetch_related("replies")
            .order_by("-timestamp")
        )

        # Get related articles through shared tags
        shared_tags = article.tags.all()
        context["related_articles"] = (
            Article.objects.filter(tags__in=shared_tags, processing_status="complete")
            .exclude(id=article.id)
            .distinct()[:5]
        )

        # Wikipedia-specific context
        context["is_wikipedia"] = True
        context["wikipedia_url"] = article.url
        context["source_tag"] = (
            article.tags.first()
        )  # The tag this Wikipedia article represents

        return context


@login_required
def update_language_preference(request):
    """Update user's language preference"""
    if request.method == "POST":
        preferred_language = request.POST.get("preferred_language")

        if preferred_language in ["en", "es"]:
            request.user.preferred_language = preferred_language
            request.user.save(update_fields=["preferred_language"])
            messages.success(request, _("Language preference updated successfully!"))
        else:
            messages.error(request, _("Invalid language selection."))

    return redirect(request.META.get("HTTP_REFERER", "verifast_app:index"))


def language_filter_articles(request):
    """HTMX endpoint for filtering articles by language"""
    language_filter = request.GET.get("lang", "all")

    # Base queryset for complete articles
    articles = Article.objects.filter(processing_status="complete")

    # Apply language filter
    if language_filter and language_filter != "all":
        articles = articles.filter(language=language_filter)

    # Handle sorting and pagination
    if request.user.is_authenticated:
        # Annotate with read status
        read_articles = QuizAttempt.objects.filter(
            user=request.user, article=OuterRef("pk")
        )
        articles = articles.annotate(is_read_by_user=Exists(read_articles)).order_by(
            "is_read_by_user", "-timestamp"
        )
    else:
        articles = articles.order_by("-timestamp")

    # Pagination
    from django.core.paginator import Paginator

    paginator = Paginator(articles, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "current_language": language_filter,
        "is_htmx": True,
    }

    return render(request, "verifast_app/partials/article_list_content.html", context)
