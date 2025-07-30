# Fix Tag model fields
# Date: 2025-07-21

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('verifast_app', '0002_add_tag_wikipedia_fields'),
    ]

    operations = [
        # Make slug unique and non-null
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(max_length=50, unique=True, blank=True),
        ),
        # Fix timestamp fields to not be nullable
        migrations.AlterField(
            model_name='tag',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tag',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]