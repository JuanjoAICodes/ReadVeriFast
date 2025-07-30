#!/usr/bin/env python
"""
Setup script for automated content acquisition system.
This script handles database migrations and initial setup.
"""

import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def run_migration():
    """Apply the automated content acquisition migration."""
    try:
        print("Applying automated content acquisition migration...")
        
        # Check if migration exists
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        
        # Get current migration state
        current_migrations = executor.loader.applied_migrations
        print(f"Current migrations: {len(current_migrations)}")
        
        # Apply the specific migration
        from django.core.management.commands.migrate import Command
        migrate_command = Command()
        migrate_command.handle(
            app_label='verifast_app',
            migration_name='0005',
            verbosity=1,
            interactive=False,
            fake=False,
            fake_initial=False,
            plan=False,
            run_syncdb=False,
            check_unapplied=False
        )
        
        print("Migration applied successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

def verify_models():
    """Verify that the new models are working correctly."""
    try:
        from verifast_app.models import Article, ContentAcquisitionLog
        
        # Test Article model with new fields
        print("Testing Article model...")
        article_count = Article.objects.count()
        print(f"Current articles in database: {article_count}")
        
        # Test ContentAcquisitionLog model
        print("Testing ContentAcquisitionLog model...")
        log_count = ContentAcquisitionLog.objects.count()
        print(f"Current acquisition logs: {log_count}")
        
        print("Model verification successful!")
        return True
        
    except Exception as e:
        print(f"Model verification failed: {e}")
        return False

def setup_cache():
    """Test Redis cache configuration."""
    try:
        from django.core.cache import cache
        
        # Test cache connection
        cache.set('test_key', 'test_value', 30)
        value = cache.get('test_key')
        
        if value == 'test_value':
            print("Redis cache configured successfully!")
            cache.delete('test_key')
            return True
        else:
            print("Redis cache test failed!")
            return False
            
    except Exception as e:
        print(f"Redis cache setup failed: {e}")
        print("Make sure Redis is running: redis-server")
        return False

if __name__ == '__main__':
    print("=== Automated Content Acquisition Setup ===")
    
    success = True
    
    # Step 1: Apply migration
    if not run_migration():
        success = False
    
    # Step 2: Verify models
    if not verify_models():
        success = False
    
    # Step 3: Setup cache (optional)
    if not setup_cache():
        print("Warning: Redis cache not available, but system can work without it")
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("Next steps:")
        print("1. Install missing dependencies: pip install django-redis==5.4.0")
        print("2. Start Redis server: redis-server")
        print("3. Continue with Content Acquisition Manager implementation")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)