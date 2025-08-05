#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Import after Django setup to avoid import issues
from verifast_app.models import Comment

# Check the Comment model fields
print("Comment model fields:")
for field in Comment._meta.get_fields():
    print(f"  - {field.name}: {type(field).__name__}")

# Check if parent_comment field exists
try:
    parent_field = Comment._meta.get_field("parent_comment")
    print(f"\nparent_comment field found: {parent_field}")
except Exception:
    print("\nparent_comment field NOT found")

# Check if parent field exists (the error field)
try:
    parent_field = Comment._meta.get_field("parent")
    print(f"\nparent field found: {parent_field}")
except Exception:
    print("\nparent field NOT found (this is expected)")
