#!/usr/bin/env python3
"""
Integration validation test for Unified Article Detail Implementation
Tests the complete user journey and component integration
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.models import Article, Tag

User = get_user_model()

class UnifiedArticleDetailIntegrationTest(TestCase):
    """Test complete integration of all article detail components"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            current_wpm=300
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='Technology', slug='technology')
        self.tag2 = Tag.objects.create(name='AI', slug='ai')
        
        # Create test article
        self.article = Article.objects.create(
            title='Test Article for Integration',
            content='This is a test article with enough content to test the speed reader functionality. ' * 20,
            source='Test Source',
            processing_status='complete',
            word_count=100,
            reading_level=8.5,
            language='en'
        )
        self.article.tags.add(self.tag1, self.tag2)
        
        # Create related article
        self.related_article = Article.objects.create(
            title='Related Test Article',
            content='This is a related article for testing.',
            source='Test Source',
            processing_status='complete',
            word_count=50,
            language='en'
        )
        self.related_article.tags.add(self.tag1)
    
    def test_article_detail_page_loads(self):
        """Test that article detail page loads with all components"""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertContains(response, 'speed-reader-section')
        self.assertContains(response, 'quiz-section')
        self.assertContains(response, 'comments-section')
        self.assertContains(response, 'related-articles')
    
    def test_article_header_metadata(self):
        """Test article header displays all metadata correctly"""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertContains(response, 'Test Source')
        self.assertContains(response, '8.5')  # Reading level
        self.assertContains(response, '100')  # Word count
        self.assertContains(response, 'article-header')
        self.assertContains(response, 'article-meta')
    
    def test_tags_section_display(self):
        """Test tags are displayed as clickable links"""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertContains(response, 'Technology')
        self.assertContains(response, 'AI')
        self.assertContains(response, 'tag-link')
        self.assertContains(response, 'article-tags')
    
    def test_speed_reader_htmx_integration(self):
        """Test speed reader HTMX endpoint integration"""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        # Check for HTMX attributes
        self.assertContains(response, 'hx-get')
        self.assertContains(response, 'speed_reader_init')
        self.assertContains(response, 'hx-target="#speed-reader-section"')
        self.assertContains(response, 'Start Reading')
    
    def test_authenticated_user_context(self):
        """Test authenticated user gets proper context"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertContains(response, '300')  # User WPM
        self.assertContains(response, 'data-user-wpm="300"')
    
    def test_anonymous_user_defaults(self):
        """Test anonymous user gets default values"""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertContains(response, '250')  # Default WPM
        self.assertContains(response, 'data-user-wpm="250"')
    
    def test_related_articles_display(self):
        """Test related articles are shown"""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertContains(response, 'Related Articles')
        self.assertContains(response, 'related-articles-grid')
        self.assertContains(response, self.related_article.title)
    
    def test_css_classes_present(self):
        """Test that all required CSS classes are present"""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        # Check for key CSS classes from our implementation
        required_classes = [
            'article-header',
            'article-header-content',
            'article-tags',
            'tag-list',
            'speed-reader-section',
            'immersive-overlay',
            'immersive-word-display',
            'immersive-controls',
            'quiz-section',
            'comments-section',
            'related-articles',
            'related-articles-grid'
        ]
        
        for css_class in required_classes:
            self.assertContains(response, css_class)
    
    def test_responsive_design_meta_tags(self):
        """Test responsive design meta tags are present"""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        # Should inherit from base template
        self.assertContains(response, 'viewport')

if __name__ == '__main__':
    # Run the tests
    import unittest
    
    print("🧪 Running Unified Article Detail Integration Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(UnifiedArticleDetailIntegrationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
        print("🎉 Unified Article Detail Implementation is ready!")
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)