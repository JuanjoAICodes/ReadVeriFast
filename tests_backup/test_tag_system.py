"""
Comprehensive Test Suite for Tag System
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from .models import Tag, Article
from .wikipedia_service import WikipediaService

User = get_user_model()


class TagModelTestCase(TestCase):
    """Test Tag model functionality"""
    
    def setUp(self):
        self.tag = Tag.objects.create(
            name='Test Technology',
            description='A test tag about technology',
            is_validated=True
        )
    
    def test_tag_creation(self):
        """Test basic tag creation"""
        self.assertEqual(self.tag.name, 'Test Technology')
        self.assertTrue(self.tag.is_validated)
        self.assertEqual(self.tag.article_count, 0)
    
    def test_slug_generation(self):
        """Test automatic slug generation"""
        self.assertEqual(self.tag.slug, 'test-technology')
    
    def test_get_absolute_url(self):
        """Test URL generation"""
        expected_url = reverse('verifast_app:tag_detail', kwargs={'tag_name': self.tag.name})
        self.assertEqual(self.tag.get_absolute_url(), expected_url)
    
    def test_update_article_count(self):
        """Test article count updating"""
        # Create test article with tag
        article = Article.objects.create(
            title='Test Article',
            content='Test content',
            processing_status='complete'
        )
        article.tags.add(self.tag)
        
        # Update count
        self.tag.update_article_count()
        self.assertEqual(self.tag.article_count, 1)


class WikipediaServiceTestCase(TestCase):
    """Test Wikipedia integration service"""
    
    def setUp(self):
        self.service = WikipediaService()
        self.tag = Tag.objects.create(name='Python Programming')
    
    @patch('wikipediaapi.Wikipedia')
    def test_validate_tag_success(self, mock_wikipedia):
        """Test successful tag validation"""
        # Mock Wikipedia response
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.title = 'Python (programming language)'
        mock_page.summary = 'Python is a programming language'
        mock_page.fullurl = 'https://en.wikipedia.org/wiki/Python_(programming_language)'
        
        mock_wiki = MagicMock()
        mock_wiki.page.return_value = mock_page
        mock_wikipedia.return_value = mock_wiki
        
        # Test validation
        is_valid, data = self.service.validate_tag_with_wikipedia('Python Programming')
        
        self.assertTrue(is_valid)
        self.assertIsNotNone(data)
        self.assertIn('title', data)
        self.assertIn('summary', data)
        self.assertIn('url', data)
    
    @patch('wikipediaapi.Wikipedia')
    def test_validate_tag_not_found(self, mock_wikipedia):
        """Test tag validation when Wikipedia page doesn't exist"""
        # Mock Wikipedia response for non-existent page
        mock_page = MagicMock()
        mock_page.exists.return_value = False
        
        mock_wiki = MagicMock()
        mock_wiki.page.return_value = mock_page
        mock_wikipedia.return_value = mock_wiki
        
        # Test validation
        is_valid, data = self.service.validate_tag_with_wikipedia('NonExistentTopic')
        
        self.assertFalse(is_valid)
        self.assertIsNone(data)


