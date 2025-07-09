import tempfile
from pathlib import Path

import numpy as np
import pytest
from pydub import AudioSegment

from multimodal_analyzer_cli.audio_analyzer import AudioAnalyzer
from multimodal_analyzer_cli.config import Config
from multimodal_analyzer_cli.utils.audio import (
    cleanup_temp_audio,
    get_audio_info,
    is_audio_file,
    is_media_file,
    is_video_file,
    prepare_audio_for_transcription,
    validate_audio_file,
)

from .test_utils import (
    get_test_audio_path,
    get_test_video_path,
    require_api_credentials,
)


class TestAudioUtils:
    """Test cases for audio utility functions."""

    def test_is_audio_file(self):
        """Test audio file detection."""
        assert is_audio_file(Path("test.mp3"))
        assert is_audio_file(Path("test.wav"))
        assert is_audio_file(Path("test.m4a"))
        assert is_audio_file(Path("test.flac"))
        assert is_audio_file(Path("test.ogg"))
        assert not is_audio_file(Path("test.txt"))
        assert not is_audio_file(Path("test.jpg"))

    def test_is_video_file(self):
        """Test video file detection."""
        assert is_video_file(Path("test.mp4"))
        assert is_video_file(Path("test.avi"))
        assert is_video_file(Path("test.mov"))
        assert is_video_file(Path("test.mkv"))
        assert not is_video_file(Path("test.txt"))
        assert not is_video_file(Path("test.mp3"))

    def test_is_media_file(self):
        """Test media file detection."""
        assert is_media_file(Path("test.mp3"))
        assert is_media_file(Path("test.mp4"))
        assert is_media_file(Path("test.wav"))
        assert is_media_file(Path("test.avi"))
        assert not is_media_file(Path("test.txt"))
        assert not is_media_file(Path("test.jpg"))

    def create_test_audio_file(self):
        """Create a test audio file for testing purposes."""
        # Generate 1 second of sine wave audio (440 Hz)
        sample_rate = 44100
        duration = 1.0  # seconds
        frequency = 440  # Hz

        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.sin(2 * np.pi * frequency * t)

        # Convert to 16-bit PCM
        audio_data = (wave * 32767).astype(np.int16)

        # Create AudioSegment
        audio = AudioSegment(
            audio_data.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1
        )

        # Save to temporary file and return path for testing
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            audio.export(tmp_file.name, format="wav")
            temp_path = Path(tmp_file.name)
            assert temp_path.exists()
            return temp_path

    def test_create_test_audio_file(self):
        """Test creating a test audio file."""
        # Create and immediately clean up test file
        temp_path = self.create_test_audio_file()
        try:
            assert temp_path.exists()
        finally:
            # Clean up the temporary file
            temp_path.unlink()

    def test_get_audio_info(self):
        """Test getting audio file information."""
        # Use real test audio file if available, otherwise create synthetic one
        test_audio_path = get_test_audio_path()

        if test_audio_path.exists():
            # Use real test audio file
            audio_info = get_audio_info(test_audio_path)

            assert "duration_seconds" in audio_info
            assert "duration_minutes" in audio_info
            assert "sample_rate" in audio_info
            assert "channels" in audio_info
            assert "file_size_bytes" in audio_info
            assert "format" in audio_info

            # Check reasonable values
            assert audio_info["duration_seconds"] > 0
            assert audio_info["sample_rate"] > 0
            assert audio_info["channels"] > 0
            assert audio_info["file_size_bytes"] > 0
            assert audio_info["format"] in ["mp3", "wav", "m4a", "flac", "ogg"]
        else:
            # Fallback to synthetic audio file
            test_audio_path = self.create_test_audio_file()
            try:
                audio_info = get_audio_info(test_audio_path)
                assert "duration_seconds" in audio_info
                assert audio_info["format"] == "wav"
            finally:
                if test_audio_path.exists():
                    test_audio_path.unlink()

    def test_validate_audio_file(self):
        """Test audio file validation."""
        # Use real test audio file if available
        test_audio_path = get_test_audio_path()

        if test_audio_path.exists():
            # Valid real audio file should pass validation
            assert validate_audio_file(test_audio_path) == True
        else:
            # Fallback to synthetic audio file
            test_audio_path = self.create_test_audio_file()
            try:
                assert validate_audio_file(test_audio_path) == True
            finally:
                if test_audio_path.exists():
                    test_audio_path.unlink()

        # Non-existent file should fail validation
        assert validate_audio_file(Path("nonexistent.wav")) == False

    def test_prepare_audio_for_transcription(self):
        """Test audio preparation for transcription."""
        # Use real test audio file if available
        test_audio_path = get_test_audio_path()

        if test_audio_path.exists():
            # Prepare real audio file (should return same file for audio)
            prepared_path, is_temp = prepare_audio_for_transcription(test_audio_path)
            assert prepared_path == test_audio_path
            assert is_temp == False
        else:
            # Fallback to synthetic audio file
            test_audio_path = self.create_test_audio_file()
            try:
                prepared_path, is_temp = prepare_audio_for_transcription(
                    test_audio_path
                )
                assert prepared_path == test_audio_path
                assert is_temp == False
            finally:
                if test_audio_path.exists():
                    test_audio_path.unlink()

    def test_prepare_video_for_transcription(self):
        """Test video file preparation for transcription."""
        # Test with real video file if available
        test_video_path = get_test_video_path()

        if test_video_path.exists():
            # Video should be prepared (audio extracted)
            prepared_path, is_temp = prepare_audio_for_transcription(test_video_path)

            # Should extract audio to a temporary file
            assert prepared_path != test_video_path
            assert is_temp == True
            assert prepared_path.suffix.lower() in [".wav", ".mp3", ".m4a"]

            # Clean up temporary file
            if is_temp and prepared_path.exists():
                cleanup_temp_audio(prepared_path)

    def test_cleanup_temp_audio(self):
        """Test temporary audio file cleanup."""
        # Create test audio file
        test_audio_path = self.create_test_audio_file()

        # Verify file exists
        assert test_audio_path.exists()

        # Clean up the file
        cleanup_temp_audio(test_audio_path)

        # Verify file is deleted
        assert not test_audio_path.exists()


