from django.core.management.base import BaseCommand
from verifast_app.services.model_selector import model_selector
import json


class Command(BaseCommand):
    help = 'Test the model selector and fallback system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reading-level',
            type=float,
            default=30.0,
            help='Reading level for testing (default: 30.0)'
        )
        parser.add_argument(
            '--word-count',
            type=int,
            default=500,
            help='Word count for testing (default: 500)'
        )
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            choices=['en', 'es'],
            help='Language for testing (default: en)'
        )
        parser.add_argument(
            '--source',
            type=str,
            default='user_submission',
            help='Source type for testing (default: user_submission)'
        )

    def handle(self, *args, **options):
        reading_level = options['reading_level']
        word_count = options['word_count']
        language = options['language']
        source = options['source']
        
        self.stdout.write("Model Selector Test")
        self.stdout.write("=" * 50)
        
        # Test model selection
        self.stdout.write(f"Testing with:")
        self.stdout.write(f"  Reading level: {reading_level}")
        self.stdout.write(f"  Word count: {word_count}")
        self.stdout.write(f"  Language: {language}")
        self.stdout.write(f"  Source: {source}")
        
        try:
            selected_model, model_config = model_selector.select_model(
                reading_level=reading_level,
                word_count=word_count,
                language=language,
                source=source
            )
            
            self.stdout.write(f"\nSelected model: {selected_model}")
            self.stdout.write(f"Model tier: {model_config.tier.value}")
            self.stdout.write(f"Max tokens: {model_config.max_tokens}")
            self.stdout.write(f"Temperature: {model_config.temperature}")
            self.stdout.write(f"Supports languages: {model_config.supports_languages}")
            
            # Test generation config
            generation_config = model_selector.get_generation_config(model_config, 5)
            self.stdout.write(f"\nGeneration config for 5 questions:")
            self.stdout.write(json.dumps(generation_config, indent=2))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Model selection failed: {str(e)}")
            )
        
        # Show model statistics
        self.stdout.write("\nModel Statistics:")
        self.stdout.write("-" * 30)
        stats = model_selector.get_model_stats()
        for model_name, model_stats in stats.items():
            status = "✓ Available" if model_stats['failure_count'] == 0 else f"✗ Failed ({model_stats['failure_count']} times)"
            self.stdout.write(f"{model_name:20} | {model_stats['tier']:10} | {status}")
            if model_stats['last_failure']:
                self.stdout.write(f"                     | Last failure: {model_stats['last_failure']}")
        
        # Test different scenarios
        self.stdout.write("\nTesting different scenarios:")
        self.stdout.write("-" * 40)
        
        scenarios = [
            {"name": "Simple article", "reading_level": 60, "word_count": 200, "source": "user_submission"},
            {"name": "Complex article", "reading_level": 15, "word_count": 1500, "source": "user_submission"},
            {"name": "Gutenberg text", "reading_level": 25, "word_count": 3000, "source": "gutenberg"},
            {"name": "Spanish article", "reading_level": 40, "word_count": 800, "source": "user_submission", "language": "es"},
        ]
        
        for scenario in scenarios:
            lang = scenario.get('language', 'en')
            try:
                selected, config = model_selector.select_model(
                    reading_level=scenario['reading_level'],
                    word_count=scenario['word_count'],
                    language=lang,
                    source=scenario['source']
                )
                self.stdout.write(f"{scenario['name']:15} → {selected} ({config.tier.value})")
            except Exception as e:
                self.stdout.write(f"{scenario['name']:15} → ERROR: {str(e)}")