"""End-to-end CLI tests for video analysis functionality."""

import pytest
from click.testing import CliRunner

from multimodal_analyzer_cli.cli import main

from .test_utils import (
    get_primary_video_model,
    get_test_video_path,
    require_api_credentials,
)


class TestCLIVideo:
    """End-to-end CLI tests for video analysis.

    Note: These tests require actual API keys to be set in environment variables.
    They make real API calls (no mocking as requested in implementation plan).
    """

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.integration
    def test_cli_video_end_to_end_with_real_gemini_api(self):
        """Test complete video analysis workflow with real Gemini API."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        # Use the real test video file if available, or skip
        test_video_path = get_test_video_path()
        if not test_video_path.exists():
            pytest.skip("No test video file available")

        # Test single video analysis with various output formats
        for output_format in ["json", "markdown", "text"]:
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
                    "40",
                    "--output",
                    output_format,
                    "--verbose",
                ],
            )

            # For real video with valid API, should succeed
            if result.exit_code != 0:
                pytest.fail(
                    f"CLI video analysis failed with {output_format}: {result.output}"
                )

            assert result.output is not None
            assert len(result.output) > 0

            if output_format == "json":
                assert "{" in result.output and "}" in result.output
            elif output_format == "markdown":
                assert "# Video Analysis Results" in result.output
            elif output_format == "text":
                assert "Video Analysis Results" in result.output

    @pytest.mark.integration
    def test_cli_video_with_custom_prompt(self):
        """Test video analysis with custom prompt."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        test_video_path = get_test_video_path()
        if not test_video_path.exists():
            pytest.skip("No test video file available")

        custom_prompt = "Describe the main visual elements and any audio in this video"

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
                "--prompt",
                custom_prompt,
                "--word-count",
                "30",
                "--output",
                "json",
            ],
        )

        if result.exit_code != 0:
            pytest.fail(
                f"CLI video analysis with custom prompt failed: {result.output}"
            )

        assert result.output is not None
        assert len(result.output) > 0

    @pytest.mark.integration
    def test_cli_video_output_to_file(self):
        """Test video analysis with output saved to file."""
        model_name = get_primary_video_model()
        require_api_credentials(model_name)

        test_video_path = get_test_video_path()
        if not test_video_path.exists():
            pytest.skip("No test video file available")

        with self.runner.isolated_filesystem():
            output_file = "video_analysis_results.json"

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
                    "25",
                    "--output",
                    "json",
                    "--output-file",
                    output_file,
                ],
            )

            if result.exit_code != 0:
                pytest.fail(
                    f"CLI video analysis with file output failed: {result.output}"
                )

            # Check that file was created
            from pathlib import Path

            output_path = Path(output_file)
            assert output_path.exists()

            # Check file contents
            with open(output_path, "r") as f:
                content = f.read()
                assert len(content) > 0
                assert "{" in content  # JSON format
