#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.models import Article

print(f"🔍 Total articles in database: {Article.objects.count()}")
print("\n📰 Recent articles:")

recent_articles = Article.objects.order_by('-timestamp')[:10]
for i, article in enumerate(recent_articles, 1):
    print(f"  {i}. {article.title[:70]}...")
    print(f"     Source: {article.acquisition_source or 'manual'}")
    print(f"     Status: {article.processing_status}")
    print(f"     Language: {article.language}")
    print(f"     Created: {article.timestamp.strftime('%Y-%m-%d %H:%M')}")
    print()

if Article.objects.count() == 0:
    print("❌ No articles found. The content motor may not have processed any articles successfully.")
else:
    print(f"✅ Found {Article.objects.count()} articles in the database!")