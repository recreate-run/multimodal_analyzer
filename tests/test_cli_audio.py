import tempfile
from pathlib import Path

import numpy as np
from click.testing import CliRunner
from pydub import AudioSegment

from multimodal_analyzer_cli.cli import main

from .test_utils import get_test_audio_path


class TestAudioCLI:
    """Test cases for CLI audio functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        # Use real test audio file
        self.test_audio_path = get_test_audio_path()

    def test_cli_missing_type_parameter(self):
        """Test that CLI requires --type parameter."""
        result = self.runner.invoke(
            main, ["--model", "whisper-1", "--path", str(self.test_audio_path)]
        )

        assert result.exit_code != 0
        assert "Error: Missing option '--type'" in result.output

    def test_cli_audio_missing_mode_parameter(self):
        """Test that CLI requires --audio-mode for audio type."""
        result = self.runner.invoke(
            main,
            [
                "--type",
                "audio",
                "--model",
                "whisper-1",
                "--path",
                str(self.test_audio_path),
            ],
        )

        assert result.exit_code != 0
        assert "audio-mode is required when --type is 'audio'" in result.output

    def test_cli_image_with_audio_mode_parameter(self):
        """Test that CLI rejects --audio-mode for image type."""
        result = self.runner.invoke(
            main,
            [
                "--type",
                "image",
                "--model",
                "gpt-4o-mini",
                "--path",
                str(self.test_audio_path),
                "--audio-mode",
                "transcript",
            ],
        )

        assert result.exit_code != 0
        assert "audio-mode should not be used when --type is 'image'" in result.output

    def test_cli_audio_invalid_mode(self):
        """Test CLI with invalid audio mode."""
        result = self.runner.invoke(
            main,
            [
                "--type",
                "audio",
                "--model",
                "whisper-1",
                "--path",
                str(self.test_audio_path),
                "--audio-mode",
                "invalid",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value for '--audio-mode'" in result.output

    def test_cli_audio_valid_parameters_structure(self):
        """Test that CLI accepts valid audio parameters (structure test only)."""
        # This test only checks parameter validation, not actual execution
        # since we don't want to make API calls in unit tests

        # Test with transcript mode
        result = self.runner.invoke(
            main,
            [
                "--type",
                "audio",
                "--model",
                "whisper-1",
                "--path",
                "/nonexistent/file.wav",  # Use non-existent file to avoid API calls
                "--audio-mode",
                "transcript",
            ],
            catch_exceptions=False,
        )

        # Should fail because file doesn't exist, not because of parameter structure
        assert result.exit_code != 0
        # Should not fail because of missing parameters
        assert "Missing option" not in result.output
        assert "should not be used" not in result.output

    def test_cli_help_includes_audio_options(self):
        """Test that CLI help includes audio-specific options."""
        result = self.runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "--type" in result.output
        assert "--audio-mode" in result.output
        assert "Analysis type: image, audio, or video" in result.output
        assert "Audio analysis mode" in result.output

    def test_cli_output_format_text_option(self):
        """Test that CLI includes 'text' as an output format option."""
        result = self.runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "text" in result.output  # Should be available as output format

    def test_cli_audio_description_mode_parameters(self):
        """Test CLI parameters for audio description mode."""
        result = self.runner.invoke(
            main,
            [
                "--type",
                "audio",
                "--model",
                "gpt-4o-mini",
                "--path",
                "/nonexistent/file.wav",
                "--audio-mode",
                "description",
                "--word-count",
                "200",
                "--prompt",
                "Test prompt",
                "--output",
                "json",
                "--verbose",
            ],
            catch_exceptions=False,
        )

        # Should fail because file doesn't exist, not because of parameter issues
        assert result.exit_code != 0
        assert "Missing option" not in result.output
        assert "should not be used" not in result.output

    def test_cli_nonexistent_file_error_handling(self):
        """Test CLI error handling for non-existent files."""
        result = self.runner.invoke(
            main,
            [
                "--type",
                "audio",
                "--model",
                "whisper-1",
                "--path",
                "/completely/nonexistent/file.wav",
                "--audio-mode",
                "transcript",
            ],
        )

        assert result.exit_code != 0
        # Should handle file not found error gracefully
