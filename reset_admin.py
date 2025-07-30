#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Try to get existing superuser or create new one
try:
    # Try to find existing superuser
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if admin_user:
        print(f"Found existing superuser: {admin_user.username}")
        # Reset password
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"Password reset for user '{admin_user.username}' to 'admin123'")
    else:
        # Create new superuser
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("Created new superuser 'admin' with password 'admin123'")
        
except Exception as e:
    print(f"Error: {e}")