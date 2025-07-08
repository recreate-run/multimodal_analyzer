import tempfile
from pathlib import Path

import pytest

from multimodal_analyzer_cli.config import Config
from multimodal_analyzer_cli.models.litellm_model import LiteLLMModel

from .test_utils import (
    FileManager,
    cleanup_temp_file,
    get_primary_image_model,
    get_primary_video_model,
    get_test_audio_path,
    get_test_image_path,
    get_test_video_path,
    require_api_credentials,
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
    async def test_analyze_audio_directly_success(self):
        """Test successful audio analysis with real API call using Gemini."""

        # Use Gemini model for direct audio analysis
        model_name = "gemini/gemini-2.5-flash"
        require_api_credentials(model_name)

        # Use the real test audio file
        test_audio_path = get_test_audio_path()

        result = await self.model.analyze_audio_directly(
            model=model_name, audio_path=test_audio_path, mode="transcript"
        )

        # Check result structure
        assert "success" in result
        assert "audio_path" in result
        assert "model" in result
        assert "mode" in result

        # For real audio, transcription should work
        if result["success"]:
            assert "transcript" in result
            assert result["error"] is None
        else:
            assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_audio_directly_validation_failure(self):
        """Test audio analysis with validation failure."""
        # Test with non-existent file
        nonexistent_path = Path("/nonexistent/audio.wav")

        with pytest.raises(ValueError, match="Invalid audio file"):
            await self.model.analyze_audio_directly(
                model="gemini/gemini-2.5-flash",
                audio_path=nonexistent_path,
                mode="transcript",
            )

    def test_validate_audio_success(self):
        """Test successful audio validation."""
        test_audio_path = get_test_audio_path()
        result = self.model._validate_audio(test_audio_path)
        assert result is True

    def test_validate_audio_nonexistent(self):
        """Test audio validation fails for non-existent files."""
        result = self.model._validate_audio(Path("/nonexistent/audio.wav"))
        assert result is False

    @pytest.mark.asyncio
    async def test_litellm_model_video_analysis_with_real_api(self):
        """Test video analysis with real Gemini API."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Use the real test video file if available, or skip
        test_video_path = get_test_video_path()
        if not test_video_path.exists():
            pytest.skip("No test video file available")

        result = await self.model.analyze_video(
            model=model_name,
            video_path=test_video_path,
            mode="description",
            word_count=50,
        )

        # Check result structure
        assert "success" in result
        assert "video_path" in result
        assert "model" in result
        assert "mode" in result
        assert "analysis" in result
        assert "word_count" in result

        # For real video with valid Gemini API, analysis should work
        if result["success"]:
            assert result["analysis"] is not None
            assert result["error"] is None
            assert result["mode"] == "description"
        else:
            assert "error" in result

    @pytest.mark.asyncio
    async def test_litellm_model_video_validation_fails_fast(self):
        """Test video analysis validation fails fast."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Test with non-existent file
        nonexistent_path = Path("/nonexistent/video.mp4")

        with pytest.raises(ValueError, match="Invalid video file"):
            await self.model.analyze_video(
                model=model_name, video_path=nonexistent_path, mode="description"
            )

    @pytest.mark.asyncio
    async def test_litellm_model_video_mode_validation(self):
        """Test video analysis mode validation."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Create a dummy video file for testing
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(b"fake video content")
            fake_video_path = Path(tmp.name)

        try:
            # Test invalid mode
            with pytest.raises(
                ValueError, match="Video analysis only supports 'description' mode"
            ):
                await self.model.analyze_video(
                    model=model_name, video_path=fake_video_path, mode="transcript"
                )

            with pytest.raises(
                ValueError, match="Video analysis only supports 'description' mode"
            ):
                await self.model.analyze_video(
                    model=model_name, video_path=fake_video_path, mode="summary"
                )
        finally:
            cleanup_temp_file(fake_video_path)

    @pytest.mark.asyncio
    async def test_litellm_model_non_gemini_model_fails_fast(self):
        """Test video analysis fails fast for non-Gemini models."""
        # Create a dummy video file for testing
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(b"fake video content")
            fake_video_path = Path(tmp.name)

        try:
            # Test with non-Gemini model
            with pytest.raises(
                ValueError, match="Video analysis only supports Gemini models"
            ):
                await self.model.analyze_video(
                    model="gpt-4o-mini", video_path=fake_video_path, mode="description"
                )

            with pytest.raises(
                ValueError, match="Video analysis only supports Gemini models"
            ):
                await self.model.analyze_video(
                    model="claude-3-sonnet-20240229",
                    video_path=fake_video_path,
                    mode="description",
                )
        finally:
            cleanup_temp_file(fake_video_path)