class TestAudioAnalyzer:
    """Test cases for AudioAnalyzer functionality.

    Note: These tests require actual API keys to be set in environment variables.
    They are integration tests that make real API calls (no mocking as requested).
    """

    def setup_method(self):
        """Set up test fixtures."""
        # Require API credentials for Gemini models
        require_api_credentials("gemini/gemini-2.5-flash")

        self.config = Config.load()
        self.analyzer = AudioAnalyzer(self.config)

        # Use real test audio file if available, otherwise create synthetic one
        self.test_audio_path = get_test_audio_path()
        if not self.test_audio_path.exists():
            self.test_audio_path = self._create_test_audio_with_speech()
            self._using_synthetic_audio = True
        else:
            self._using_synthetic_audio = False

    def teardown_method(self):
        """Clean up test fixtures."""
        # Only clean up if we created a synthetic audio file
        if (
            hasattr(self, "_using_synthetic_audio")
            and self._using_synthetic_audio
            and hasattr(self, "test_audio_path")
            and self.test_audio_path.exists()
        ):
            self.test_audio_path.unlink()

    def _create_test_audio_with_speech(self):
        """Create a test audio file with synthesized speech for testing."""
        # Generate a longer sine wave that could potentially be processed
        sample_rate = 44100
        duration = 5.0  # 5 seconds
        frequency = 440  # Hz

        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.sin(2 * np.pi * frequency * t)

        # Add some variation to make it more speech-like
        wave = wave * (1 + 0.1 * np.sin(2 * np.pi * 10 * t))

        # Convert to 16-bit PCM
        audio_data = (wave * 16000).astype(np.int16)  # Lower volume

        # Create AudioSegment
        audio = AudioSegment(
            audio_data.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            audio.export(tmp_file.name, format="wav")
            return Path(tmp_file.name)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_single_audio_transcript_mode(self):
        """Test single audio file transcription."""

        try:
            result = await self.analyzer.analyze_single_audio(
                model="gemini/gemini-2.5-flash",
                audio_path=self.test_audio_path,
                mode="transcript",
                verbose=True,
            )

            # Check result structure
            assert "audio_path" in result
            assert "model" in result
            assert "mode" in result
            assert "success" in result
            assert result["mode"] == "transcript"

            # Test must succeed - fail if API call failed
            if not result["success"]:
                pytest.fail(
                    f"Audio transcription failed: {result.get('error', 'Unknown error')}"
                )

            assert "transcript" in result
            assert "audio_info" in result

        except Exception as e:
            pytest.fail(f"Unexpected error in transcription test: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_single_audio_description_mode(self):
        """Test single audio file description analysis."""

        try:
            result = await self.analyzer.analyze_single_audio(
                model="gemini/gemini-2.5-flash",
                audio_path=self.test_audio_path,
                mode="description",
                word_count=50,
                prompt="Describe the content of this audio",
                verbose=True,
            )

            # Check result structure
            assert "audio_path" in result
            assert "mode" in result
            assert "success" in result
            assert result["mode"] == "description"

            # Test must succeed - fail if API call failed
            if not result["success"]:
                pytest.fail(
                    f"Audio description analysis failed: {result.get('error', 'Unknown error')}"
                )

            assert "transcript" in result
            assert "analysis" in result
            assert "model" in result
            assert "prompt" in result
            assert "word_count" in result
            assert "audio_info" in result

        except Exception as e:
            pytest.fail(f"Unexpected error in description test: {e}")

    @pytest.mark.asyncio
    async def test_analyze_invalid_mode(self):
        """Test error handling for invalid analysis mode."""
        with pytest.raises(ValueError, match="Invalid mode"):
            await self.analyzer.analyze_single_audio(
                model="gemini/gemini-2.5-flash",
                audio_path=self.test_audio_path,
                mode="invalid_mode",
            )

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self):
        """Test error handling for non-existent audio file."""
        nonexistent_path = Path("nonexistent_audio_file.wav")

        with pytest.raises(ValueError, match="Audio file validation failed"):
            await self.analyzer.analyze_single_audio(
                model="gemini/gemini-2.5-flash",
                audio_path=nonexistent_path,
                mode="transcript",
            )

    def test_output_formatting_json(self):
        """Test JSON output formatting for audio results."""
        test_results = [
            {
                "audio_path": "/test/audio.wav",
                "mode": "transcript",
                "model": "gemini/gemini-2.5-flash",
                "transcript": "Test transcript",
                "success": True,
                "audio_info": {"duration_minutes": 1.0, "format": "wav"},
            }
        ]

        # Test non-verbose JSON
        json_output = self.analyzer.output_formatter.format_audio_json(
            test_results, verbose=False
        )
        assert '"audio_path": "/test/audio.wav"' in json_output
        assert '"mode": "transcript"' in json_output
        assert '"transcript": "Test transcript"' in json_output
        assert '"success": true' in json_output

        # Should not include audio_info in non-verbose mode
        assert '"audio_info"' not in json_output

    def test_output_formatting_markdown(self):
        """Test Markdown output formatting for audio results."""
        test_results = [
            {
                "audio_path": "/test/audio.wav",
                "mode": "description",
                "transcription_model": "gemini/gemini-2.5-flash",
                "analysis_model": "azure/gpt-4o-mini",
                "transcript": "Test transcript",
                "analysis": "Test analysis",
                "success": True,
                "audio_info": {"duration_minutes": 1.0, "format": "wav"},
            }
        ]

        markdown_output = self.analyzer.output_formatter.format_audio_markdown(
            test_results, verbose=True
        )

        assert "# Audio Analysis Results" in markdown_output
        assert "audio.wav" in markdown_output
        assert "**Mode:** description" in markdown_output
        assert "**Transcript:**" in markdown_output
        assert "**Analysis:**" in markdown_output
        assert "Test transcript" in markdown_output
        assert "Test analysis" in markdown_output

    def test_output_formatting_text(self):
        """Test plain text output formatting for audio results."""
        test_results = [
            {
                "audio_path": "/test/audio.wav",
                "mode": "transcript",
                "model": "gemini/gemini-2.5-flash",
                "transcript": "Test transcript",
                "success": True,
            }
        ]

        text_output = self.analyzer.output_formatter.format_audio_text(
            test_results, verbose=False
        )

        assert "Audio Analysis Results" in text_output
        assert "audio.wav" in text_output
        assert "Mode: transcript" in text_output
        assert "Transcript:" in text_output
        assert "Test transcript" in text_output

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_processing(self):
        """Test batch processing of multiple audio files."""

        # Use real test files if available, otherwise create synthetic ones
        audio_files = [self.test_audio_path]
        files_to_cleanup = []

        # Try to add the test video file if it exists (for audio extraction testing)
        test_video_path = get_test_video_path()
        if test_video_path.exists():
            audio_files.append(test_video_path)
        else:
            # Create a second synthetic audio file
            test_audio_path2 = self._create_test_audio_with_speech()
            audio_files.append(test_audio_path2)
            files_to_cleanup.append(test_audio_path2)

        try:
            results = await self.analyzer.analyze_batch(
                model="gemini/gemini-2.5-flash",
                audio_files=audio_files,
                mode="transcript",
                concurrency=1,  # Use low concurrency to avoid rate limits
            )

            assert len(results) == 2
            assert all("audio_path" in result for result in results)
            assert all("mode" in result for result in results)
            assert all("success" in result for result in results)

        finally:
            # Clean up any synthetic test files
            for file_path in files_to_cleanup:
                if file_path.exists():
                    file_path.unlink()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_test_files_analysis(self):
        """Test analysis using the actual test files from data directory."""

        test_audio_path = get_test_audio_path()
        test_video_path = get_test_video_path()

        # Test real audio file if available
        if test_audio_path.exists():
            print(f"Testing with real audio file: {test_audio_path}")
            result = await self.analyzer.analyze_single_audio(
                model="gemini/gemini-2.5-flash",
                audio_path=test_audio_path,
                mode="transcript",
                verbose=True,
            )

            assert "audio_path" in result
            assert str(test_audio_path) in result["audio_path"]
            assert "success" in result

            # Test must succeed - fail if API call failed
            if not result["success"]:
                pytest.fail(
                    f"Real audio analysis failed: {result.get('error', 'Unknown error')}"
                )

            assert "transcript" in result
            assert "audio_info" in result
            print(
                f"Successfully analyzed real audio: {result.get('transcript', 'No transcript')[:100]}..."
            )

        # Test real video file if available (audio extraction)
        if test_video_path.exists():
            print(f"Testing with real video file: {test_video_path}")
            result = await self.analyzer.analyze_single_audio(
                model="gemini/gemini-2.5-flash",
                audio_path=test_video_path,
                mode="transcript",
                verbose=True,
            )

            assert "audio_path" in result
            assert str(test_video_path) in result["audio_path"]
            assert "success" in result

            # Test must succeed - fail if API call failed
            if not result["success"]:
                pytest.fail(
                    f"Video audio analysis failed: {result.get('error', 'Unknown error')}"
                )

            assert "transcript" in result
            transcript = result.get("transcript", "No transcript")
            display_transcript = (
                transcript[:100] + "..."
                if transcript and len(transcript) > 100
                else transcript
            )
            print(f"Successfully analyzed video audio: {display_transcript}")

    def test_config_loading_with_audio_keys(self):
        """Test configuration loading with audio-specific environment variables."""
        # Test that config loads audio-specific environment variables
        test_env = {
            "AZURE_OPENAI_API_KEY": "test_azure_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "GEMINI_API_KEY": "test_gemini_key",
        }

        with pytest.MonkeyPatch().context() as m:
            for key, value in test_env.items():
                m.setenv(key, value)

            config = Config.load()

            assert config.AZURE_OPENAI_API_KEY == "test_azure_key"
            assert config.azure_openai_endpoint == "https://test.openai.azure.com/"
            assert config.gemini_api_key == "test_gemini_key"

    def test_api_key_selection_for_audio_models(self):
        """Test API key selection logic for audio models."""
        # Create config with test keys
        config = Config()
        config.AZURE_OPENAI_API_KEY = "azure_key"
        config.openai_api_key = "openai_key"
        config.gemini_api_key = "gemini_key"

        # Test Gemini model key selection (should use Gemini key)
        assert config.get_api_key("gemini/gemini-2.5-flash") == "gemini_key"

        # Test with only Gemini key available
        config.AZURE_OPENAI_API_KEY = None
        config.openai_api_key = None
        assert config.get_api_key("gemini/gemini-2.5-flash") == "gemini_key"

        # Test OpenAI Whisper model uses OpenAI key when available
        config.openai_api_key = "openai_key"  # Reset for this test
        assert config.get_api_key("whisper-1") == "openai_key"


# Integration test marker configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (requires API keys)"
    )
