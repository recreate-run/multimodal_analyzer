import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration management for Media Analyzer CLI."""

    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None

    # Default settings
    default_model: str = "gemini/gemini-2.5-flash"
    default_word_count: int = 100
    default_prompt: str = "Describe this image in detail."
    max_concurrency: int = 5
    max_file_size_mb: int = 10

    # Supported formats
    supported_image_formats: list = field(
        default_factory=lambda: [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".webp",
        ]
    )

    # Advanced settings
    retry_attempts: int = 3
    timeout_seconds: int = 30
    max_audio_size_mb: int = 100

    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> "Config":
        """Load configuration from environment and optional YAML file."""

        # Load environment variables
        load_dotenv()

        # Start with default config
        config_data = {}

        # Load from YAML file if provided
        if config_file and config_file.exists():
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f) or {}

        # Override with environment variables
        env_mapping = {
            "OPENAI_API_KEY": "openai_api_key",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "GOOGLE_API_KEY": "google_api_key",
            "GEMINI_API_KEY": "gemini_api_key",
            "AZURE_OPENAI_KEY": "azure_openai_key",
            "AZURE_OPENAI_ENDPOINT": "azure_openai_endpoint",
            "DEFAULT_MODEL": "default_model",
            "DEFAULT_WORD_COUNT": "default_word_count",
            "DEFAULT_PROMPT": "default_prompt",
            "MAX_CONCURRENCY": "max_concurrency",
            "MAX_FILE_SIZE_MB": "max_file_size_mb",
            "MAX_AUDIO_SIZE_MB": "max_audio_size_mb",
            "RETRY_ATTEMPTS": "retry_attempts",
            "TIMEOUT_SECONDS": "timeout_seconds",
        }

        for env_var, config_key in env_mapping.items():
            if os.getenv(env_var):
                value = os.getenv(env_var)
                # Convert numeric values
                if config_key in [
                    "default_word_count",
                    "max_concurrency",
                    "max_file_size_mb",
                    "max_audio_size_mb",
                    "retry_attempts",
                    "timeout_seconds",
                ]:
                    value = int(value)
                config_data[config_key] = value

        return cls(**config_data)

    def get_api_key(self, model: str) -> Optional[str]:
        """Get appropriate API key for the given model."""
        if (
            model.startswith("gpt-")
            or model.startswith("openai/")
            or model.startswith("whisper")
        ):
            # Prioritize Azure OpenAI, then regular OpenAI
            return self.azure_openai_key or self.openai_api_key
        elif model.startswith("claude-") or model.startswith("anthropic/"):
            return self.anthropic_api_key
        elif model.startswith("gemini") or model.startswith("google/"):
            return self.gemini_api_key or self.google_api_key
        return None

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        if self.default_word_count < 1:
            raise ValueError("default_word_count must be at least 1")
        if self.max_file_size_mb < 1:
            raise ValueError("max_file_size_mb must be at least 1")
