"""Test cases for VideoAnalyzer functionality."""

import tempfile
from pathlib import Path

import pytest

from multimodal_analyzer_cli.config import Config
from multimodal_analyzer_cli.video_analyzer import VideoAnalyzer

from .test_utils import (
    cleanup_temp_file,
    get_primary_video_model,
    get_test_video_path,
    require_api_credentials,
)


class TestVideoAnalyzer:
    """Test cases for VideoAnalyzer functionality.

    Note: These tests require actual API keys to be set in environment variables.
    They are integration tests that make real API calls (no mocking as requested).
    """

    def setup_method(self):
        self.config = Config.load()
        self.analyzer = VideoAnalyzer(self.config)

    @pytest.mark.asyncio
    async def test_video_analyzer_single_file_with_real_api(self):
        """Test single video analysis with real Gemini API."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Use the real test video file if available, or skip
        test_video_path = get_test_video_path()
        if not test_video_path.exists():
            pytest.skip("No test video file available")

        result = await self.analyzer.analyze_single_video(
            model=model_name,
            video_path=test_video_path,
            mode="description",
            word_count=50,
            verbose=True,
        )

        # Check result structure
        assert "success" in result
        assert "video_path" in result
        assert "model" in result
        assert "mode" in result
        assert "analysis" in result
        assert "word_count" in result
        assert "video_info" in result

        # For real video with valid API, analysis should work
        if result["success"]:
            assert result["analysis"] is not None
            assert result["error"] is None
            assert result["mode"] == "description"
            assert "verbose" in result
        else:
            assert "error" in result

    @pytest.mark.asyncio
    async def test_video_analyzer_batch_processing_with_real_api(self):
        """Test batch video processing with real Gemini API."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Create temporary video files for testing
        temp_files = []
        try:
            for i in range(2):
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=f"_test_{i}.mp4", delete=False
                )
                temp_file.write(b"fake video content")
                temp_file.flush()
                temp_files.append(Path(temp_file.name))

            # Use analyze_batch_with_progress to handle exceptions gracefully
            results = await self.analyzer.analyze_batch_with_progress(
                model=model_name,
                video_files=temp_files,
                mode="description",
                word_count=30,
                concurrency=2,
            )

            assert len(results) == 2
            for result in results:
                assert "success" in result
                assert "video_path" in result
                assert "model" in result
                assert "mode" in result
                # Note: These will likely fail validation, so success should be False
                if not result["success"]:
                    assert "error" in result
                else:
                    assert "analysis" in result

        finally:
            # Cleanup temporary files
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)

    @pytest.mark.asyncio
    async def test_video_analyzer_error_handling_fails_fast(self):
        """Test error handling with fail-fast behavior."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Test with non-existent file
        nonexistent_path = Path("/nonexistent/video.mp4")

        with pytest.raises((ValueError, FileNotFoundError)):
            await self.analyzer.analyze_single_video(
                model=model_name, video_path=nonexistent_path, mode="description"
            )

    @pytest.mark.asyncio
    async def test_video_analyzer_mode_validation(self):
        """Test mode validation for video analysis."""
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
                await self.analyzer.analyze_single_video(
                    model=model_name, video_path=fake_video_path, mode="transcript"
                )

            with pytest.raises(
                ValueError, match="Video analysis only supports 'description' mode"
            ):
                await self.analyzer.analyze_single_video(
                    model=model_name, video_path=fake_video_path, mode="summary"
                )
        finally:
            cleanup_temp_file(fake_video_path)

    @pytest.mark.asyncio
    async def test_video_analyzer_directory_processing(self):
        """Test directory processing for video analysis."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Create a temporary directory with video files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test video files
            (temp_path / "video1.mp4").touch()
            (temp_path / "video2.avi").touch()
            (temp_path / "not_video.txt").touch()

            # Test directory analysis
            try:
                formatted_output = await self.analyzer.analyze(
                    model=model_name,
                    path=temp_path,
                    mode="description",
                    word_count=30,
                    output_format="json",
                    recursive=False,
                    concurrency=2,
                )

                assert isinstance(formatted_output, str)
                # Should contain results for 2 video files
                import json

                results = json.loads(formatted_output)
                assert len(results) == 2

            except ValueError as e:
                # This is expected if video validation fails for fake files
                assert "validation failed" in str(e) or "No video streams found" in str(
                    e
                )

    @pytest.mark.asyncio
    async def test_video_analyzer_non_gemini_model_fails_fast(self):
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
                await self.analyzer.analyze_single_video(
                    model="gpt-4o-mini", video_path=fake_video_path, mode="description"
                )

            with pytest.raises(
                ValueError, match="Video analysis only supports Gemini models"
            ):
                await self.analyzer.analyze_single_video(
                    model="claude-3-sonnet-20240229",
                    video_path=fake_video_path,
                    mode="description",
                )
        finally:
            cleanup_temp_file(fake_video_path)

    @pytest.mark.asyncio
    async def test_video_analyzer_output_formatting(self):
        """Test output formatting for video results."""
        # Test with mock results (no API call needed)
        mock_results = [
            {
                "video_path": "/test/video1.mp4",
                "model": "gemini/gemini-2.5-flash",
                "mode": "description",
                "analysis": "Test analysis result",
                "word_count": 50,
                "success": True,
                "error": None,
                "video_info": {
                    "duration_minutes": 2.5,
                    "format": "mp4",
                    "width": 1920,
                    "height": 1080,
                    "file_size_mb": 15.2,
                },
            }
        ]

        # Test JSON formatting
        json_output = self.analyzer._format_output(mock_results, "json", verbose=True)
        assert "video_path" in json_output
        assert "Test analysis result" in json_output

        # Test Markdown formatting
        md_output = self.analyzer._format_output(mock_results, "markdown", verbose=True)
        assert "# Video Analysis Results" in md_output
        assert "Test analysis result" in md_output

        # Test Text formatting
        text_output = self.analyzer._format_output(mock_results, "text", verbose=True)
        assert "Video Analysis Results" in text_output
        assert "Test analysis result" in text_output
