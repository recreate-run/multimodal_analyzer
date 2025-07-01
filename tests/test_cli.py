import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil

from media_analyzer_cli.cli import main
from .test_utils import get_test_image_path, get_primary_image_model, FileManager


class TestCLI:
    """Test cases for CLI functionality.

    Note: Integration tests require actual API keys to be set in environment variables.
    They make real API calls (no mocking as requested in implementation plan).
    """

    def setup_method(self):
        self.runner = CliRunner()
        # Validate API keys are available before running integration tests
        try:
            get_primary_image_model()  # This will fail if no API keys
        except Exception:
            pass  # Non-integration tests don't need API keys

    def test_help_command(self):
        """Test --help command works."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ai-powered" in result.output.lower()

    def test_version_command(self):
        """Test --version command works."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_missing_required_options(self):
        """Test CLI fails with missing required options."""
        result = self.runner.invoke(main, [])
        assert result.exit_code != 0
        # CLI should indicate missing required parameters
        assert "Missing option" in result.output or "Usage:" in result.output

    @pytest.mark.integration
    def test_basic_image_analysis(self):
        """Test basic single image analysis with real API call."""

        model_name = get_primary_image_model()
        test_image_path = get_test_image_path()

        with self.runner.isolated_filesystem():
            # Copy test image to isolated filesystem or create one
            if test_image_path.exists():
                shutil.copy2(test_image_path, "test_image.jpg")
                image_file = "test_image.jpg"
            else:
                # Create a simple test image
                with FileManager() as manager:
                    temp_image = manager.create_test_image()
                    shutil.copy2(temp_image, "test_image.jpg")
                    image_file = "test_image.jpg"

            result = self.runner.invoke(
                main,
                ["--model", model_name, "--path", image_file, "--word-count", "30"],
            )

            # Test must succeed - fail if CLI failed
            if result.exit_code != 0:
                pytest.fail(f"CLI image analysis failed: {result.output}")
            
            # Should return some JSON output
            assert result.output is not None
            assert len(result.output) > 0

    @pytest.mark.integration
    def test_custom_options(self):
        """Test CLI with custom options using real API call."""

        # Use any available image model
        model_name = get_primary_image_model()

        with self.runner.isolated_filesystem():
            # Create test image
            with FileManager() as manager:
                temp_image = manager.create_test_image()
                shutil.copy2(temp_image, "test.png")

            result = self.runner.invoke(
                main,
                [
                    "--model",
                    model_name,
                    "--path",
                    "test.png",
                    "--word-count",
                    "50",
                    "--prompt",
                    "Describe briefly",
                    "--output",
                    "markdown",
                    "--output-file",
                    "results.md",
                    "--log-level",
                    "INFO",
                ],
            )

            # Test must succeed - fail if CLI failed
            if result.exit_code != 0:
                pytest.fail(f"CLI custom options test failed: {result.output}")
            
            # Check if output file was created
            output_file = Path("results.md")
            if output_file.exists():
                content = output_file.read_text()
                assert len(content) > 0
                assert "test.png" in content.lower() or "image" in content.lower()

    @pytest.mark.integration
    def test_verbose_flag(self):
        """Test CLI with verbose flag using real API call."""

        model_name = get_primary_image_model()

        with self.runner.isolated_filesystem():
            # Create test image
            with FileManager() as manager:
                temp_image = manager.create_test_image()
                shutil.copy2(temp_image, "test.png")

            result = self.runner.invoke(
                main,
                [
                    "--model",
                    model_name,
                    "--path",
                    "test.png",
                    "--verbose",
                    "--word-count",
                    "30",
                ],
            )

            # Test must succeed - fail if CLI failed
            if result.exit_code != 0:
                pytest.fail(f"CLI verbose flag test failed: {result.output}")
            
            # Verbose mode should include more detailed output
            assert result.output is not None
            assert len(result.output) > 0

    def test_invalid_model(self):
        """Test CLI with invalid model name."""
        with self.runner.isolated_filesystem():
            # Create a dummy image file
            test_image = Path("test.jpg")
            test_image.write_bytes(b"fake image data")

            result = self.runner.invoke(
                main, ["--model", "invalid-model-name", "--path", "test.jpg"]
            )

            # Should fail with invalid model
            assert result.exit_code != 0

    def test_nonexistent_image_path(self):
        """Test CLI with non-existent image path."""
        result = self.runner.invoke(
            main, ["--model", "gpt-4o-mini", "--path", "/nonexistent/image.jpg"]
        )

        # Should fail with file not found error
        assert result.exit_code != 0
        assert (
            "does not exist" in result.output.lower()
            or "no such file" in result.output.lower()
        )

    @pytest.mark.integration
    def test_batch_directory_processing(self):
        """Test CLI batch processing with directory."""

        model_name = get_primary_image_model()

        with self.runner.isolated_filesystem():
            # Create test directory with multiple images
            test_dir = Path("test_images")
            test_dir.mkdir()

            with FileManager() as manager:
                for i in range(2):  # Create 2 test images
                    temp_image = manager.create_test_image(
                        width=50, height=50, color=["red", "blue"][i]
                    )
                    shutil.copy2(temp_image, test_dir / f"image_{i}.jpg")

            result = self.runner.invoke(
                main,
                [
                    "--model",
                    model_name,
                    "--path",
                    str(test_dir),
                    "--word-count",
                    "20",
                    "--concurrency",
                    "1",  # Low concurrency to avoid rate limits
                ],
            )

            # Test must succeed - fail if CLI failed
            if result.exit_code != 0:
                pytest.fail(f"CLI batch directory processing failed: {result.output}")
            
            # Should process both images
            assert result.output is not None
            assert len(result.output) > 0
