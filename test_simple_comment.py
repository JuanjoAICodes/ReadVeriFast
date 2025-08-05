#!/usr/bin/env python
"""Simple test to check comment functionality without full template rendering."""

import os
import sys

# Setup Django before importing Django modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.test import Client
from django.urls import reverse
from verifast_app.models import CustomUser, Article


def test_simple_comment():
    """Test comment functionality with direct view access."""
    client = Client()

    # Get an existing article
    try:
        article = Article.objects.first()
        if not article:
            print("❌ No articles found in database")
            return

        print(f"✅ Testing with article: {article.title} (ID: {article.id})")

        # Test article detail URL construction
        url = reverse("verifast_app:article_detail", kwargs={"pk": article.pk})
        print(f"✅ Article URL: {url}")

        # Use the correct language prefix
        if url.startswith("/en-us/"):
            url = url.replace("/en-us/", "/en/")
            print(f"✅ Corrected URL: {url}")

        # Test as anonymous user
        print("\n=== ANONYMOUS USER TEST ===")
        try:
            response = client.get(url)
            print(f"✅ Response status: {response.status_code}")

            if response.status_code == 200:
                content = response.content.decode("utf-8")

                # Check for key elements
                checks = [
                    ("comments-section", "Comments section"),
                    ("add-comment-form", "Add comment form"),
                    ("Complete the quiz", "Quiz completion message"),
                    ("speed-reader-section", "Speed reader section"),
                    ("quiz-section", "Quiz section"),
                ]

                for check_text, description in checks:
                    if check_text in content:
                        print(f"✅ {description} found")
                    else:
                        print(f"❌ {description} NOT found")
            else:
                print(f"❌ Failed to load page: {response.status_code}")

        except Exception as e:
            print(f"❌ Error loading page: {e}")

        # Test with authenticated user
        print("\n=== AUTHENTICATED USER TEST ===")
        try:
            user = CustomUser.objects.filter(username="testuser").first()
            if user:
                client.force_login(user)
                print(f"✅ Logged in as {user.username}")

                response = client.get(url)
                print(f"✅ Response status: {response.status_code}")

                if response.status_code == 200:
                    content = response.content.decode("utf-8")

                    # Check for authenticated user elements
                    if "<textarea" in content:
                        print("✅ Comment textarea found")
                    else:
                        print("❌ Comment textarea NOT found")

                    if "Share your thoughts" in content:
                        print("✅ Comment placeholder found")
                    else:
                        print("❌ Comment placeholder NOT found")
                else:
                    print(f"❌ Failed to load page: {response.status_code}")
            else:
                print("❌ testuser not found")

        except Exception as e:
            print(f"❌ Error with authenticated test: {e}")

    except Exception as e:
        print(f"❌ General error: {e}")


if __name__ == "__main__":
    test_simple_comment()
