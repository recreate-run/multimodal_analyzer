import tempfile
from pathlib import Path

import pytest

from multimodal_analyzer_cli.config import Config
from multimodal_analyzer_cli.image_analyzer import ImageAnalyzer

from .test_utils import (
    FileManager,
    get_primary_image_model,
    get_test_image_path,
)


class TestImageAnalyzer:
    """Test cases for ImageAnalyzer functionality.

    Note: These tests require actual API keys to be set in environment variables.
    They are integration tests that make real API calls (no mocking as requested).
    """

    def setup_method(self):
        self.config = Config.load()
        # Validate API keys are available before running tests
        model_name = get_primary_image_model()  # This will fail if no API keys
        self.config.validate_api_keys(model_name)
        self.analyzer = ImageAnalyzer(self.config)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_single_image_success(self):
        """Test successful single image analysis with real API call."""

        model_name = get_primary_image_model()
        test_image_path = get_test_image_path()

        # Use real test image or create one if not available
        if not test_image_path.exists():
            with FileManager() as manager:
                test_image_path = manager.create_test_image()

                result = await self.analyzer.analyze(
                    model=model_name,
                    path=test_image_path,
                    word_count=50,
                    prompt="Describe this image briefly",
                    verbose=True,
                )
        else:
            result = await self.analyzer.analyze(
                model=model_name,
                path=test_image_path,
                word_count=50,
                prompt="Describe this image briefly",
                verbose=True,
            )

        # Should return JSON string with success indicator
        assert isinstance(result, str)
        assert '"success"' in result

        # Parse result to check structure and ensure success
        import json

        try:
            parsed_result = json.loads(result)
            assert isinstance(parsed_result, list)
            if len(parsed_result) > 0:
                # Test must succeed - fail if API call failed
                if not parsed_result[0].get("success", False):
                    pytest.fail(
                        f"Image analysis failed: {parsed_result[0].get('error', 'Unknown error')}"
                    )
                assert "image_path" in parsed_result[0]
                assert "model" in parsed_result[0]
        except json.JSONDecodeError:
            pytest.fail("Result is not valid JSON")

    @pytest.mark.asyncio
    async def test_analyze_no_images_found(self):
        """Test error when no images are found."""
        # Create empty temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(ValueError, match="No supported image files found"):
                await self.analyzer.analyze(
                    model="gpt-4o-mini",  # Model doesn't matter for this test
                    path=temp_path,
                    word_count=100,
                )

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_analyze_batch_processing(self):
        """Test batch processing with multiple images using real API calls."""

        model_name = get_primary_image_model()

        with FileManager() as manager:
            # Create multiple test images
            test_images = [
                manager.create_test_image(width=50, height=50, color="red"),
                manager.create_test_image(width=50, height=50, color="blue"),
                manager.create_test_image(width=50, height=50, color="green"),
            ]

            # Create temporary directory and copy images
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Copy test images to temp directory
                for i, img_path in enumerate(test_images):
                    dest_path = temp_path / f"test_image_{i}.jpg"
                    import shutil

                    shutil.copy2(img_path, dest_path)

                result = await self.analyzer.analyze(
                    model=model_name,
                    path=temp_path,
                    concurrency=2,
                    word_count=30,
                    verbose=True,
                )

                # Should return JSON with multiple results
                assert isinstance(result, str)
                assert '"success"' in result

                # Parse and validate structure
                import json

                try:
                    parsed_result = json.loads(result)
                    assert isinstance(parsed_result, list)
                    assert len(parsed_result) == 3  # Should process all 3 images

                    for item in parsed_result:
                        # Test must succeed - fail if any API call failed
                        if not item.get("success", False):
                            pytest.fail(
                                f"Batch image analysis failed for {item.get('image_path', 'unknown')}: {item.get('error', 'Unknown error')}"
                            )
                        assert "image_path" in item
                        assert "model" in item
                        assert "success" in item
                except json.JSONDecodeError:
                    pytest.fail("Result is not valid JSON")

    def test_format_output_json(self):
        """Test JSON output formatting."""
        results = [
            {
                "image_path": "/test.jpg",
                "model": "test-model",
                "analysis": "test analysis",
                "success": True,
                "prompt": "test prompt",
                "word_count": 100,
                "extra_field": "extra_data",
            }
        ]

        # Test verbose mode - should include all data
        output_verbose = self.analyzer._format_output(results, "json", verbose=True)
        assert '"image_path": "/test.jpg"' in output_verbose
        assert '"model": "test-model"' in output_verbose
        assert '"analysis": "test analysis"' in output_verbose
        assert '"extra_field": "extra_data"' in output_verbose

        # Test non-verbose mode - should only include essential fields
        output_non_verbose = self.analyzer._format_output(
            results, "json", verbose=False
        )
        assert '"image_path": "/test.jpg"' in output_non_verbose
        assert '"analysis": "test analysis"' in output_non_verbose
        # Extra fields should not be included in non-verbose mode
        # (specific behavior depends on OutputFormatter implementation)

    def test_format_output_invalid_format(self):
        """Test error with invalid output format."""
        results = [{"image_path": "/test.jpg", "analysis": "test"}]
        with pytest.raises(ValueError, match="Unsupported output format"):
            self.analyzer._format_output(results, "invalid")

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self):
        """Test error handling for non-existent file."""
        nonexistent_path = Path("/definitely/does/not/exist.jpg")

        with pytest.raises(ValueError, match="No supported image files found"):
            await self.analyzer.analyze(
                model="gpt-4o-mini",  # Model doesn't matter for this test
                path=nonexistent_path,
                word_count=100,
            )

    def test_format_output_markdown(self):
        """Test Markdown output formatting."""
        results = [
            {
                "image_path": "/test.jpg",
                "model": "test-model",
                "prompt": "test prompt",
                "word_count": 100,
                "analysis": "test analysis",
                "success": True,
            }
        ]

        output = self.analyzer._format_output(results, "markdown", verbose=True)
        assert isinstance(output, str)
        assert "test.jpg" in output
        assert "test analysis" in output

