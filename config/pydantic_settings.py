"""
Pydantic Settings for environment-based configuration management.

This module provides type-safe configuration management using Pydantic Settings,
ensuring all environment variables are properly validated and typed.
"""

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Dict, Any


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="DB_", case_sensitive=False)
    
    name: str = "verifast_db"
    user: str = "verifast_user"
    password: str = ""
    host: str = "localhost"
    port: int = 5432
    engine: str = "django.db.backends.postgresql"
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Validate database port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError('Database port must be between 1 and 65535')
        return v
    
    @field_validator('engine')
    @classmethod
    def validate_engine(cls, v):
        """Validate database engine is supported."""
        supported_engines = [
            'django.db.backends.postgresql',
            'django.db.backends.sqlite3',
            'django.db.backends.mysql'
        ]
        if v not in supported_engines:
            raise ValueError(f'Unsupported database engine: {v}')
        return v
    
    def get_database_url(self) -> str:
        """Generate database URL for Django."""
        if self.engine == 'django.db.backends.sqlite3':
            return f"sqlite:///{self.name}"
        elif self.engine == 'django.db.backends.postgresql':
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        elif self.engine == 'django.db.backends.mysql':
            return f"mysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return ""


class GeminiConfig(BaseSettings):
    """Google Gemini API configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="GEMINI_", case_sensitive=False)
    
    api_key: str = ""
    model_name: str = "gemini-pro"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30
    retry_attempts: int = 3
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key format."""
        if not v or len(v) < 10:
            raise ValueError('Gemini API key must be at least 10 characters')
        return v
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v
    
    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v):
        """Validate max tokens is reasonable."""
        if not 100 <= v <= 8192:
            raise ValueError('Max tokens must be between 100 and 8192')
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout is reasonable."""
        if not 5 <= v <= 300:
            raise ValueError('Timeout must be between 5 and 300 seconds')
        return v


class CeleryConfig(BaseSettings):
    """Celery configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="CELERY_", case_sensitive=False)
    
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = ["json"]
    timezone: str = "UTC"
    enable_utc: bool = True
    task_always_eager: bool = False
    
    @field_validator('broker_url', 'result_backend')
    @classmethod
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError('Redis URL must start with redis:// or rediss://')
        return v
    
    @field_validator('task_serializer', 'result_serializer')
    @classmethod
    def validate_serializer(cls, v):
        """Validate serializer is supported."""
        supported = ['json', 'pickle', 'yaml', 'msgpack']
        if v not in supported:
            raise ValueError(f'Unsupported serializer: {v}. Use one of: {supported}')
        return v


class XPSystemConfig(BaseSettings):
    """XP System configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="XP_", case_sensitive=False)
    
    base_quiz_xp: int = 50
    perfect_score_bonus: int = 25
    speed_bonus_threshold: int = 300
    speed_bonus_multiplier: float = 1.2
    comment_cost: int = 10
    reply_cost: int = 5
    interaction_bronze_cost: int = 5
    interaction_silver_cost: int = 10
    interaction_gold_cost: int = 20
    author_share_percentage: float = 0.5
    
    # Premium feature costs
    word_chunking_2_cost: int = 100
    word_chunking_3_cost: int = 150
    word_chunking_4_cost: int = 200
    word_chunking_5_cost: int = 250
    smart_connectors_cost: int = 300
    premium_fonts_cost: int = 200
    
    @field_validator('base_quiz_xp', 'perfect_score_bonus', 'comment_cost', 'reply_cost')
    @classmethod
    def validate_positive_integers(cls, v):
        """Validate XP values are positive."""
        if v <= 0:
            raise ValueError('XP values must be positive integers')
        return v
    
    @field_validator('speed_bonus_multiplier', 'author_share_percentage')
    @classmethod
    def validate_multipliers(cls, v):
        """Validate multipliers are reasonable."""
        if not 0.1 <= v <= 10.0:
            raise ValueError('Multipliers must be between 0.1 and 10.0')
        return v
    
    @field_validator('author_share_percentage')
    @classmethod
    def validate_percentage(cls, v):
        """Validate percentage is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Percentage must be between 0.0 and 1.0')
        return v


