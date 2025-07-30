"""
Django management command for testing Pydantic validation pipeline
Usage: python manage.py test_pydantic_validation [--verbose] [--model MODEL_NAME]
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import json
import logging
from typing import Dict, Any, Optional

from ...validation.pipeline import ValidationPipeline
from ...validation.startup_validator import StartupValidator
from ...pydantic_models.llm import (
    MasterAnalysisResponse, QuizQuestion, LLMGenerationRequest
)
from ...pydantic_models.api import (
    ArticleSubmissionRequest, QuizSubmissionRequest, SearchRequest
)
from ...pydantic_models.dto import (
    ArticleAnalysisDTO, XPTransactionDTO, ContentAcquisitionDTO
)


class Command(BaseCommand):
    help = 'Test Pydantic validation pipeline with comprehensive test cases'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output with detailed test results',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Test specific model only (e.g., ArticleAnalysisDTO)',
        )
        parser.add_argument(
            '--startup-check',
            action='store_true',
            help='Run startup configuration validation',
        )
        parser.add_argument(
            '--performance',
            action='store_true',
            help='Run performance benchmarks',
        )
        parser.add_argument(
            '--export-results',
            type=str,
            help='Export test results to JSON file',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        
        # Initialize validation pipeline
        self.pipeline = ValidationPipeline(logger_name="test_command")
        
        # Initialize test results
        self.test_results = {
            'timestamp': timezone.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'performance_metrics': {},
            'startup_validation': None
        }
        
        self.stdout.write(
            self.style.SUCCESS('🧪 Starting Pydantic Validation Testing...')
        )
        
        try:
            # Run startup validation if requested
            if options.get('startup_check'):
                self._run_startup_validation()
            
            # Run model-specific tests or all tests
            if options.get('model'):
                self._test_specific_model(options['model'])
            else:
                self._run_all_tests()
            
            # Run performance benchmarks if requested
            if options.get('performance'):
                self._run_performance_tests()
            
            # Display results
            self._display_results()
            
            # Export results if requested
            if options.get('export_results'):
                self._export_results(options['export_results'])
            
            # Exit with appropriate code
            if self.test_results['failed_tests'] > 0:
                raise CommandError(f"❌ {self.test_results['failed_tests']} tests failed")
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ All {self.test_results['passed_tests']} tests passed!")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Command execution failed: {str(e)}")
            )
            raise CommandError(str(e))
    
    def _run_startup_validation(self):
        """Run startup configuration validation"""
        self.stdout.write("🔍 Running startup configuration validation...")
        
        validator = StartupValidator()
        results = validator.validate_all_configurations()
        
        self.test_results['startup_validation'] = results
        
        if results['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Startup validation passed: {results['summary']['passed']}/{results['summary']['total_checks']} checks"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Startup validation failed: {len(results['errors'])} errors"
                )
            )
            
            if self.verbose:
                for error in results['errors']:
                    self.stdout.write(f"  • {error}")
    
    def _test_specific_model(self, model_name: str):
        """Test a specific Pydantic model"""
        model_tests = {
            'MasterAnalysisResponse': self._test_master_analysis_response,
            'QuizQuestion': self._test_quiz_question,
            'LLMGenerationRequest': self._test_llm_generation_request,
            'ArticleSubmissionRequest': self._test_article_submission_request,
            'QuizSubmissionRequest': self._test_quiz_submission_request,
            'SearchRequest': self._test_search_request,
            'ArticleAnalysisDTO': self._test_article_analysis_dto,
            'XPTransactionDTO': self._test_xp_transaction_dto,
            'ContentAcquisitionDTO': self._test_content_acquisition_dto,
        }
        
        if model_name not in model_tests:
            raise CommandError(f"Unknown model: {model_name}. Available: {', '.join(model_tests.keys())}")
        
        self.stdout.write(f"🧪 Testing {model_name}...")
        model_tests[model_name]()
    
    def _run_all_tests(self):
        """Run all validation tests"""
        self.stdout.write("🧪 Running comprehensive validation tests...")
        
        # Test LLM models
        self._test_master_analysis_response()
        self._test_quiz_question()
        self._test_llm_generation_request()
        
        # Test API models
        self._test_article_submission_request()
        self._test_quiz_submission_request()
        self._test_search_request()
        
        # Test DTO models
        self._test_article_analysis_dto()
        self._test_xp_transaction_dto()
        self._test_content_acquisition_dto()
        
        # Test validation pipeline
        self._test_validation_pipeline()
    
    def _test_master_analysis_response(self):
        """Test MasterAnalysisResponse model"""
        test_cases = [
            # Valid case
            {
                'name': 'Valid MasterAnalysisResponse',
                'data': {
                    "quiz": [
                        {
                            "question": "What is artificial intelligence?",
                            "options": ["AI technology", "Human intelligence", "Computer program", "Data analysis"],
                            "answer": "AI technology",
                            "explanation": "AI refers to artificial intelligence technology."
                        },
                        {
                            "question": "What is machine learning?",
                            "options": ["ML algorithm", "Manual learning", "Memory learning", "Model learning"],
                            "answer": "ML algorithm",
                            "explanation": "ML refers to machine learning algorithms."
                        },
                        {
                            "question": "What is deep learning?",
                            "options": ["Neural networks", "Surface learning", "Quick learning", "Basic learning"],
                            "answer": "Neural networks",
                            "explanation": "Deep learning uses neural networks."
                        },
                        {
                            "question": "What is natural language processing?",
                            "options": ["NLP technology", "Number processing", "Network processing", "Normal processing"],
                            "answer": "NLP technology",
                            "explanation": "NLP processes natural language."
                        },
                        {
                            "question": "What is computer vision?",
                            "options": ["Image processing", "Computer screens", "Vision correction", "Visual computing"],
                            "answer": "Image processing",
                            "explanation": "Computer vision processes images."
                        }
                    ],
                    "tags": ["Technology", "AI", "Science"],
                    "reading_level": 65.5,
                    "key_concepts": ["machine learning", "neural networks"]
                },
                'should_pass': True
            },
            # Invalid case - insufficient quiz questions
            {
                'name': 'Invalid MasterAnalysisResponse - Few Questions',
                'data': {
                    "quiz": [
                        {
                            "question": "Test?",
                            "options": ["A", "B", "C", "D"],
                            "answer": "A"
                        }
                    ] * 3,  # Only 3 questions, need 5
                    "tags": ["Test"]
                },
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(MasterAnalysisResponse, test_case)
    
    def _test_quiz_question(self):
        """Test QuizQuestion model"""
        test_cases = [
            # Valid case
            {
                'name': 'Valid QuizQuestion',
                'data': {
                    "question": "What is the capital of France",
                    "options": ["Paris", "London", "Berlin", "Madrid"],
                    "answer": "Paris",
                    "explanation": "Paris is the capital of France."
                },
                'should_pass': True
            },
            # Invalid case - duplicate options
            {
                'name': 'Invalid QuizQuestion - Duplicate Options',
                'data': {
                    "question": "Test question?",
                    "options": ["A", "B", "A", "D"],  # Duplicate "A"
                    "answer": "A"
                },
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(QuizQuestion, test_case)
    
    def _test_llm_generation_request(self):
        """Test LLMGenerationRequest model"""
        test_cases = [
            # Valid case
            {
                'name': 'Valid LLMGenerationRequest',
                'data': {
                    "content": "This is a comprehensive article about artificial intelligence and machine learning technologies. " * 10,
                    "language": "en",
                    "max_questions": 8,
                    "difficulty_level": "medium"
                },
                'should_pass': True
            },
            # Invalid case - content too short
            {
                'name': 'Invalid LLMGenerationRequest - Short Content',
                'data': {
                    "content": "Too short",
                    "language": "en"
                },
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(LLMGenerationRequest, test_case)
    
    def _test_article_submission_request(self):
        """Test ArticleSubmissionRequest model"""
        test_cases = [
            # Valid case
            {
                'name': 'Valid ArticleSubmissionRequest',
                'data': {
                    "url": "https://example.com/article",
                    "title": "Sample Article",
                    "language": "en",
                    "priority": "normal"
                },
                'should_pass': True
            },
            # Invalid case - localhost URL
            {
                'name': 'Invalid ArticleSubmissionRequest - Localhost',
                'data': {
                    "url": "http://localhost:8000/article",
                    "title": "Test Article"
                },
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(ArticleSubmissionRequest, test_case)
    
    def _test_quiz_submission_request(self):
        """Test QuizSubmissionRequest model"""
        test_cases = [
            # Valid case
            {
                'name': 'Valid QuizSubmissionRequest',
                'data': {
                    "article_id": 123,
                    "answers": [0, 1, 2, 3, 0],
                    "wpm": 250,
                    "reading_time_seconds": 180
                },
                'should_pass': True
            },
            # Invalid case - invalid answer
            {
                'name': 'Invalid QuizSubmissionRequest - Bad Answer',
                'data': {
                    "article_id": 123,
                    "answers": [0, 1, 4, 2],  # 4 is invalid (should be 0-3)
                    "wpm": 250
                },
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(QuizSubmissionRequest, test_case)
    
    def _test_search_request(self):
        """Test SearchRequest model"""
        test_cases = [
            # Valid case
            {
                'name': 'Valid SearchRequest',
                'data': {
                    "query": "machine learning",
                    "filters": {"language": "en", "tags": ["Technology"]},
                    "page": 1,
                    "per_page": 20,
                    "sort_by": "relevance"
                },
                'should_pass': True
            },
            # Invalid case - invalid filters
            {
                'name': 'Invalid SearchRequest - Bad Filters',
                'data': {
                    "query": "test",
                    "filters": {"invalid_filter": "value"}
                },
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(SearchRequest, test_case)
    
    def _test_article_analysis_dto(self):
        """Test ArticleAnalysisDTO model"""
        test_cases = [
            # Valid case
            {
                'name': 'Valid ArticleAnalysisDTO',
                'data': {
                    "article_id": 123,
                    "content": "This is sample article content for analysis. " * 20,
                    "language": "en",
                    "entities": ["OpenAI", "GPT", "Machine Learning"],
                    "reading_level": 65.5,
                    "word_count": 100,
                    "processing_time": 2.5,
                    "confidence_score": 0.92
                },
                'should_pass': True
            },
            # Invalid case - negative article ID
            {
                'name': 'Invalid ArticleAnalysisDTO - Negative ID',
                'data': {
                    "article_id": -1,
                    "content": "Test content",
                    "language": "en",
                    "entities": [],
                    "word_count": 10
                },
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(ArticleAnalysisDTO, test_case)
    
    def _test_xp_transaction_dto(self):
        """Test XPTransactionDTO model"""
        test_cases = [
            # Valid EARN case
            {
                'name': 'Valid XPTransactionDTO - EARN',
                'data': {
                    "user_id": 456,
                    "transaction_type": "EARN",
                    "amount": 50,
                    "source": "quiz_completion",
                    "description": "Completed quiz",
                    "metadata": {"article_id": 123, "score": 85}
                },
                'should_pass': True
            },
            # Invalid case - wrong amount sign
            {
                'name': 'Invalid XPTransactionDTO - Wrong Amount Sign',
                'data': {
                    "user_id": 456,
                    "transaction_type": "EARN",
                    "amount": -50,  # Should be positive for EARN
                    "source": "test",
                    "description": "test"
                },
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(XPTransactionDTO, test_case)
    
    def _test_content_acquisition_dto(self):
        """Test ContentAcquisitionDTO model"""
        test_cases = [
            # Valid case
            {
                'name': 'Valid ContentAcquisitionDTO',
                'data': {
                    "source_id": "newsapi_tech",
                    "source_type": "api",
                    "url": "https://example.com/article",
                    "title": "Latest Technology Trends",
                    "content": "This article discusses technology trends. " * 10,
                    "language": "en",
                    "tags": ["Technology", "Innovation", "AI"],
                    "priority": "normal"
                },
                'should_pass': True
            }
        ]
        
        for test_case in test_cases:
            self._run_test_case(ContentAcquisitionDTO, test_case)
    
    def _test_validation_pipeline(self):
        """Test validation pipeline functionality"""
        self.stdout.write("🔧 Testing validation pipeline...")
        
        # Test successful validation
        test_data = {
            "article_id": 1,
            "content": "Test content for pipeline validation. " * 10,
            "language": "en",
            "entities": ["Test Entity"],
            "word_count": 50
        }
        
        result = self.pipeline.validate_and_parse(
            ArticleAnalysisDTO,
            test_data,
            context="Pipeline test",
            raise_on_error=False
        )
        
        if result:
            self._record_test_result("Validation Pipeline - Success", True, "Pipeline validation successful")
        else:
            self._record_test_result("Validation Pipeline - Success", False, "Pipeline returned None")
        
        # Test statistics collection
        stats = self.pipeline.get_validation_statistics()
        if stats and 'total_validations' in stats:
            self._record_test_result("Pipeline Statistics", True, f"Statistics: {stats}")
        else:
            self._record_test_result("Pipeline Statistics", False, "Statistics not available")
    
    def _run_performance_tests(self):
        """Run performance benchmarks"""
        self.stdout.write("⚡ Running performance benchmarks...")
        
        import time
        
        # Test validation performance
        test_data = {
            "article_id": 1,
            "content": "Performance test content. " * 50,
            "language": "en",
            "entities": ["Test"],
            "word_count": 100
        }
        
        # Warm up
        for _ in range(10):
            self.pipeline.validate_and_parse(ArticleAnalysisDTO, test_data, raise_on_error=False)
        
        # Benchmark
        iterations = 100
        start_time = time.time()
        
        for _ in range(iterations):
            self.pipeline.validate_and_parse(ArticleAnalysisDTO, test_data, raise_on_error=False)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        self.test_results['performance_metrics'] = {
            'total_time': total_time,
            'average_time_per_validation': avg_time,
            'validations_per_second': iterations / total_time,
            'iterations': iterations
        }
        
        self.stdout.write(
            f"📊 Performance: {avg_time*1000:.2f}ms avg, {iterations/total_time:.1f} validations/sec"
        )
    
    def _run_test_case(self, model_class, test_case):
        """Run a single test case"""
        result = self.pipeline.validate_and_parse(
            model_class,
            test_case['data'],
            context=test_case['name'],
            raise_on_error=False
        )
        
        success = (result is not None) == test_case['should_pass']
        
        if success:
            message = f"Expected {'success' if test_case['should_pass'] else 'failure'}"
        else:
            message = f"Expected {'success' if test_case['should_pass'] else 'failure'}, got {'success' if result else 'failure'}"
        
        self._record_test_result(test_case['name'], success, message)
    
    def _record_test_result(self, test_name: str, success: bool, message: str):
        """Record a test result"""
        self.test_results['total_tests'] += 1
        
        if success:
            self.test_results['passed_tests'] += 1
            if self.verbose:
                self.stdout.write(f"  ✅ {test_name}: {message}")
        else:
            self.test_results['failed_tests'] += 1
            self.stdout.write(f"  ❌ {test_name}: {message}")
        
        self.test_results['test_details'].append({
            'name': test_name,
            'success': success,
            'message': message,
            'timestamp': timezone.now().isoformat()
        })
    
    def _display_results(self):
        """Display test results summary"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 TEST RESULTS SUMMARY")
        self.stdout.write("="*60)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        
        self.stdout.write(f"Total Tests: {total}")
        self.stdout.write(f"Passed: {passed} ({(passed/max(total,1)*100):.1f}%)")
        self.stdout.write(f"Failed: {failed} ({(failed/max(total,1)*100):.1f}%)")
        
        if self.test_results.get('performance_metrics'):
            perf = self.test_results['performance_metrics']
            self.stdout.write("\nPerformance:")
            self.stdout.write(f"  Average time: {perf['average_time_per_validation']*1000:.2f}ms")
            self.stdout.write(f"  Throughput: {perf['validations_per_second']:.1f} validations/sec")
        
        if self.test_results.get('startup_validation'):
            startup = self.test_results['startup_validation']
            self.stdout.write("\nStartup Validation:")
            self.stdout.write(f"  Success: {startup['success']}")
            self.stdout.write(f"  Checks: {startup['summary']['passed']}/{startup['summary']['total_checks']}")
        
        # Pipeline statistics
        stats = self.pipeline.get_validation_statistics()
        if stats:
            self.stdout.write("\nPipeline Statistics:")
            self.stdout.write(f"  Total validations: {stats.get('total_validations', 0)}")
            self.stdout.write(f"  Success rate: {stats.get('success_rate', 0):.1f}%")
    
    def _export_results(self, filename: str):
        """Export test results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            self.stdout.write(f"📄 Results exported to: {filename}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to export results: {str(e)}")
            )