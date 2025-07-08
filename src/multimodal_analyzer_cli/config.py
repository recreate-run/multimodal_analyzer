import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration management for Media Analyzer CLI."""

    # API Keys (loaded from environment)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    azure_openai_key: str | None = None
    azure_openai_endpoint: str | None = None

    # Default settings
    default_model: str = "gemini/gemini-2.5-flash"
    default_word_count: int = 100
    default_prompt: str = "Describe this image in detail."
    max_concurrency: int = 20
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
    max_video_size_mb: int = 2048  # 2GB default for Gemini 2.0
    
    # Video specific settings
    supported_video_formats: list = field(
        default_factory=lambda: [
            ".mp4",
            ".avi", 
            ".mov",
            ".mkv",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v"
        ]
    )

    @classmethod
    def load(cls, config_file: Path | None = None) -> "Config":
        """Load configuration from environment and optional YAML file."""

        # Load environment variables
        load_dotenv()

        # Start with default config
        config_data = {}

        # Load from YAML file if provided
        if config_file and config_file.exists():
            with open(config_file) as f:
                config_data = yaml.safe_load(f) or {}

        # Override with environment variables
        env_mapping = {
            "OPENAI_API_KEY": "openai_api_key",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "GEMINI_API_KEY": "gemini_api_key",
            "AZURE_OPENAI_KEY": "azure_openai_key",
            "AZURE_OPENAI_ENDPOINT": "azure_openai_endpoint",
            "DEFAULT_MODEL": "default_model",
            "DEFAULT_WORD_COUNT": "default_word_count",
            "DEFAULT_PROMPT": "default_prompt",
            "MAX_CONCURRENCY": "max_concurrency",
            "MAX_FILE_SIZE_MB": "max_file_size_mb",
            "MAX_AUDIO_SIZE_MB": "max_audio_size_mb",
            "MAX_VIDEO_SIZE_MB": "max_video_size_mb",
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
                    "max_video_size_mb",
                    "retry_attempts",
                    "timeout_seconds",
                ]:
                    value = int(value)
                config_data[config_key] = value

        return cls(**config_data)

    def get_api_key(self, model: str) -> str | None:
        """Get appropriate API key for the given model."""
        if model.startswith("azure/"):
            return self.azure_openai_key
        if (
            model.startswith("gpt-")
            or model.startswith("openai/")
            or model.startswith("whisper")
        ):
            return self.openai_api_key
        elif model.startswith("claude-") or model.startswith("anthropic/"):
            return self.anthropic_api_key
        elif model.startswith("gemini") or model.startswith("google/"):
            return self.gemini_api_key
        return None

    def validate_api_keys(self, model: str) -> None:
        """Validate that required API key is present for the given model."""
        if model.startswith("azure/"):
            if not self.azure_openai_key or self.azure_openai_key.strip() == "":
                raise ValueError("AZURE_OPENAI_KEY environment variable is required for Azure models")
            if not self.azure_openai_endpoint or self.azure_openai_endpoint.strip() == "":
                raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required for Azure models")
            return

        api_key = self.get_api_key(model)
        if not api_key or api_key.strip() == "":
            if model.startswith(("gpt-", "openai/", "whisper")):
                raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI models")
            elif model.startswith(("claude-", "anthropic/")):
                raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic models")
            elif model.startswith(("gemini", "google/")):
                raise ValueError("GEMINI_API_KEY environment variable is required for Google models")
            else:
                raise ValueError(f"No API key available for model: {model}")

    def validate(self) -> None:
        """Validate configuration settings."""
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        if self.default_word_count < 1:
            raise ValueError("default_word_count must be at least 1")
        if self.max_file_size_mb < 1:
            raise ValueError("max_file_size_mb must be at least 1")
        if self.max_video_size_mb < 1:
            raise ValueError("max_video_size_mb must be at least 1")
