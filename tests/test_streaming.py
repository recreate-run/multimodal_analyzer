"""Test streaming JSON input functionality."""

import base64
import io
import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

from multimodal_analyzer_cli.cli import main
from multimodal_analyzer_cli.config import Config


class TestStreaming:
    """Test streaming JSON input functionality."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def create_test_image_base64(self, width: int = 10, height: int = 10, color: str = "red") -> str:
        """Create a simple test image and return as base64 data URL."""
        img = Image.new('RGB', (width, height), color=color)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/jpeg;base64,{img_str}"

    def test_streaming_validation_requires_both_formats(self):
        """Test that streaming requires both input-format and output stream-json."""
        # Test input-format without output stream-json
        result = self.runner.invoke(main, [
            "--type", "image",
            "--model", "gemini/gemini-2.5-flash",
            "-p", ".",
            "--input-format", "stream-json"
        ])
        assert result.exit_code != 0
        assert "requires --output stream-json" in result.output

        # Test output stream-json without input-format
        result = self.runner.invoke(main, [
            "--type", "image", 
            "--model", "gemini/gemini-2.5-flash",
            "-p", ".",
            "--output", "stream-json"
        ])
        assert result.exit_code != 0
        assert "requires --input-format stream-json" in result.output

    def test_streaming_validation_requires_path_flag(self):
        """Test that streaming requires -p flag."""
        result = self.runner.invoke(main, [
            "--type", "image",
            "--model", "gemini/gemini-2.5-flash", 
            "--input-format", "stream-json",
            "--output", "stream-json"
        ])
        assert result.exit_code != 0
        assert "requires -p flag" in result.output

    def test_streaming_validation_excludes_files_flag(self):
        """Test that streaming cannot be used with --files."""
        result = self.runner.invoke(main, [
            "--type", "image",
            "--model", "gemini/gemini-2.5-flash",
            "-p", ".",
            "--files", "test.jpg",
            "--input-format", "stream-json", 
            "--output", "stream-json"
        ])
        assert result.exit_code != 0
        # The CLI checks for mutually exclusive -p and --files first
        assert "Cannot specify both --path and --files" in result.output

    def test_streaming_validation_excludes_output_file(self):
        """Test that streaming cannot be used with --output-file."""
        result = self.runner.invoke(main, [
            "--type", "image",
            "--model", "gemini/gemini-2.5-flash",
            "-p", ".",
            "--output-file", "results.json",
            "--input-format", "stream-json",
            "--output", "stream-json" 
        ])
        assert result.exit_code != 0
        assert "cannot be used with --output-file" in result.output

    def get_primary_image_model(self) -> str:
        """Get the primary image model for testing."""
        config = Config.load()
        
        # Try Gemini first
        if config.gemini_api_key:
            return "gemini/gemini-2.5-flash"
        # Try OpenAI
        if config.openai_api_key:
            return "gpt-4o-mini"
        # Try Anthropic
        if config.anthropic_api_key:
            return "claude-3-sonnet-20240229"
        
        pytest.fail("No image analysis models available. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY environment variable.")

    def require_api_credentials(self, model: str):
        """Require API credentials for specified model. Raises error if missing."""
        config = Config.load()
        try:
            config.validate_api_keys(model)
        except Exception as e:
            pytest.fail(f"Required API credentials missing for {model}: {str(e)}")

    @pytest.mark.integration
    def test_streaming_image_analysis(self):
        """Test streaming image analysis with base64 input."""
        # Require API credentials for integration test
        model = self.get_primary_image_model()
        self.require_api_credentials(model)

        # Create test message with base64 image
        image_data_url = self.create_test_image_base64()
        test_message = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image briefly"},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        }

        # Convert to JSONL format
        json_input = json.dumps(test_message) + "\n"

        # Run streaming command
        result = self.runner.invoke(main, [
            "--type", "image",
            "--model", model,
            "-p", ".",
            "--input-format", "stream-json",
            "--output", "stream-json",
            "--log-level", "WARNING"  # Reduce log noise
        ], input=json_input)

        assert result.exit_code == 0

        # Parse the response (extract JSON from output)
        output_lines = result.output.strip().split('\n')
        json_response = None
        
        for line in output_lines:
            try:
                # Try to parse any line that looks like JSON
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    parsed = json.loads(line)
                    # Look for assistant response with success=True
                    if (parsed.get("type") == "assistant" and 
                        parsed.get("metadata", {}).get("success") is True):
                        json_response = parsed
                        break
            except json.JSONDecodeError:
                continue
        
        # Validate response format
        assert json_response is not None, f"No valid JSON response found in output: {result.output}"
        assert json_response["type"] == "assistant"
        assert "message" in json_response
        assert json_response["message"]["role"] == "assistant"
        assert "content" in json_response["message"]
        assert json_response["message"]["content"]  # Should have analysis content
        assert "metadata" in json_response
        assert json_response["metadata"]["success"] is True
        assert json_response["metadata"]["model"] == model

    def test_streaming_audio_not_implemented(self):
        """Test that audio streaming returns not implemented error."""
        result = self.runner.invoke(main, [
            "--type", "audio",
            "--model", "whisper-1",
            "--audio-mode", "transcript",
            "-p", ".",
            "--input-format", "stream-json",
            "--output", "stream-json"
        ])
        assert result.exit_code != 0
        assert "not yet implemented" in result.output

    def test_streaming_video_not_implemented(self):
        """Test that video streaming returns not implemented error."""
        result = self.runner.invoke(main, [
            "--type", "video", 
            "--model", "gemini/gemini-2.5-flash",
            "--video-mode", "description",
            "-p", ".",
            "--input-format", "stream-json",
            "--output", "stream-json"
        ])
        assert result.exit_code != 0
        assert "not yet implemented" in result.output