"""
Configuration Management

This module provides configuration management for the MusicBrainz MCP server,
including API endpoints, timeouts, rate limits, logging configuration, and
other settings.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json


@dataclass
class APIConfig:
    """Configuration for MusicBrainz API settings."""
    
    base_url: str = "https://musicbrainz.org/ws/2"
    user_agent: str = "MusicBrainzMCP/0.1.0"
    rate_limit: float = 1.0  # Requests per second
    timeout: float = 30.0  # Request timeout in seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # Base delay between retries
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.rate_limit <= 0:
            raise ValueError("Rate limit must be positive")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")


@dataclass
class CacheConfig:
    """Configuration for caching settings."""
    
    enabled: bool = True
    default_ttl: int = 300  # 5 minutes
    max_entries: int = 1000
    cleanup_interval: int = 60  # Cleanup expired entries every 60 seconds
    
    # TTL for different types of data
    search_ttl: int = 300  # 5 minutes
    lookup_ttl: int = 3600  # 1 hour
    browse_ttl: int = 600  # 10 minutes
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.default_ttl < 0:
            raise ValueError("Default TTL must be non-negative")
        if self.max_entries <= 0:
            raise ValueError("Max entries must be positive")


@dataclass
class LoggingConfig:
    """Configuration for logging settings."""
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # File logging
    log_to_file: bool = False
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Console logging
    log_to_console: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}")
        
        if self.log_to_file and not self.log_file:
            raise ValueError("Log file path required when file logging is enabled")


@dataclass
class ServerConfig:
    """Configuration for MCP server settings."""
    
    name: str = "MusicBrainz MCP Server"
    version: str = "0.1.0"
    description: str = "MCP server for querying the MusicBrainz database"
    
    # Transport settings
    transport: str = "stdio"  # stdio, http, sse
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"
    
    # Request limits
    max_search_limit: int = 100
    default_search_limit: int = 25
    max_browse_limit: int = 100
    default_browse_limit: int = 25
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        valid_transports = ["stdio", "http", "sse"]
        if self.transport not in valid_transports:
            raise ValueError(f"Invalid transport: {self.transport}")
        
        if self.port < 1 or self.port > 65535:
            raise ValueError("Port must be between 1 and 65535")


@dataclass
class MusicBrainzMCPConfig:
    """Main configuration class for the MusicBrainz MCP server."""
    
    api: APIConfig = field(default_factory=APIConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    # Additional settings
    debug: bool = False
    environment: str = "production"  # development, testing, production
    
    @classmethod
    def from_env(cls) -> "MusicBrainzMCPConfig":
        """
        Create configuration from environment variables.
        
        Returns:
            Configuration instance with values from environment
        """
        config = cls()
        
        # API configuration
        config.api.base_url = os.getenv("MUSICBRAINZ_BASE_URL", config.api.base_url)
        config.api.user_agent = os.getenv("MUSICBRAINZ_USER_AGENT", config.api.user_agent)
        config.api.rate_limit = float(os.getenv("MUSICBRAINZ_RATE_LIMIT", config.api.rate_limit))
        config.api.timeout = float(os.getenv("MUSICBRAINZ_TIMEOUT", config.api.timeout))
        config.api.max_retries = int(os.getenv("MUSICBRAINZ_MAX_RETRIES", config.api.max_retries))
        
        # Cache configuration
        config.cache.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        config.cache.default_ttl = int(os.getenv("CACHE_DEFAULT_TTL", config.cache.default_ttl))
        config.cache.max_entries = int(os.getenv("CACHE_MAX_ENTRIES", config.cache.max_entries))
        
        # Logging configuration
        config.logging.level = os.getenv("LOG_LEVEL", config.logging.level).upper()
        config.logging.log_to_file = os.getenv("LOG_TO_FILE", "false").lower() == "true"
        config.logging.log_file = os.getenv("LOG_FILE", config.logging.log_file)
        
        # Server configuration
        config.server.name = os.getenv("SERVER_NAME", config.server.name)
        config.server.transport = os.getenv("SERVER_TRANSPORT", config.server.transport)
        config.server.host = os.getenv("SERVER_HOST", config.server.host)
        config.server.port = int(os.getenv("SERVER_PORT", config.server.port))
        
        # General settings
        config.debug = os.getenv("DEBUG", "false").lower() == "true"
        config.environment = os.getenv("ENVIRONMENT", config.environment)
        
        return config
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "MusicBrainzMCPConfig":
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        
        # Create configuration with defaults
        config = cls()
        
        # Update with file data
        if "api" in config_data:
            api_data = config_data["api"]
            for key, value in api_data.items():
                if hasattr(config.api, key):
                    setattr(config.api, key, value)
        
        if "cache" in config_data:
            cache_data = config_data["cache"]
            for key, value in cache_data.items():
                if hasattr(config.cache, key):
                    setattr(config.cache, key, value)
        
        if "logging" in config_data:
            logging_data = config_data["logging"]
            for key, value in logging_data.items():
                if hasattr(config.logging, key):
                    setattr(config.logging, key, value)
        
        if "server" in config_data:
            server_data = config_data["server"]
            for key, value in server_data.items():
                if hasattr(config.server, key):
                    setattr(config.server, key, value)
        
        # Update general settings
        config.debug = config_data.get("debug", config.debug)
        config.environment = config_data.get("environment", config.environment)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            "api": {
                "base_url": self.api.base_url,
                "user_agent": self.api.user_agent,
                "rate_limit": self.api.rate_limit,
                "timeout": self.api.timeout,
                "max_retries": self.api.max_retries,
                "retry_delay": self.api.retry_delay,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "default_ttl": self.cache.default_ttl,
                "max_entries": self.cache.max_entries,
                "cleanup_interval": self.cache.cleanup_interval,
                "search_ttl": self.cache.search_ttl,
                "lookup_ttl": self.cache.lookup_ttl,
                "browse_ttl": self.cache.browse_ttl,
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "date_format": self.logging.date_format,
                "log_to_file": self.logging.log_to_file,
                "log_file": self.logging.log_file,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count,
                "log_to_console": self.logging.log_to_console,
            },
            "server": {
                "name": self.server.name,
                "version": self.server.version,
                "description": self.server.description,
                "transport": self.server.transport,
                "host": self.server.host,
                "port": self.server.port,
                "path": self.server.path,
                "max_search_limit": self.server.max_search_limit,
                "default_search_limit": self.server.default_search_limit,
                "max_browse_limit": self.server.max_browse_limit,
                "default_browse_limit": self.server.default_browse_limit,
            },
            "debug": self.debug,
            "environment": self.environment,
        }
    
    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            config_path: Path to save configuration file
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def setup_logging(self) -> None:
        """Configure logging based on the logging configuration."""
        # Create logger
        logger = logging.getLogger("musicbrainz_mcp")
        logger.setLevel(getattr(logging, self.logging.level))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            self.logging.format,
            datefmt=self.logging.date_format
        )
        
        # Console handler
        if self.logging.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if self.logging.log_to_file and self.logging.log_file:
            from logging.handlers import RotatingFileHandler
            
            log_path = Path(self.logging.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                self.logging.log_file,
                maxBytes=self.logging.max_file_size,
                backupCount=self.logging.backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)


# Global configuration instance
_global_config: Optional[MusicBrainzMCPConfig] = None


def get_config() -> MusicBrainzMCPConfig:
    """
    Get the global configuration instance.
    
    Returns:
        Global configuration instance
    """
    global _global_config
    if _global_config is None:
        _global_config = MusicBrainzMCPConfig.from_env()
    return _global_config


def set_config(config: MusicBrainzMCPConfig) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config: Configuration instance to set as global
    """
    global _global_config
    _global_config = config


def load_config_from_file(config_path: Union[str, Path]) -> MusicBrainzMCPConfig:
    """
    Load configuration from file and set as global.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded configuration instance
    """
    config = MusicBrainzMCPConfig.from_file(config_path)
    set_config(config)
    return config
