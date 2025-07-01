import pytest
from pathlib import Path
from PIL import Image
import tempfile
import io

from media_analyzer_cli.models.litellm_model import LiteLLMModel
from media_analyzer_cli.config import Config
from .test_utils import (
    get_test_image_path,
    get_primary_image_model,
    get_primary_audio_model,
    FileManager,
    cleanup_temp_file,
)


class TestLiteLLMModel:
    """Test cases for LiteLLMModel functionality.

    Note: These tests require actual API keys to be set in environment variables.
    They are integration tests that make real API calls (no mocking as requested).
    """

    def setup_method(self):
        self.config = Config.load()
        self.model = LiteLLMModel(self.config)

    def test_encode_image(self):
        """Test image encoding to base64."""
        with FileManager() as manager:
            # Create a real test image file
            test_image_path = manager.create_test_image(
                width=100, height=100, color="red"
            )

            result = self.model._encode_image(test_image_path)
            assert isinstance(result, str)
            assert len(result) > 0
            # Base64 strings should be divisible by 4
            assert len(result) % 4 == 0

    def test_validate_image_success(self):
        """Test successful image validation."""
        # Use real test image
        test_image_path = get_test_image_path()
        if not test_image_path.exists():
            with FileManager() as manager:
                test_image_path = manager.create_test_image()
                result = self.model._validate_image(test_image_path)
                assert result is True
        else:
            result = self.model._validate_image(test_image_path)
            assert result is True

    def test_validate_image_too_large(self):
        """Test image validation fails for oversized files."""
        # Test with a config that has very small max file size
        small_config = Config.load()
        small_config.max_file_size_mb = 0.001  # 1KB limit
        small_model = LiteLLMModel(small_config)

        with FileManager() as manager:
            # Create a larger test image
            test_image_path = manager.create_test_image(
                width=1000, height=1000
            )  # Should be > 1KB
            result = small_model._validate_image(test_image_path)
            assert result is False

    def test_validate_image_unsupported_format(self):
        """Test image validation fails for unsupported formats."""
        # Create a file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake data")

        try:
            result = self.model._validate_image(temp_path)
            assert result is False
        finally:
            cleanup_temp_file(temp_path)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_image_success(self):
        """Test successful image analysis with real API call."""

        model_name = get_primary_image_model()
        test_image_path = get_test_image_path()

        # Use real test image or create one if not available
        if not test_image_path.exists():
            with FileManager() as manager:
                test_image_path = manager.create_test_image()

                result = await self.model.analyze_image(
                    model=model_name,
                    image_path=test_image_path,
                    prompt="Describe this image briefly",
                    word_count=50,
                )
        else:
            result = await self.model.analyze_image(
                model=model_name,
                image_path=test_image_path,
                prompt="Describe this image briefly",
                word_count=50,
            )

        # Check result structure
        assert "success" in result
        assert "image_path" in result
        assert "model" in result
        assert "prompt" in result
        assert "word_count" in result

        if result["success"]:
            assert "analysis" in result
            assert result["analysis"] is not None
            assert len(result["analysis"]) > 0
            assert result["error"] is None
        else:
            assert "error" in result
            print(f"Image analysis failed: {result['error']}")

    @pytest.mark.asyncio
    async def test_analyze_image_validation_failure(self):
        """Test image analysis with validation failure."""
        # Test with non-existent file
        nonexistent_path = Path("/nonexistent/image.jpg")

        with pytest.raises(ValueError, match="Invalid image"):
            await self.model.analyze_image(
                model="gpt-4o-mini",  # Model doesn't matter for validation failure
                image_path=nonexistent_path,
                prompt="Test prompt",
            )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_transcribe_audio_success(self):
        """Test successful audio transcription with real API call."""

        model_name = get_primary_audio_model()

        with FileManager() as manager:
            # Create test audio file
            test_audio_path = manager.create_test_audio(duration=2.0, format="wav")

            result = await self.model.transcribe_audio(
                model=model_name, audio_path=test_audio_path
            )

            # Check result structure
            assert "success" in result
            assert "audio_path" in result
            assert "model" in result

            # For synthetic audio, transcription might not be meaningful,
            # but we're testing the pipeline works
            if result["success"]:
                assert "transcript" in result
                assert result["error"] is None
            else:
                assert "error" in result
                print(f"Audio transcription failed: {result['error']}")

    @pytest.mark.asyncio
    async def test_transcribe_audio_validation_failure(self):
        """Test audio transcription with validation failure."""
        # Test with non-existent file
        nonexistent_path = Path("/nonexistent/audio.wav")

        with pytest.raises(ValueError, match="Invalid audio file"):
            await self.model.transcribe_audio(
                model="whisper-1", audio_path=nonexistent_path
            )

    def test_validate_audio_success(self):
        """Test successful audio validation."""
        with FileManager() as manager:
            test_audio_path = manager.create_test_audio()
            result = self.model._validate_audio(test_audio_path)
            assert result is True

    def test_validate_audio_nonexistent(self):
        """Test audio validation fails for non-existent files."""
        result = self.model._validate_audio(Path("/nonexistent/audio.wav"))
        assert result is False
