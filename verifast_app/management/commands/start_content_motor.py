"""
Django Management Command: Start Content Motor
Simple command to start the content acquisition system
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from ...models_content_acquisition import ContentSource, ContentAcquisitionJob
from ...tasks_content_acquisition import acquire_content_from_source
from ...services.content_orchestrator import ContentAcquisitionOrchestrator


class Command(BaseCommand):
    help = "Start the content motor to acquire articles from configured sources"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sources",
            nargs="+",
            help="Specific source names to run (default: all active sources)",
        )
        parser.add_argument(
            "--languages",
            nargs="+",
            default=["en", "es"],
            help="Languages to acquire content for (default: en es)",
        )
        parser.add_argument(
            "--max-articles",
            type=int,
            default=20,
            help="Maximum articles to acquire per source (default: 20)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually doing it",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force acquisition even if sources have recent failures",
        )
        parser.add_argument(
            "--orchestrate",
            action="store_true",
            help="Use orchestrated acquisition (recommended)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting VeriFast Content Motor"))

        # Get sources to process
        sources_queryset = ContentSource.objects.filter(is_active=True)

        if options["sources"]:
            sources_queryset = sources_queryset.filter(name__in=options["sources"])
            if not sources_queryset.exists():
                raise CommandError(
                    f"No active sources found with names: {options['sources']}"
                )

        if not sources_queryset.exists():
            raise CommandError(
                "No active content sources found. Please configure sources in the admin."
            )

        sources = list(sources_queryset)

        # Check source health unless forced
        if not options["force"]:
            unhealthy_sources = []
            for source in sources:
                health_score = source.get_health_score()
                if health_score < 50:
                    unhealthy_sources.append(
                        f"{source.name} (health: {health_score}/100)"
                    )

            if unhealthy_sources:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Unhealthy sources detected:\n"
                        + "\n".join(f"  - {s}" for s in unhealthy_sources)
                    )
                )
                if not options["dry_run"]:
                    confirm = input("Continue anyway? (y/N): ")
                    if confirm.lower() != "y":
                        self.stdout.write("Aborted.")
                        return

        # Show what will be done
        self.stdout.write("\n📋 Content Acquisition Plan:")
        self.stdout.write(f"  Sources: {len(sources)}")
        self.stdout.write(f"  Languages: {', '.join(options['languages'])}")
        self.stdout.write(f"  Max articles per source: {options['max_articles']}")
        self.stdout.write(
            f"  Mode: {'Orchestrated' if options['orchestrate'] else 'Individual'}"
        )

        for source in sources:
            can_request, reason = source.can_make_request()
            status_icon = "✅" if can_request else "❌"
            self.stdout.write(
                f"  {status_icon} {source.name} ({source.get_source_type_display()}) - {reason}"
            )

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(
                    "\n🔍 DRY RUN - No actual acquisition will be performed"
                )
            )
            return

        # Execute acquisition
        if options["orchestrate"]:
            self._run_orchestrated_acquisition(options)
        else:
            self._run_individual_acquisition(sources, options)

    def _run_orchestrated_acquisition(self, options):
        """Run orchestrated content acquisition"""
        self.stdout.write("\n🎯 Starting orchestrated content acquisition...")

        try:
            orchestrator = ContentAcquisitionOrchestrator()
            result = orchestrator.orchestrate_acquisition(
                languages=options["languages"], max_articles=options["max_articles"]
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Orchestrated acquisition completed:\n"
                    f"  Sources processed: {result['sources_processed']}\n"
                    f"  Sources successful: {result['sources_successful']}\n"
                    f"  Total articles found: {result['total_articles_found']}\n"
                    f"  Total articles processed: {result['total_articles_processed']}\n"
                    f"  Duplicates skipped: {result['total_articles_duplicated']}\n"
                    f"  Articles rejected: {result['total_articles_rejected']}"
                )
            )

            if result.get("errors"):
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  Errors encountered:\n"
                        + "\n".join(f"  - {error}" for error in result["errors"])
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Orchestrated acquisition failed: {str(e)}")
            )

    def _run_individual_acquisition(self, sources, options):
        """Run individual source acquisition"""
        self.stdout.write("\n🔄 Starting individual source acquisition...")

        task_ids = []
        successful_sources = []
        failed_sources = []

        for source in sources:
            try:
                can_request, reason = source.can_make_request()

                if not can_request and not options["force"]:
                    failed_sources.append(f"{source.name}: {reason}")
                    continue

                # Trigger acquisition task
                task = acquire_content_from_source.delay(
                    source.id, "manual", options["max_articles"]
                )

                task_ids.append(task.id)
                successful_sources.append(source.name)

                self.stdout.write(f"  ✅ Queued {source.name} (Task: {task.id})")

            except Exception as e:
                failed_sources.append(f"{source.name}: {str(e)}")
                self.stdout.write(f"  ❌ Failed to queue {source.name}: {str(e)}")

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎯 Acquisition tasks queued:\n"
                f"  Successful: {len(successful_sources)}\n"
                f"  Failed: {len(failed_sources)}\n"
                f"  Task IDs: {', '.join(task_ids[:5])}"
                + (f" (+{len(task_ids) - 5} more)" if len(task_ids) > 5 else "")
            )
        )

        if failed_sources:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Failed sources:\n"
                    + "\n".join(f"  - {error}" for error in failed_sources)
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n📊 Monitor progress:\n"
                f"  - Django Admin: /admin/verifast_app/contentacquisitionjob/\n"
                f"  - Celery Flower: http://localhost:5555 (if running)\n"
                f"  - Logs: tail -f celery.log"
            )
        )

    def _show_recent_activity(self):
        """Show recent acquisition activity"""
        recent_jobs = ContentAcquisitionJob.objects.select_related("source").order_by(
            "-created_at"
        )[:5]

        if recent_jobs:
            self.stdout.write("\n📈 Recent acquisition activity:")
            for job in recent_jobs:
                duration = job.get_duration()
                duration_str = f"{duration:.1f}s" if duration > 0 else "ongoing"

                self.stdout.write(
                    f"  {job.created_at.strftime('%H:%M')} - {job.source.name} "
                    f"({job.get_status_display()}) - {job.articles_processed} articles - {duration_str}"
                )
        else:
            self.stdout.write("\n📈 No recent acquisition activity")
