# Generated manually for automated content acquisition system

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('verifast_app', '0004_alter_customuser_ad_free_articles_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='acquisition_source',
            field=models.CharField(
                choices=[
                    ('manual', 'Manual Submission'),
                    ('rss', 'RSS Feed'),
                    ('newsdata_api', 'NewsData.io API'),
                    ('scraping', 'Web Scraping')
                ],
                default='manual',
                help_text='Source method used to acquire this article.',
                max_length=50,
                verbose_name='Acquisition Source'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='source_url',
            field=models.URLField(
                blank=True,
                help_text='Original URL where the article was acquired from.',
                max_length=500,
                null=True,
                verbose_name='Source URL'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='topic_category',
            field=models.CharField(
                blank=True,
                help_text='Automatically detected topic category (politics, business, etc.).',
                max_length=50,
                verbose_name='Topic Category'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='geographic_focus',
            field=models.CharField(
                blank=True,
                help_text='Geographic region or country focus of the article.',
                max_length=100,
                verbose_name='Geographic Focus'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='acquisition_timestamp',
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                help_text='Timestamp when the article was acquired by the system.',
                verbose_name='Acquisition Timestamp'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='content_quality_score',
            field=models.FloatField(
                default=0.0,
                help_text='Automated quality score for the article content (0.0-1.0).',
                verbose_name='Content Quality Score'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='duplicate_check_hash',
            field=models.CharField(
                blank=True,
                help_text='Hash for duplicate detection based on content similarity.',
                max_length=64,
                verbose_name='Duplicate Check Hash'
            ),
        ),
        migrations.CreateModel(
            name='ContentAcquisitionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, help_text='When this acquisition cycle started.', verbose_name='Timestamp')),
                ('acquisition_type', models.CharField(choices=[('rss', 'RSS Feed'), ('newsdata_api', 'NewsData.io API'), ('scraping', 'Web Scraping'), ('full_cycle', 'Full Acquisition Cycle')], help_text='Type of acquisition performed.', max_length=20, verbose_name='Acquisition Type')),
                ('source_name', models.CharField(help_text='Name of the specific source (e.g., \'BBC News\', \'NewsData.io\').', max_length=100, verbose_name='Source Name')),
                ('articles_acquired', models.IntegerField(default=0, help_text='Number of articles successfully acquired.', verbose_name='Articles Acquired')),
                ('articles_processed', models.IntegerField(default=0, help_text='Number of articles successfully processed and stored.', verbose_name='Articles Processed')),
                ('articles_rejected', models.IntegerField(default=0, help_text='Number of articles rejected due to quality or duplication.', verbose_name='Articles Rejected')),
                ('api_calls_used', models.IntegerField(default=0, help_text='Number of API calls consumed during this acquisition.', verbose_name='API Calls Used')),
                ('errors_encountered', models.JSONField(default=list, help_text='List of errors encountered during acquisition.', verbose_name='Errors Encountered')),
                ('processing_time_seconds', models.FloatField(help_text='Total time taken for this acquisition cycle in seconds.', verbose_name='Processing Time (seconds)')),
                ('language_distribution', models.JSONField(default=dict, help_text='Distribution of articles by language (e.g., {\'en\': 10, \'es\': 5}).', verbose_name='Language Distribution')),
                ('topic_distribution', models.JSONField(default=dict, help_text='Distribution of articles by topic category.', verbose_name='Topic Distribution')),
            ],
            options={
                'verbose_name': 'Content Acquisition Log',
                'verbose_name_plural': 'Content Acquisition Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['acquisition_source'], name='verifast_app_article_acquisition_source_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['topic_category'], name='verifast_app_article_topic_category_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['acquisition_timestamp'], name='verifast_app_article_acquisition_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='contentacquisitionlog',
            index=models.Index(fields=['-timestamp'], name='verifast_app_contentacquisitionlog_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='contentacquisitionlog',
            index=models.Index(fields=['acquisition_type', '-timestamp'], name='verifast_app_contentacquisitionlog_acq_type_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='contentacquisitionlog',
            index=models.Index(fields=['source_name', '-timestamp'], name='verifast_app_contentacquisitionlog_source_timestamp_idx'),
        ),
    ]