"""
Django Management Command: Setup Content Sources
Creates basic content sources for the content motor if they don't exist
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

from ...models_content_acquisition import ContentSource
from ...content_acquisition_config import RSS_SOURCES

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up basic content sources for the content motor'

    def add_arguments(self, parser):
        parser.add_argument(
            '--newsdata-api-key',
            help='NewsData.io API key for news content acquisition',
        )
        parser.add_argument(
            '--gnews-api-key',
            help='GNews API key for news content acquisition',
        )
        parser.add_argument(
            '--newsapi-key',
            help='NewsAPI.org API key for news content acquisition',
        )
        parser.add_argument(
            '--create-sample-rss',
            action='store_true',
            help='Create sample RSS feed sources (BBC, Reuters, El País)',
        )
        parser.add_argument(
            '--create-all-rss',
            action='store_true',
            help='Create all RSS feed sources defined in content_acquisition_config.RSS_SOURCES',
        )
        parser.add_argument(
            '--create-all-apis',
            action='store_true',
            help='Create sources for all available APIs (requires API keys)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Setting up VeriFast Content Sources')
        )
        
        created_count = 0
        updated_count = 0
        
        # Get or create admin user for source ownership
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Sample RSS sources (kept for quick demo)
        rss_sources = [
            {
                'name': 'BBC News RSS',
                'description': 'BBC News RSS feed for English articles',
                'source_type': 'rss',
                'url': 'http://feeds.bbci.co.uk/news/rss.xml',
                'language': 'en',
                'priority': 'high',
                'config_data': {
                    'extract_full_content': True,
                    'category': 'news'
                }
            },
            {
                'name': 'Reuters World News',
                'description': 'Reuters world news RSS feed',
                'source_type': 'rss',
                'url': 'https://www.reuters.com/rssFeed/worldNews',
                'language': 'en',
                'priority': 'normal',
                'config_data': {
                    'extract_full_content': True,
                    'category': 'world'
                }
            },
            {
                'name': 'El País RSS',
                'description': 'El País Spanish news RSS feed',
                'source_type': 'rss',
                'url': 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada',
                'language': 'es',
                'priority': 'normal',
                'config_data': {
                    'extract_full_content': True,
                    'category': 'news'
                }
            }
        ]
        
        # Create RSS sources if requested
        if options['create_sample_rss']:
            for source_data in rss_sources:
                source, created = ContentSource.objects.get_or_create(
                    name=source_data['name'],
                    defaults={
                        **source_data,
                        'created_by': admin_user,
                        'is_active': True,
                        'requests_per_hour': 12,  # Conservative for RSS
                        'requests_per_day': 100
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"  ✅ Created RSS source: {source.name}")
                else:
                    self.stdout.write(f"  ℹ️  RSS source already exists: {source.name}")
        
        # Create ALL RSS sources from config if requested
        if options.get('create_all_rss'):
            for lang_key in ('english', 'spanish'):
                for item in RSS_SOURCES.get(lang_key, []):
                    source_name = f"{item['name']} RSS"
                    source, created = ContentSource.objects.get_or_create(
                        name=source_name,
                        defaults={
                            'description': f"{item['name']} {lang_key.title()} RSS feed",
                            'source_type': 'rss',
                            'url': item['url'],
                            'language': item.get('language') or ('en' if lang_key == 'english' else 'es'),
                            'priority': 'normal',
                            'config_data': {
                                'extract_full_content': True,
                                'category': item.get('category', 'general')
                            },
                            'created_by': admin_user,
                            'is_active': True,
                            'requests_per_hour': 12,
                            'requests_per_day': 100,
                        }
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(f"  ✅ Created RSS source: {source.name}")
                    else:
                        self.stdout.write(f"  ℹ️  RSS source already exists: {source.name}")
        
        # If API keys weren't provided via flags, try environment variables
        options['newsdata_api_key'] = options['newsdata_api_key'] or os.environ.get('NEWSDATA_API_KEY')
        options['gnews_api_key'] = options['gnews_api_key'] or os.environ.get('GNEWS_API_KEY')
        options['newsapi_key'] = options['newsapi_key'] or os.environ.get('NEWSAPI_KEY')

        # NewsData.io API source
        if options['newsdata_api_key']:
            newsdata_sources = [
                {
                    'name': 'NewsData.io English',
                    'description': 'NewsData.io API for English news articles',
                    'source_type': 'newsdata_api',
                    'url': 'https://newsdata.io/api/1/news',
                    'language': 'en',
                    'priority': 'high',
                    'config_data': {
                        'api_key': options['newsdata_api_key'],
                        'categories': ['business', 'technology', 'science', 'health'],
                        'countries': ['us', 'gb', 'ca', 'au']
                    }
                },
                {
                    'name': 'NewsData.io Spanish',
                    'description': 'NewsData.io API for Spanish news articles',
                    'source_type': 'newsdata_api',
                    'url': 'https://newsdata.io/api/1/news',
                    'language': 'es',
                    'priority': 'high',
                    'config_data': {
                        'api_key': options['newsdata_api_key'],
                        'categories': ['business', 'technology', 'science', 'health'],
                        'countries': ['es', 'mx', 'ar', 'co']
                    }
                }
            ]
            
            for source_data in newsdata_sources:
                source, created = ContentSource.objects.get_or_create(
                    name=source_data['name'],
                    defaults={
                        **source_data,
                        'created_by': admin_user,
                        'is_active': True,
                        'requests_per_hour': 20,  # NewsData.io rate limits
                        'requests_per_day': 200
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"  ✅ Created NewsData.io source: {source.name}")
                else:
                    # Update API key if source exists
                    source.config_data['api_key'] = options['newsdata_api_key']
                    source.save()
                    updated_count += 1
                    self.stdout.write(f"  🔄 Updated API key for: {source.name}")
        
        # GNews API sources
        if options['gnews_api_key']:
            gnews_sources = [
                {
                    'name': 'GNews English',
                    'description': 'GNews API for English news articles',
                    'source_type': 'gnews_api',
                    'url': 'https://gnews.io/api/v4',
                    'language': 'en',
                    'priority': 'high',
                    'config_data': {
                        'api_key': options['gnews_api_key'],
                        'category': 'general',
                        'country': 'us'
                    }
                },
                {
                    'name': 'GNews Spanish',
                    'description': 'GNews API for Spanish news articles',
                    'source_type': 'gnews_api',
                    'url': 'https://gnews.io/api/v4',
                    'language': 'es',
                    'priority': 'high',
                    'config_data': {
                        'api_key': options['gnews_api_key'],
                        'category': 'general',
                        'country': 'es'
                    }
                }
            ]
            
            for source_data in gnews_sources:
                source, created = ContentSource.objects.get_or_create(
                    name=source_data['name'],
                    defaults={
                        **source_data,
                        'created_by': admin_user,
                        'is_active': True,
                        'requests_per_hour': 10,  # GNews rate limits
                        'requests_per_day': 100
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"  ✅ Created GNews source: {source.name}")
                else:
                    # Update API key if source exists
                    source.config_data['api_key'] = options['gnews_api_key']
                    source.save()
                    updated_count += 1
                    self.stdout.write(f"  🔄 Updated API key for: {source.name}")
        
        # NewsAPI.org sources
        if options['newsapi_key']:
            newsapi_sources = [
                {
                    'name': 'NewsAPI English',
                    'description': 'NewsAPI.org for English news articles',
                    'source_type': 'newsapi',
                    'url': 'https://newsapi.org/v2',
                    'language': 'en',
                    'priority': 'high',
                    'config_data': {
                        'api_key': options['newsapi_key'],
                        'category': 'general',
                        'country': 'us'
                    }
                },
                {
                    'name': 'NewsAPI Business',
                    'description': 'NewsAPI.org for business news',
                    'source_type': 'newsapi',
                    'url': 'https://newsapi.org/v2',
                    'language': 'en',
                    'priority': 'normal',
                    'config_data': {
                        'api_key': options['newsapi_key'],
                        'category': 'business',
                        'country': 'us'
                    }
                }
            ]
            
            for source_data in newsapi_sources:
                source, created = ContentSource.objects.get_or_create(
                    name=source_data['name'],
                    defaults={
                        **source_data,
                        'created_by': admin_user,
                        'is_active': True,
                        'requests_per_hour': 50,  # NewsAPI rate limits
                        'requests_per_day': 1000
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"  ✅ Created NewsAPI source: {source.name}")
                else:
                    # Update API key if source exists
                    source.config_data['api_key'] = options['newsapi_key']
                    source.save()
                    updated_count += 1
                    self.stdout.write(f"  🔄 Updated API key for: {source.name}")
        
        # Summary
        total_active = ContentSource.objects.filter(is_active=True).count()
        total_sources = ContentSource.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Content sources setup completed:\n"
                f"  Created: {created_count} sources\n"
                f"  Updated: {updated_count} sources\n"
                f"  Total active sources: {total_active} / {total_sources} total"
            )
        )
        
        # Show next steps
        self.stdout.write(
            self.style.SUCCESS(
                "\n🚀 Next steps:\n"
                "  1. Test sources: python manage.py start_content_motor --dry-run\n"
                "  2. Start content motor: python manage.py start_content_motor --orchestrate\n"
                "  3. Monitor in admin: /admin/verifast_app/contentacquisitionjob/\n"
                "  4. Or use the admin action: Go to Articles → Select any → Actions → 🚀 Start Content Motor"
            )
        )
        
        if not options['newsdata_api_key'] and not options['create_sample_rss'] and not options.get('create_all_rss'):
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  No sources were created. Use:\n"
                    "  --create-sample-rss    Create sample RSS sources\n"
                    "  --create-all-rss       Create all RSS sources from config\n"
                    "  --newsdata-api-key     Add NewsData.io API sources\n"
                    "\nExample:\n"
                    "  python manage.py setup_content_sources --create-all-rss --newsdata-api-key YOUR_API_KEY"
                )
            )