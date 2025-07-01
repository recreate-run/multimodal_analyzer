"""Test utilities for media analyzer tests."""

import pytest
from pathlib import Path
import tempfile
import os
from PIL import Image
import numpy as np
from pydub import AudioSegment

from media_analyzer_cli.config import Config


def get_test_data_path() -> Path:
    """Get path to test data directory."""
    return Path(__file__).parent.parent / "data"


def get_test_image_path() -> Path:
    """Get path to test image file."""
    return get_test_data_path() / "speaker.jpg"


def get_test_audio_path() -> Path:
    """Get path to test audio file."""
    return get_test_data_path() / "test_audio.mp3"


def get_test_video_path() -> Path:
    """Get path to test video file."""
    return get_test_data_path() / "test_video.mp4"


def create_test_image(width: int = 100, height: int = 100, color: str = "red") -> Path:
    """Create a temporary test image file."""
    img = Image.new("RGB", (width, height), color=color)
    temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(temp_file.name, format="JPEG")
    return Path(temp_file.name)


def create_test_audio(
    duration: float = 1.0, frequency: int = 440, format: str = "wav"
) -> Path:
    """Create a temporary test audio file with sine wave."""
    sample_rate = 44100

    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * frequency * t)

    # Convert to 16-bit PCM
    audio_data = (wave * 16000).astype(np.int16)  # Lower volume

    # Create AudioSegment
    audio = AudioSegment(
        audio_data.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1
    )

    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False)
    audio.export(temp_file.name, format=format)
    return Path(temp_file.name)


def cleanup_temp_file(file_path: Path):
    """Clean up temporary test file."""
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass  # Ignore cleanup errors


def get_available_models() -> dict:
    """Get available models based on API keys."""
    config = Config.load()
    models = {"image": [], "audio_transcription": [], "text_analysis": []}

    # Image models
    if config.gemini_api_key or config.gemini_api_key:
        models["image"].append("gemini/gemini-2.5-flash")
    if config.openai_api_key or config.azure_openai_key:
        models["image"].append("gpt-4o-mini")
    if config.anthropic_api_key:
        models["image"].append("claude-3-sonnet-20240229")

    # Audio transcription models
    if config.openai_api_key or config.azure_openai_key:
        models["audio_transcription"].append("whisper-1")

    # Text analysis models
    if config.gemini_api_key or config.gemini_api_key:
        models["text_analysis"].append("gemini/gemini-2.5-flash")
    if config.openai_api_key or config.azure_openai_key:
        models["text_analysis"].append("gpt-4o-mini")
    if config.anthropic_api_key:
        models["text_analysis"].append("claude-3-sonnet-20240229")

    return models


def get_primary_image_model() -> str:
    """Get the primary image model for testing."""
    models = get_available_models()["image"]
    if not models:
        pytest.fail("No image analysis models available. Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY environment variable.")
    return models[0]


def get_primary_audio_model() -> str:
    """Get the primary audio model for testing."""
    models = get_available_models()["audio_transcription"]
    if not models:
        pytest.fail("No audio transcription models available. Set OPENAI_API_KEY or AZURE_OPENAI_KEY environment variable.")
    return models[0]


def get_primary_text_model() -> str:
    """Get the primary text analysis model for testing."""
    models = get_available_models()["text_analysis"]
    if not models:
        pytest.fail("No text analysis models available. Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY environment variable.")
    return models[0]


class FileManager:
    """Context manager for test files that ensures cleanup."""

    def __init__(self):
        self.temp_files = []

    def create_test_image(self, **kwargs) -> Path:
        """Create test image and track for cleanup."""
        path = create_test_image(**kwargs)
        self.temp_files.append(path)
        return path

    def create_test_audio(self, **kwargs) -> Path:
        """Create test audio and track for cleanup."""
        path = create_test_audio(**kwargs)
        self.temp_files.append(path)
        return path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for file_path in self.temp_files:
            cleanup_temp_file(file_path)
