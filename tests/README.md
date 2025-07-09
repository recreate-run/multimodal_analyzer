# Media Analyzer CLI - Test Suite

This test suite follows the **no mocking** requirement specified in the CLI implementation plan. All tests use real API calls to ensure accurate integration testing.

## Test Structure

## Running Tests

### Prerequisites

1. **Install dependencies:**

   ```bash
   uv sync
   ```

2. **Set up API keys:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Test Commands

```bash
# Run all tests
uv run pytest

# Run only unit tests (no API calls)
uv run pytest -m "not integration"

# Run only integration tests
uv run pytest -m integration

# Run tests excluding slow ones
uv run pytest -m "not slow"

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_models.py

# Run with verbose output
uv run pytest -v
```

## API Key Requirements

### For Image Analysis Tests

At least one of these API keys is required:

- `OPENAI_API_KEY` - For GPT-4V models
- `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` - For Azure OpenAI
- `GEMINI_API_KEY` or `GEMINI_API_KEY` - For Gemini models
- `ANTHROPIC_API_KEY` - For Claude models

### For Audio Analysis Tests

Required for audio transcription:

- `OPENAI_API_KEY` or `AZURE_OPENAI_API_KEY` - For Whisper models

latoi## Test Data

### Test Files Available

- **`data/speaker.jpg`** - Real image file for testing
- **`data/test_audio.mp3`** - Audio file for transcription tests
- **`data/test_video.mp4`** - Video file for audio extraction tests

## Test Design Principles

### Performance Considerations

- Use low concurrency settings to respect rate limits
- Batch tests marked as `@pytest.mark.slow`
- Small test files to minimize API usage
- Reasonable timeouts for API calls

### Debug Mode

```bash
# Run with debug logging
uv run pytest --log-cli-level=DEBUG

# Capture stdout/stderr
uv run pytest -s
```