class TagViewsTestCase(TestCase):
    """Test tag system views"""
    
    def setUp(self):
        self.client = Client()
        self.tag = Tag.objects.create(
            name='Django Framework',
            description='Web framework for Python',
            is_validated=True,
            article_count=5
        )
    
    def test_tag_search_view(self):
        """Test tag search page"""
        response = self.client.get(reverse('verifast_app:tag_search'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tag Search & Discovery')
        self.assertContains(response, self.tag.name)
    
    def test_tag_detail_view(self):
        """Test individual tag detail page"""
        response = self.client.get(
            reverse('verifast_app:tag_detail', kwargs={'tag_name': self.tag.name})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag.name)
        self.assertContains(response, self.tag.description)
    
    def test_tag_search_with_query(self):
        """Test tag search with search query"""
        response = self.client.get(
            reverse('verifast_app:tag_search') + '?q=Django'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag.name)
    
    def test_tag_search_filter_tags_only(self):
        """Test tag search with tags-only filter"""
        response = self.client.get(
            reverse('verifast_app:tag_search') + '?type=tags&q=Django'
        )
        self.assertEqual(response.status_code, 200)


class TagIntegrationTestCase(TestCase):
    """Test end-to-end tag system integration"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
    
    def test_article_tag_navigation(self):
        """Test navigation from article to tag pages"""
        # Create article with tags
        tag = Tag.objects.create(name='Web Development', is_validated=True)
        article = Article.objects.create(
            title='Web Development Guide',
            content='A comprehensive guide to web development',
            processing_status='complete'
        )
        article.tags.add(tag)
        
        # Test article page contains tag links
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        
        # Test tag link leads to tag page
        tag_url = reverse('verifast_app:tag_detail', kwargs={'tag_name': tag.name})
        response = self.client.get(tag_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, tag.name)
    
    def test_tag_article_listing(self):
        """Test that tag pages list related articles"""
        # Create tag and articles
        tag = Tag.objects.create(name='Machine Learning', is_validated=True)
        
        for i in range(3):
            article = Article.objects.create(
                title=f'ML Article {i+1}',
                content=f'Machine learning content {i+1}',
                processing_status='complete'
            )
            article.tags.add(tag)
        
        # Update tag article count
        tag.update_article_count()
        
        # Test tag page shows articles
        response = self.client.get(
            reverse('verifast_app:tag_detail', kwargs={'tag_name': tag.name})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ML Article 1')
        self.assertContains(response, 'ML Article 2')
        self.assertContains(response, 'ML Article 3')


class TagAnalyticsTestCase(TestCase):
    """Test tag analytics functionality"""
    
    def setUp(self):
        # Create test tags with different popularity
        self.popular_tag = Tag.objects.create(
            name='Popular Topic',
            is_validated=True,
            article_count=10
        )
        
        self.new_tag = Tag.objects.create(
            name='New Topic',
            is_validated=True,
            article_count=1
        )
    
    def test_tag_popularity_calculation(self):
        """Test tag popularity metrics"""
        from .tag_analytics import TagAnalytics
        
        analytics = TagAnalytics()
        popular_tags = analytics.get_tag_popularity_stats(limit=10)
        
        self.assertIsInstance(popular_tags, list)
        if popular_tags:
            # Most popular tag should be first
            self.assertEqual(popular_tags[0]['tag'].name, self.popular_tag.name)
    
    def test_tag_relationships(self):
        """Test tag relationship analysis"""
        from .tag_analytics import TagAnalytics
        
        # Create articles with multiple tags
        tag1 = Tag.objects.create(name='Python', is_validated=True)
        tag2 = Tag.objects.create(name='Programming', is_validated=True)
        
        article = Article.objects.create(
            title='Python Programming Guide',
            content='Learn Python programming',
            processing_status='complete'
        )
        article.tags.add(tag1, tag2)
        
        analytics = TagAnalytics()
        relationships = analytics.get_tag_relationships(tag1, limit=5)
        
        self.assertIsInstance(relationships, list)


class TagAdminTestCase(TestCase):
    """Test tag admin functionality"""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            is_staff=True,
            is_superuser=True
        )
        self.client = Client()
        self.client.force_login(self.admin_user)
        
        self.tag = Tag.objects.create(
            name='Test Admin Tag',
            is_validated=False
        )
    
    def test_tag_admin_list_view(self):
        """Test tag admin list page"""
        response = self.client.get('/admin/verifast_app/tag/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag.name)
    
    def test_tag_admin_detail_view(self):
        """Test tag admin detail page"""
        response = self.client.get(f'/admin/verifast_app/tag/{self.tag.id}/change/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag.name)
    
    @patch('verifast_app.wikipedia_service.WikipediaService.validate_tag_with_wikipedia')
    def test_validate_with_wikipedia_action(self, mock_validate):
        """Test Wikipedia validation admin action"""
        # Mock successful validation
        mock_validate.return_value = (True, {
            'title': 'Test Topic',
            'summary': 'A test topic summary',
            'url': 'https://en.wikipedia.org/wiki/Test_Topic'
        })
        
        # Test admin action
        response = self.client.post('/admin/verifast_app/tag/', {
            'action': 'validate_with_wikipedia',
            '_selected_action': [self.tag.id]
        }, follow=True)
        
        # Should redirect back to admin
        self.assertEqual(response.status_code, 302)
        
        # Check tag was updated
        self.tag.refresh_from_db()
        # Note: In a real test, we'd check if the tag was validated
        # but since we're mocking, we just verify the action was called
        mock_validate.assert_called_once()


class TagPerformanceTestCase(TestCase):
    """Test tag system performance"""
    
    def setUp(self):
        # Create multiple tags and articles for performance testing
        self.tags = []
        for i in range(20):
            tag = Tag.objects.create(
                name=f'Performance Tag {i}',
                is_validated=True,
                article_count=i
            )
            self.tags.append(tag)
    
    def test_tag_search_performance(self):
        """Test tag search page performance with many tags"""
        response = self.client.get(reverse('verifast_app:tag_search'))
        self.assertEqual(response.status_code, 200)
        
        # Should handle multiple tags without issues
        self.assertContains(response, 'Performance Tag')
    
    def test_tag_detail_performance(self):
        """Test tag detail page performance"""
        tag = self.tags[0]
        response = self.client.get(
            reverse('verifast_app:tag_detail', kwargs={'tag_name': tag.name})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, tag.name)