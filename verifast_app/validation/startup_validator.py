"""
Startup Configuration Validator
Validates all Pydantic configurations and settings on Django startup
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class StartupValidator:
    """Validates all Pydantic configurations on application startup"""

    def __init__(self):
        self.validation_results = {
            "timestamp": datetime.now(),
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "warnings": 0,
            "errors": [],
            "warnings_list": [],
            "success": True,
        }

    def validate_all_configurations(self) -> Dict[str, Any]:
        """Run all configuration validations"""
        logger.info("🔍 Starting Pydantic configuration validation...")

        # Run all validation checks
        self._validate_pydantic_settings()
        self._validate_model_imports()
        self._validate_validation_pipeline()
        self._validate_environment_variables()
        self._validate_model_schemas()
        self._validate_database_connection()

        # Calculate final results
        self.validation_results["success"] = len(self.validation_results["errors"]) == 0

        # Create summary
        self.validation_results["summary"] = {
            "total_checks": self.validation_results["total_checks"],
            "passed": self.validation_results["passed_checks"],
            "failed": self.validation_results["failed_checks"],
            "warnings": self.validation_results["warnings"],
            "success_rate": (
                self.validation_results["passed_checks"]
                / max(self.validation_results["total_checks"], 1)
            )
            * 100,
        }

        if self.validation_results["success"]:
            logger.info(
                f"✅ Configuration validation completed successfully: "
                f"{self.validation_results['passed_checks']}/{self.validation_results['total_checks']} checks passed"
            )
        else:
            logger.error(
                f"❌ Configuration validation failed: "
                f"{len(self.validation_results['errors'])} errors, "
                f"{self.validation_results['warnings']} warnings"
            )

        return self.validation_results

    def _add_check(
        self,
        name: str,
        success: bool,
        error_msg: Optional[str] = None,
        warning_msg: Optional[str] = None,
    ):
        """Add a validation check result"""
        self.validation_results["total_checks"] += 1

        if success:
            self.validation_results["passed_checks"] += 1
            logger.debug(f"✅ {name}: PASSED")
        else:
            self.validation_results["failed_checks"] += 1
            if error_msg:
                self.validation_results["errors"].append(f"{name}: {error_msg}")
                logger.error(f"❌ {name}: {error_msg}")

        if warning_msg:
            self.validation_results["warnings"] += 1
            self.validation_results["warnings_list"].append(f"{name}: {warning_msg}")
            logger.warning(f"⚠️ {name}: {warning_msg}")

    def _validate_pydantic_settings(self):
        """Validate Pydantic settings configuration"""
        try:
            from config.pydantic_settings import settings

            # Test settings instantiation
            self._add_check("Pydantic Settings Import", True)

            # Validate critical settings
            critical_settings = [
                ("gemini.api_key", "Gemini API Key"),
                ("database.name", "Database Name"),
                ("security.secret_key", "Django Secret Key"),
                ("redis.host", "Redis Host"),
                ("celery.broker_url", "Celery Broker URL"),
            ]

            for setting_path, description in critical_settings:
                try:
                    value = settings
                    for part in setting_path.split("."):
                        value = getattr(value, part)

                    if value:
                        self._add_check(f"Setting: {description}", True)
                    else:
                        self._add_check(
                            f"Setting: {description}",
                            False,
                            warning_msg=f"Empty value for {setting_path}",
                        )

                except AttributeError:
                    self._add_check(
                        f"Setting: {description}",
                        False,
                        error_msg=f"Missing setting: {setting_path}",
                    )

            # Test settings validation
            try:
                # Test environment detection
                is_production = settings.is_production()
                settings.is_development()

                self._add_check("Environment Detection", True)

                if is_production:
                    # Additional production checks
                    if settings.security.debug:
                        self._add_check(
                            "Production Security",
                            False,
                            error_msg="Debug mode enabled in production",
                        )
                    else:
                        self._add_check("Production Security", True)

            except Exception as e:
                self._add_check(
                    "Settings Validation",
                    False,
                    error_msg=f"Settings validation failed: {str(e)}",
                )

        except ImportError as e:
            self._add_check(
                "Pydantic Settings Import",
                False,
                error_msg=f"Could not import Pydantic settings: {str(e)}",
            )
        except Exception as e:
            self._add_check(
                "Pydantic Settings Validation",
                False,
                error_msg=f"Settings validation error: {str(e)}",
            )

    def _validate_model_imports(self):
        """Validate all Pydantic model imports"""
        model_imports = [
            (
                "pydantic_models.llm",
                ["MasterAnalysisResponse", "QuizQuestion", "LLMGenerationRequest"],
            ),
            (
                "pydantic_models.api",
                ["ArticleSubmissionRequest", "QuizSubmissionRequest", "SearchRequest"],
            ),
            (
                "pydantic_models.dto",
                ["ArticleAnalysisDTO", "XPTransactionDTO", "ContentAcquisitionDTO"],
            ),
        ]

        for module_path, model_names in model_imports:
            try:
                module = __import__(f"verifast_app.{module_path}", fromlist=model_names)

                for model_name in model_names:
                    try:
                        model_class = getattr(module, model_name)
                        self._add_check(f"Model Import: {model_name}", True)

                        # Test model schema generation
                        try:
                            schema = model_class.model_json_schema()
                            if schema and "properties" in schema:
                                self._add_check(f"Model Schema: {model_name}", True)
                            else:
                                self._add_check(
                                    f"Model Schema: {model_name}",
                                    False,
                                    warning_msg="Schema missing properties",
                                )
                        except Exception as e:
                            self._add_check(
                                f"Model Schema: {model_name}",
                                False,
                                error_msg=f"Schema generation failed: {str(e)}",
                            )

                    except AttributeError:
                        self._add_check(
                            f"Model Import: {model_name}",
                            False,
                            error_msg=f"Model {model_name} not found in {module_path}",
                        )

            except ImportError as e:
                self._add_check(
                    f"Module Import: {module_path}",
                    False,
                    error_msg=f"Could not import {module_path}: {str(e)}",
                )

    def _validate_validation_pipeline(self):
        """Validate the validation pipeline functionality"""
        try:
            from .pipeline import ValidationPipeline
            from ..pydantic_models.dto import ArticleAnalysisDTO

            # Test pipeline initialization
            pipeline = ValidationPipeline(logger_name="startup_validator")
            self._add_check("Validation Pipeline Init", True)

            # Test basic validation
            test_data = {
                "article_id": 1,
                "content": "Test content for startup validation. " * 10,
                "language": "en",
                "entities": ["Test Entity"],
                "word_count": 50,
            }

            result = pipeline.validate_and_parse(
                ArticleAnalysisDTO,
                test_data,
                context="Startup validation test",
                raise_on_error=False,
            )

            if result:
                self._add_check("Validation Pipeline Test", True)
            else:
                self._add_check(
                    "Validation Pipeline Test",
                    False,
                    warning_msg="Pipeline validation test returned None",
                )

            # Test statistics collection
            stats = pipeline.get_validation_statistics()
            if stats and "total_validations" in stats:
                self._add_check("Pipeline Statistics", True)
            else:
                self._add_check(
                    "Pipeline Statistics",
                    False,
                    warning_msg="Statistics collection not working",
                )

        except ImportError as e:
            self._add_check(
                "Validation Pipeline Import",
                False,
                error_msg=f"Could not import validation pipeline: {str(e)}",
            )
        except Exception as e:
            self._add_check(
                "Validation Pipeline Test",
                False,
                error_msg=f"Pipeline test failed: {str(e)}",
            )

    def _validate_environment_variables(self):
        """Validate required environment variables"""
        required_env_vars = [
            ("GEMINI_API_KEY", "Gemini API Key"),
            ("SECRET_KEY", "Django Secret Key"),
            ("DB_NAME", "Database Name"),
        ]

        optional_env_vars = [
            ("REDIS_HOST", "Redis Host"),
            ("CELERY_BROKER_URL", "Celery Broker URL"),
            ("DEBUG", "Debug Mode"),
        ]

        # Check required variables
        for var_name, description in required_env_vars:
            value = os.getenv(var_name)
            if value:
                self._add_check(f"Env Var: {description}", True)
            else:
                self._add_check(
                    f"Env Var: {description}",
                    False,
                    error_msg=f"Required environment variable {var_name} not set",
                )

        # Check optional variables
        for var_name, description in optional_env_vars:
            value = os.getenv(var_name)
            if value:
                self._add_check(f"Optional Env Var: {description}", True)
            else:
                self._add_check(
                    f"Optional Env Var: {description}",
                    True,
                    warning_msg=f"Optional environment variable {var_name} not set",
                )

    def _validate_model_schemas(self):
        """Validate Pydantic model schemas for consistency"""
        try:
            from ..pydantic_models.llm import MasterAnalysisResponse
            from ..pydantic_models.api import ArticleSubmissionRequest
            from ..pydantic_models.dto import ArticleAnalysisDTO

            test_models = [
                (
                    MasterAnalysisResponse,
                    {
                        "quiz": [
                            {
                                "question": "Test question?",
                                "options": ["A", "B", "C", "D"],
                                "answer": "A",
                                "explanation": "Test explanation",
                            }
                        ]
                        * 5,
                        "tags": ["Test"],
                    },
                ),
                (ArticleSubmissionRequest, {"url": "https://example.com/test"}),
                (
                    ArticleAnalysisDTO,
                    {
                        "article_id": 1,
                        "content": "Test content. " * 20,
                        "language": "en",
                        "entities": ["Test"],
                        "word_count": 40,
                    },
                ),
            ]

            for model_class, test_data in test_models:
                try:
                    # Test model instantiation
                    instance = model_class(**test_data)
                    self._add_check(f"Model Schema: {model_class.__name__}", True)

                    # Test serialization
                    json_data = instance.model_dump()
                    if json_data:
                        self._add_check(
                            f"Model Serialization: {model_class.__name__}", True
                        )
                    else:
                        self._add_check(
                            f"Model Serialization: {model_class.__name__}",
                            False,
                            warning_msg="Serialization returned empty data",
                        )

                except Exception as e:
                    self._add_check(
                        f"Model Schema: {model_class.__name__}",
                        False,
                        error_msg=f"Schema validation failed: {str(e)}",
                    )

        except ImportError as e:
            self._add_check(
                "Model Schema Validation",
                False,
                error_msg=f"Could not import models for schema validation: {str(e)}",
            )

    def _validate_database_connection(self):
        """Validate database connection and Pydantic integration"""
        try:
            from django.db import connection

            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            if result:
                self._add_check("Database Connection", True)
            else:
                self._add_check(
                    "Database Connection",
                    False,
                    error_msg="Database query returned no result",
                )

            # Test Django model integration with Pydantic
            try:
                from django.contrib.auth import get_user_model

                User = get_user_model()

                # Check if we can query users (table exists)
                User.objects.count()
                self._add_check("Django Model Integration", True)

            except Exception as e:
                self._add_check(
                    "Django Model Integration",
                    False,
                    warning_msg=f"Could not query Django models: {str(e)}",
                )

        except Exception as e:
            self._add_check(
                "Database Connection",
                False,
                error_msg=f"Database connection failed: {str(e)}",
            )
