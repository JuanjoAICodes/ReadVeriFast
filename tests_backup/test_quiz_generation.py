from django.core.management.base import BaseCommand
from django.utils import timezone
from verifast_app.models import Article
from verifast_app.tasks import process_article
import time


class Command(BaseCommand):
    help = "Test quiz generation by creating sample articles and processing them"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=3,
            help="Number of test articles to create (default: 3)",
        )
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Process articles synchronously instead of using Celery",
        )

    def handle(self, *args, **options):
        count = options["count"]
        sync_mode = options["sync"]

        self.stdout.write(f"Creating {count} test articles for quiz generation...")

        # Sample articles with different complexities
        sample_articles = [
            {
                "title": "The Benefits of Reading",
                "content": """Reading is one of the most beneficial activities for the human mind. It improves vocabulary, enhances critical thinking skills, and provides knowledge about various subjects. Regular reading can also reduce stress and improve focus.

Studies have shown that people who read regularly have better memory retention and are more empathetic. Reading fiction, in particular, helps develop emotional intelligence by allowing readers to experience different perspectives and situations.

Furthermore, reading before bedtime can improve sleep quality. The act of reading helps calm the mind and prepare it for rest. Many successful people attribute their achievements to their reading habits.

In conclusion, reading is a simple yet powerful tool for personal development and mental well-being.""",
                "language": "en",
                "source": "test_generation",
            },
            {
                "title": "Climate Change and Its Effects",
                "content": """Climate change refers to long-term shifts in global temperatures and weather patterns. While climate variations are natural, scientific evidence shows that human activities have been the main driver of climate change since the 1800s.

The primary cause is the burning of fossil fuels like coal, oil, and gas, which releases greenhouse gases into the atmosphere. These gases trap heat from the sun, causing global temperatures to rise.

The effects of climate change are already visible worldwide. Ice caps are melting, sea levels are rising, and extreme weather events are becoming more frequent. These changes threaten ecosystems, agriculture, and human settlements.

To address climate change, countries are working together to reduce greenhouse gas emissions. Renewable energy sources like solar and wind power are becoming more popular. Individual actions, such as using public transportation and reducing energy consumption, also make a difference.

The fight against climate change requires global cooperation and immediate action to protect our planet for future generations.""",
                "language": "en",
                "source": "test_generation",
            },
            {
                "title": "La Importancia de la Educación",
                "content": """La educación es fundamental para el desarrollo personal y social. Proporciona las herramientas necesarias para comprender el mundo y participar activamente en la sociedad.

A través de la educación, las personas desarrollan habilidades de pensamiento crítico, aprenden a resolver problemas y adquieren conocimientos especializados. Esto les permite tomar decisiones informadas y contribuir al progreso de sus comunidades.

La educación también promueve la igualdad de oportunidades. Cuando todas las personas tienen acceso a una educación de calidad, se reducen las desigualdades sociales y económicas.

En el mundo moderno, la educación continua es esencial. Los avances tecnológicos y los cambios en el mercado laboral requieren que las personas actualicen constantemente sus conocimientos y habilidades.

Por tanto, invertir en educación es invertir en el futuro de la sociedad.""",
                "language": "es",
                "source": "test_generation",
            },
        ]

        created_articles = []

        for i in range(min(count, len(sample_articles))):
            article_data = sample_articles[i]

            article = Article.objects.create(
                title=article_data["title"],
                content=article_data["content"],
                language=article_data["language"],
                source=article_data["source"],
                processing_status="pending",
                timestamp=timezone.now(),
            )

            created_articles.append(article)
            self.stdout.write(f"Created article {article.id}: {article.title}")

        # Process articles
        if sync_mode:
            self.stdout.write("Processing articles synchronously...")
            for article in created_articles:
                self.stdout.write(f"Processing article {article.id}...")
                try:
                    result = process_article(article.id)
                    if result.get("success"):
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Article {article.id} processed successfully"
                            )
                        )

                        # Refresh from database to see results
                        article.refresh_from_db()
                        if article.quiz_data:
                            quiz_count = (
                                len(article.quiz_data)
                                if isinstance(article.quiz_data, list)
                                else 0
                            )
                            self.stdout.write(
                                f"  Generated {quiz_count} quiz questions"
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING("  No quiz data generated")
                            )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Article {article.id} processing failed: {result.get('error')}"
                            )
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Article {article.id} processing error: {str(e)}"
                        )
                    )
        else:
            self.stdout.write("Queuing articles for async processing...")
            for article in created_articles:
                process_article.delay(article.id)
                self.stdout.write(f"Queued article {article.id} for processing")

            self.stdout.write(
                "Articles queued. Check Celery logs for processing status."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Test completed. Created {len(created_articles)} articles."
            )
        )