class RedisConfig(BaseSettings):
    """Redis configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="REDIS_", case_sensitive=False)
    
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 5
    connection_pool_max_connections: int = 50
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Validate Redis port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError('Redis port must be between 1 and 65535')
        return v
    
    @field_validator('db')
    @classmethod
    def validate_db(cls, v):
        """Validate Redis database number."""
        if not 0 <= v <= 15:
            raise ValueError('Redis database must be between 0 and 15')
        return v
    
    def get_redis_url(self) -> str:
        """Generate Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class SecurityConfig(BaseSettings):
    """Security configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)
    
    secret_key: str = "django-insecure-default-key-for-development-only"
    debug: bool = False
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_allowed_origins: List[str] = []
    csrf_trusted_origins: List[str] = []
    secure_ssl_redirect: bool = False
    session_cookie_secure: bool = False
    csrf_cookie_secure: bool = False
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        """Validate secret key is strong enough."""
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v
    
    @model_validator(mode='after')
    def validate_production_security(self):
        """Validate security settings for production."""
        # Only enforce strict security in production (when debug=False and not using default secret key)
        is_production = not self.debug and not self.secret_key.startswith('django-insecure-')
        
        if is_production:
            if not self.secure_ssl_redirect:
                raise ValueError('SSL redirect must be enabled in production')
            if not self.session_cookie_secure:
                raise ValueError('Secure session cookies must be enabled in production')
        return self


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="LOG_", case_sensitive=False)
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    
    @field_validator('level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is supported."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @field_validator('max_file_size')
    @classmethod
    def validate_file_size(cls, v):
        """Validate max file size is reasonable."""
        if not 1024 <= v <= 104857600:  # 1KB to 100MB
            raise ValueError('Max file size must be between 1KB and 100MB')
        return v


class VeriFastSettings(BaseSettings):
    """Main VeriFast application settings."""
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False, extra='ignore')
    
    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    gemini: GeminiConfig = GeminiConfig()
    celery: CeleryConfig = CeleryConfig()
    xp_system: XPSystemConfig = XPSystemConfig()
    redis: RedisConfig = RedisConfig()
    security: SecurityConfig = SecurityConfig()
    logging: LoggingConfig = LoggingConfig()
    
    # Application-specific settings
    app_name: str = "VeriFast"
    app_version: str = "1.0.0"
    environment: str = "development"
    base_url: str = "http://localhost:8000"
    
    # Feature flags
    enable_content_acquisition: bool = True
    enable_quiz_generation: bool = True
    enable_xp_system: bool = True
    enable_premium_features: bool = True
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment is supported."""
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v.rstrip('/')  # Remove trailing slash
    
    @model_validator(mode='after')
    def validate_configuration_consistency(self):
        """Validate configuration consistency across components."""
        # Production environment validations
        if self.environment == 'production':
            if self.security.debug:
                raise ValueError('Debug mode must be disabled in production')
            
            if not self.base_url.startswith('https://'):
                raise ValueError('HTTPS must be used in production')
        
        return self
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == 'development'
    
    def get_django_settings_dict(self) -> Dict[str, Any]:
        """Generate Django settings dictionary."""
        return {
            'SECRET_KEY': self.security.secret_key,
            'DEBUG': self.security.debug,
            'ALLOWED_HOSTS': self.security.allowed_hosts,
            'DATABASES': {
                'default': {
                    'ENGINE': self.database.engine,
                    'NAME': self.database.name,
                    'USER': self.database.user,
                    'PASSWORD': self.database.password,
                    'HOST': self.database.host,
                    'PORT': self.database.port,
                }
            },
            'CACHES': {
                'default': {
                    'BACKEND': 'django_redis.cache.RedisCache',
                    'LOCATION': self.redis.get_redis_url(),
                    'OPTIONS': {
                        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    }
                }
            },
            'CELERY_BROKER_URL': self.celery.broker_url,
            'CELERY_RESULT_BACKEND': self.celery.result_backend,
        }

# Global settings instance
settings = VeriFastSettings()