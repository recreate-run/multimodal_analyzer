import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .auth import GoogleAuthProvider


@dataclass
class Config:
    """Configuration management for Media Analyzer CLI."""

    # API Keys (loaded from environment)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    azure_openai_endpoint: str | None = None

    # Google authentication provider
    google_auth_provider: GoogleAuthProvider | None = field(default=None, init=False)

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

        # Load environment variables (only for .env file support)
        load_dotenv()

        # Start with default config
        config_data = {}

        # Load from YAML file if provided
        if config_file and config_file.exists():
            with open(config_file) as f:
                config_data = yaml.safe_load(f) or {}

        # Load only essential API keys from environment
        config_data.update({
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
            "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        })

        # Create config instance
        config = cls(**config_data)
        
        # Initialize Google Auth Provider after config creation
        config.google_auth_provider = GoogleAuthProvider.from_environment()
        
        return config

    def get_api_key(self, model: str) -> str | None:
        """Get appropriate API key or OAuth token for the given model."""
        if model.startswith("azure/"):
            return self.AZURE_OPENAI_API_KEY
        if (
            model.startswith("gpt-")
            or model.startswith("openai/")
            or model.startswith("whisper")
        ):
            return self.openai_api_key
        elif model.startswith("claude-") or model.startswith("anthropic/"):
            return self.anthropic_api_key
        elif model.startswith("gemini") or model.startswith("google/"):
            # Use OAuth token if available, otherwise fall back to API key
            if self.google_auth_provider:
                auth_token = self.google_auth_provider.get_auth_token()
                if auth_token:
                    return auth_token
            return self.gemini_api_key
        return None

    def validate_api_keys(self, model: str) -> None:
        """Validate that required authentication is available for the given model."""
        if model.startswith("azure/"):
            if not self.AZURE_OPENAI_API_KEY or self.AZURE_OPENAI_API_KEY.strip() == "":
                raise ValueError("AZURE_OPENAI_API_KEY environment variable is required for Azure models")
            if not self.azure_openai_endpoint or self.azure_openai_endpoint.strip() == "":
                raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required for Azure models")
            return

        # Special handling for Google/Gemini models with OAuth support
        if model.startswith(("gemini", "google/")):
            if self.google_auth_provider:
                self.google_auth_provider.validate_for_model(model)
            else:
                # Fallback to API key validation
                if not self.gemini_api_key or self.gemini_api_key.strip() == "":
                    raise ValueError("GEMINI_API_KEY environment variable is required for Google models")
            return

        # Standard API key validation for other providers
        api_key = self.get_api_key(model)
        if not api_key or api_key.strip() == "":
            if model.startswith(("gpt-", "openai/", "whisper")):
                raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI models")
            elif model.startswith(("claude-", "anthropic/")):
                raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic models")
            else:
                raise ValueError(f"No API key available for model: {model}")

    @property
    def google_oauth_enabled(self) -> bool:
        """Check if Google OAuth authentication is currently enabled/active."""
        if not self.google_auth_provider:
            return False
        
        auth_status = self.google_auth_provider.get_auth_status()
        return auth_status.get("oauth_authenticated", False)

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
