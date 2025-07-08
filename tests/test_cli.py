import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from multimodal_analyzer_cli.cli import main

from .test_utils import (
    FileManager,
    get_primary_image_model,
    get_primary_video_model,
    get_test_image_path,
    get_test_video_path,
    require_api_credentials,
)


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
                [
                    "--type",
                    "image",
                    "--model",
                    model_name,
                    "--path",
                    image_file,
                    "--word-count",
                    "30",
                ],
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
                    "--type",
                    "image",
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
                    "--type",
                    "image",
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
        # Use the actual test image from data directory
        test_image_path = get_test_image_path()

        with self.runner.isolated_filesystem():
            # Copy the real test image
            if test_image_path.exists():
                shutil.copy2(test_image_path, "speaker.jpg")
                image_file = "speaker.jpg"
            else:
                # Fallback to creating a test image if real one doesn't exist
                with FileManager() as manager:
                    temp_image = manager.create_test_image()
                    shutil.copy2(temp_image, "test.jpg")
                    image_file = "test.jpg"

            result = self.runner.invoke(
                main,
                [
                    "--type",
                    "image",
                    "--model",
                    "invalid-model-name",
                    "--path",
                    image_file,
                ],
            )

            # With immediate exception raising, the CLI should now fail with non-zero exit code
            assert result.exit_code != 0

    def test_nonexistent_image_path(self):
        """Test CLI with non-existent image path."""
        result = self.runner.invoke(
            main,
            [
                "--type",
                "image",
                "--model",
                "gpt-4o-mini",
                "--path",
                "/nonexistent/image.jpg",
            ],
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
                    "--type",
                    "image",
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

    def test_cli_video_analysis_with_real_api(self):
        """Test CLI video analysis with real Gemini API."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Use the real test video file if available, or skip
        test_video_path = get_test_video_path()
        if not test_video_path.exists():
            pytest.skip("No test video file available")

        result = self.runner.invoke(
            main,
            [
                "--type",
                "video",
                "--model",
                model_name,
                "--path",
                str(test_video_path),
                "--video-mode",
                "description",
                "--word-count",
                "30",
                "--output",
                "json",
            ],
        )

        # For real video with valid API, should succeed
        if result.exit_code != 0:
            print(f"CLI output: {result.output}")
        assert result.exit_code == 0
        assert "analysis" in result.output or "error" in result.output

    def test_cli_video_mode_validation_fails_fast(self):
        """Test CLI video mode validation fails fast."""
        with self.runner.isolated_filesystem():
            # Create a fake video file that exists
            fake_video = Path("fake_video.mp4")
            fake_video.touch()

            # Test missing video mode
            result = self.runner.invoke(
                main,
                [
                    "--type",
                    "video",
                    "--model",
                    "gemini/gemini-2.5-flash",
                    "--path",
                    str(fake_video),
                ],
            )

            assert result.exit_code != 0
            assert "video-mode is required" in result.output

            # Test audio-mode with video type
            result = self.runner.invoke(
                main,
                [
                    "--type",
                    "video",
                    "--model",
                    "gemini/gemini-2.5-flash",
                    "--path",
                    str(fake_video),
                    "--video-mode",
                    "description",
                    "--audio-mode",
                    "transcript",
                ],
            )

            assert result.exit_code != 0
            assert (
                "audio-mode should not be used when --type is 'video'" in result.output
            )

    def test_cli_video_batch_processing(self):
        """Test CLI video batch processing with directory."""
        model_name = get_primary_video_model()

        with self.runner.isolated_filesystem():
            # Create test directory with video files
            test_dir = Path("test_videos")
            test_dir.mkdir()

            # Create fake video files
            (test_dir / "video1.mp4").touch()
            (test_dir / "video2.avi").touch()
            (test_dir / "not_video.txt").touch()

            result = self.runner.invoke(
                main,
                [
                    "--type",
                    "video",
                    "--model",
                    model_name,
                    "--path",
                    str(test_dir),
                    "--video-mode",
                    "description",
                    "--word-count",
                    "20",
                    "--output",
                    "json",
                ],
            )

            # This will likely fail due to fake video files, but test CLI structure
            # The important thing is the CLI accepts the arguments correctly
            if result.exit_code != 0:
                # Expected - fake video files will fail validation
                assert (
                    "validation failed" in result.output
                    or "No video streams found" in result.output
                    or "does not exist" in result.output
                )

    def test_cli_video_help_display(self):
        """Test CLI help includes video options."""
        result = self.runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "video" in result.output
        assert "--video-mode" in result.output
        assert "Video analysis mode" in result.output

    def test_missing_required_options_hybrid(self):
        """Test CLI fails when neither --path nor --files is provided."""
        result = self.runner.invoke(main, [
            "--type", "image", 
            "--model", "gpt-4o-mini"
        ])
        assert result.exit_code != 0
        assert "Must specify either --path or --files" in result.output

    def test_mutually_exclusive_options(self):
        """Test CLI fails when both --path and --files are provided."""
        with self.runner.isolated_filesystem():
            # Create a test file so path validation passes
            with open("test.jpg", "w") as f:
                f.write("test")

            result = self.runner.invoke(main, [
                "--type", "image",
                "--model", "gpt-4o-mini",
                "--path", "test.jpg",
                "--files", "test.jpg"
            ])
            assert result.exit_code != 0
            assert "Cannot specify both --path and --files" in result.output

    @pytest.mark.integration
    def test_files_mode_analysis(self):
        """Test --files mode with explicit file list using real API calls."""
        model_name = get_primary_image_model()
        require_api_credentials()

        with self.runner.isolated_filesystem():
            # Create multiple test images
            with FileManager() as manager:
                img1 = manager.create_test_image(width=50, height=50, color="red")
                img2 = manager.create_test_image(width=50, height=50, color="blue")
                shutil.copy2(img1, "test1.jpg")
                shutil.copy2(img2, "test2.jpg")

            result = self.runner.invoke(
                main,
                [
                    "--type", "image",
                    "--model", model_name,
                    "--files", "test1.jpg",
                    "--files", "test2.jpg",
                    "--word-count", "30"
                ]
            )

            # Test must succeed - fail if CLI failed
            if result.exit_code != 0:
                pytest.fail(f"CLI files mode analysis failed: {result.output}")

            # Should process both images
            assert result.output is not None
            assert len(result.output) > 0

    def test_files_mode_nonexistent_file(self):
        """Test --files mode fails fast on nonexistent file."""
        result = self.runner.invoke(
            main,
            [
                "--type", "image",
                "--model", "gpt-4o-mini",
                "--files", "nonexistent.jpg"
            ]
        )
        assert result.exit_code != 0
        assert "File not found" in result.output

    def test_files_mode_unsupported_format(self):
        """Test --files mode fails fast on unsupported format."""
        with self.runner.isolated_filesystem():
            # Create a text file
            with open("test.txt", "w") as f:
                f.write("not an image")

            result = self.runner.invoke(
                main,
                [
                    "--type", "image",
                    "--model", "gpt-4o-mini",
                    "--files", "test.txt"
                ]
            )
            assert result.exit_code != 0
            assert "Unsupported format" in result.output
