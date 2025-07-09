"""Test utilities for media analyzer tests."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pydub import AudioSegment

from multimodal_analyzer_cli.config import Config
from multimodal_analyzer_cli.utils.video import (
    find_videos,
    get_video_info,
    is_video_file,
    validate_video_file,
)


def require_api_credentials(*models: str):
    """Require API credentials for specified models. Raises error if missing."""
    config = Config.load()
    for model in models:
        try:
            config.validate_api_keys(model)
        except Exception as e:
            pytest.fail(f"Required API credentials missing for {model}: {str(e)}")


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
    if config.openai_api_key or config.AZURE_OPENAI_API_KEY:
        models["image"].append("gpt-4o-mini")
    if config.anthropic_api_key:
        models["image"].append("claude-3-sonnet-20240229")

    # Audio transcription models
    if config.openai_api_key or config.AZURE_OPENAI_API_KEY:
        models["audio_transcription"].append("whisper-1")

    # Text analysis models
    if config.gemini_api_key or config.gemini_api_key:
        models["text_analysis"].append("gemini/gemini-2.5-flash")
    if config.openai_api_key or config.AZURE_OPENAI_API_KEY:
        models["text_analysis"].append("gpt-4o-mini")
    if config.anthropic_api_key:
        models["text_analysis"].append("claude-3-sonnet-20240229")

    return models


def get_primary_image_model() -> str:
    """Get the primary image model for testing."""
    models = get_available_models()["image"]
    if not models:
        pytest.fail(
            "No image analysis models available. Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY environment variable."
        )
    return models[0]


def get_primary_audio_model() -> str:
    """Get the primary audio model for testing."""
    models = get_available_models()["audio_transcription"]
    if not models:
        pytest.fail(
            "No audio transcription models available. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY environment variable."
        )
    return models[0]


def get_primary_text_model() -> str:
    """Get the primary text analysis model for testing."""
    models = get_available_models()["text_analysis"]
    if not models:
        pytest.fail(
            "No text analysis models available. Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY environment variable."
        )
    return models[0]


def get_primary_video_model() -> str:
    """Get the primary video model for testing (Gemini only)."""
    config = Config.load()
    if config.gemini_api_key:
        return "gemini/gemini-2.5-flash"
    pytest.fail(
        "No video analysis models available. Set GEMINI_API_KEY environment variable."
    )


def test_find_videos_recursive_with_real_files():
    """Test find_videos function with recursive search."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create subdirectories
        subdir1 = temp_path / "subdir1"
        subdir2 = temp_path / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()

        # Create test video files
        (temp_path / "video1.mp4").touch()
        (temp_path / "video2.avi").touch()
        (subdir1 / "video3.mov").touch()
        (subdir2 / "video4.mkv").touch()
        (temp_path / "not_video.txt").touch()

        # Test non-recursive search
        videos = list(find_videos(temp_path, recursive=False))
        video_names = [v.name for v in videos]
        assert "video1.mp4" in video_names
        assert "video2.avi" in video_names
        assert "video3.mov" not in video_names  # Should not find in subdirs
        assert "video4.mkv" not in video_names

        # Test recursive search
        videos_recursive = list(find_videos(temp_path, recursive=True))
        video_names_recursive = [v.name for v in videos_recursive]
        assert "video1.mp4" in video_names_recursive
        assert "video2.avi" in video_names_recursive
        assert "video3.mov" in video_names_recursive
        assert "video4.mkv" in video_names_recursive
        assert len(videos_recursive) == 4


def test_validate_video_file_fails_fast():
    """Test video validation with fail-fast behavior."""
    # Test with non-existent file
    non_existent = Path("/non/existent/video.mp4")
    with pytest.raises(FileNotFoundError):
        validate_video_file(non_existent)

    # Test with unsupported format
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"not a video")
        tmp.flush()
        unsupported_file = Path(tmp.name)

        with pytest.raises(ValueError, match="Unsupported video format"):
            validate_video_file(unsupported_file)

        unsupported_file.unlink()


def test_get_video_info_with_real_video():
    """Test get_video_info with a real video file."""
    # This test requires a real video file to work properly
    # For now, we'll test the error handling
    test_video_path = get_test_video_path()

    if not test_video_path.exists():
        # If no test video file exists, test error handling
        with pytest.raises(FileNotFoundError):
            get_video_info(test_video_path)
    else:
        # If test video exists, validate the info structure
        try:
            info = get_video_info(test_video_path)
            assert "path" in info
            assert "format" in info
            assert "duration_seconds" in info
            assert "duration_minutes" in info
            assert "file_size_mb" in info
            assert "width" in info
            assert "height" in info
            assert "fps" in info
            assert "video_codec" in info
            assert "audio_codec" in info
            assert "bitrate" in info
            assert "has_audio" in info
            assert "video_streams" in info
            assert "audio_streams" in info
        except ValueError:
            # If ffmpeg fails, that's expected in test environment
            pytest.skip("ffmpeg not available or video file invalid")


def test_is_video_file_format_detection():
    """Test is_video_file function."""
    # Test supported formats
    assert is_video_file(Path("test.mp4"))
    assert is_video_file(Path("test.avi"))
    assert is_video_file(Path("test.mov"))
    assert is_video_file(Path("test.mkv"))
    assert is_video_file(Path("test.wmv"))
    assert is_video_file(Path("test.flv"))
    assert is_video_file(Path("test.webm"))
    assert is_video_file(Path("test.m4v"))

    # Test case insensitivity
    assert is_video_file(Path("test.MP4"))
    assert is_video_file(Path("test.AVI"))

    # Test unsupported formats
    assert not is_video_file(Path("test.txt"))
    assert not is_video_file(Path("test.jpg"))
    assert not is_video_file(Path("test.mp3"))
    assert not is_video_file(Path("test.pdf"))


class FileManager:
    """Context manager for test files that ensures cleanup."""

    def __init__(self):
        self.temp_files = []

    def create_test_image(self, **kwargs) -> Path:
        """Create test image and track for cleanup."""
        path = create_test_image(**kwargs)
        self.temp_files.append(path)
        return path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for file_path in self.temp_files:
            cleanup_temp_file(file_path)
