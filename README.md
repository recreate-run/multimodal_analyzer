# Media Analyzer CLI

AI-powered media analysis tool using multiple LLM providers through LiteLLM. Analyze images and audio files with customizable prompts and output formats.

## Features

- 🤖 **Multi-model Support**: Use Gemini, OpenAI, Claude, and more through LiteLLM
- 🖼️ **Image Analysis**: Analyze single images or process entire directories
- 🎵 **Audio Processing**: Transcribe audio files and analyze audio content
- ⚡ **Async Processing**: Concurrent analysis with configurable concurrency limits
- 📊 **Multiple Output Formats**: JSON, Markdown, and Text export
- 🎯 **Custom Prompts**: Use predefined or custom analysis prompts
- 📈 **Progress Tracking**: Real-time progress bars for batch operations
- 🔄 **Retry Logic**: Automatic retries with exponential backoff
- ⚙️ **Flexible Configuration**: Environment variables and YAML config support

## Quick Start

### Installation

**Option 1: Global CLI Installation (Recommended for users)**

```bash
# Install UV first (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install media-analyzer globally
uv tool install media-analyzer

# Use CLI directly anywhere
media-analyzer --help
```

**Option 2: Development Installation**

```bash
# Clone the repository
git clone <repository-url>
cd media-analyzer

# Install with uv (recommended for development)
uv sync

# Use with uv run prefix
uv run media-analyzer --help
```

### Basic Usage

```bash
# Set your API key (choose one)
export OPENAI_API_KEY="sk-your-key-here"
export GEMINI_API_KEY="your-google-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Analyze a single image (global installation)
media-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg

# Analyze with custom prompt and word count
media-analyzer --type image --model gpt-4o-mini --path image.png \
  --prompt "Describe the technical aspects of this image" --word-count 200

# Batch process a directory of images
media-analyzer --type image --model claude-3-sonnet-20240229 --path ./photos/ \
  --output markdown --output-file results.md --concurrency 3

# Transcribe audio file
media-analyzer --type audio --model whisper-1 --path audio.mp3 --audio-mode transcript

# Analyze audio content with description
media-analyzer --type audio --model gpt-4o-mini --path podcast.wav \
  --audio-mode description --prompt "Summarize the key points discussed"

# If using development installation, prefix with uv run:
# uv run media-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg
```

## Installation Methods

### Method 1: Global CLI Installation (Recommended)

Install the CLI globally and use it anywhere on your system:

```bash
# Install UV package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install media-analyzer CLI globally
uv tool install media-analyzer

# Verify installation
media-analyzer --version

# Use directly
media-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg
```

### Method 2: From Source (Development)

For development or when installing from source:

```bash
# Clone repository
git clone <repository-url>
cd media-analyzer

# Install with uv (creates isolated environment automatically)
uv sync

# Use with uv run prefix
uv run media-analyzer --help
```

### Method 3: Local Editable Installation

```bash
# Clone repository
git clone <repository-url>
cd media-analyzer

# Install locally with uv (editable mode)
uv sync

# Add to PATH or use uv run
uv run media-analyzer --help
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your API keys
OPENAI_API_KEY=sk-your-openai-key
GEMINI_API_KEY=your-google-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Optional settings
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_WORD_COUNT=100
MAX_CONCURRENCY=5
```

### YAML Configuration

For advanced configuration, copy and customize the YAML config:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` to set custom prompts, file size limits, and more.

## Usage Examples

### Single Image Analysis

```bash
# Basic image analysis
media-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg

# Save image analysis as markdown report
media-analyzer --type image --model gpt-4o-mini --path diagram.png \
  --output markdown --output-file analysis.md

# Custom prompt with specific word count
media-analyzer --type image --model claude-3-sonnet-20240229 --path chart.jpg \
  --prompt "Analyze this chart focusing on data insights" --word-count 300
```

### Batch Processing

````bash
# Process all images in a directory
media-analyzer --type image --model gemini/gemini-2.5-flash --path ./images/ \
  --output text --output-file results.txt

# Recursive directory processing with concurrency
media-analyzer --type image --model gpt-4o-mini --path ./dataset/ \
  --recursive --concurrency 5 --output json --output-file batch_results.json

# Process with progress tracking and custom settings
media-analyzer --type image --model gemini/gemini-2.5-flash --path ./photos/ \
  --word-count 150 --log-level INFO --concurrency 3

### Audio Processing

```bash
# Transcribe audio files
media-analyzer --type audio --model whisper-1 --path ./audio/ \
  --audio-mode transcript --output text --output-file transcripts.txt

# Analyze audio content with batch processing
media-analyzer --type audio --model gpt-4o-mini --path ./podcasts/ \
  --audio-mode description --recursive --concurrency 2 --word-count 200
````

### Output Formats

#### JSON Output

```bash
media-analyzer --type image --model gemini/gemini-2.5-flash --path image.jpg --output json
```

#### Markdown Report

```bash
media-analyzer --type image --model gpt-4o-mini --path image.jpg --output markdown
```

#### Text Output for Data Analysis

```bash
media-analyzer --type image --model claude-3-sonnet-20240229 --path ./images/ --output text
```

### Audio Analysis

#### Audio Transcription

```bash
# Transcribe a single audio file
media-analyzer --type audio --model whisper-1 --path recording.mp3 --audio-mode transcript

# Batch transcribe audio files
media-analyzer --type audio --model whisper-1 --path ./audio_files/ --audio-mode transcript --output text
```

#### Audio Content Analysis

```bash
# Analyze audio content with description
media-analyzer --type audio --model gpt-4o-mini --path podcast.wav --audio-mode description \
  --prompt "Summarize the main topics and key insights" --word-count 200

# Batch analyze audio with custom prompts
media-analyzer --type audio --model claude-3-sonnet-20240229 --path ./meetings/ \
  --audio-mode description --recursive --concurrency 2
```

## Supported Models

The tool supports any model available through [LiteLLM](https://docs.litellm.ai/docs/providers). Popular options include:

### OpenAI Models

**Vision Models:**

- `gpt-4o-mini` (recommended, cost-effective)
- `gpt-4o`
- `gpt-4-vision-preview`
- `gpt-4-turbo`

**Audio Models:**

- `whisper-1` (for transcription)
- `gpt-4o-mini` (for audio content analysis)
- `gpt-4o` (for audio content analysis)

### Google Models

- `gemini/gemini-2.5-flash` (recommended)
- `gemini/gemini-1.5-flash`
- `gemini/gemini-1.5-pro`
- `gemini/gemini-pro-vision`

### Anthropic Models

- `claude-3-sonnet-20240229`
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`

### Other Providers

- Azure OpenAI
- AWS Bedrock
- Cohere
- And many more through LiteLLM

## Command Line Options

```
Options:
  -t, --type [image|audio]        Analysis type: image or audio (required)
  -m, --model TEXT                LiteLLM model (required)
  -p, --path PATH                 Media file or directory path (required)
  --audio-mode [transcript|description] Audio analysis mode (required for audio type)
  -w, --word-count INTEGER        Target description word count [default: 100]
  --prompt TEXT                   Custom analysis prompt
  -o, --output [json|markdown|text] Output format [default: json]
  --output-file TEXT              Save results to file
  -r, --recursive                 Process directories recursively
  -c, --concurrency INTEGER       Concurrent requests [default: 3]
  --log-level [DEBUG|INFO|WARNING|ERROR] Logging level [default: INFO]
  -v, --verbose                   Show detailed output including model info
  --version                       Show version and exit
  --help                          Show help and exit
```

## Development

This project follows strict development standards outlined in the [Development Guidelines](#development-guidelines) section above. Please review those principles before contributing.

### Running Tests

**Important**: All tests require valid API keys. Tests will fail immediately if API keys are missing - this is intentional to ensure test coverage accuracy.

```bash
# Set up API keys first (required)
export OPENAI_API_KEY="sk-your-key-here"
export GEMINI_API_KEY="your-google-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Run all tests (will fail fast if API keys missing)
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_cli.py -v

# Run integration tests specifically
uv run pytest -m integration -v
```

### Code Quality

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src/

# Run all quality checks
uv run pytest && uv run black . && uv run ruff check . && uv run mypy src/
```

### Adding Dependencies

```bash
# Add runtime dependency
uv add pillow

# Add development dependency
uv add --dev pytest-mock

# Update all dependencies
uv sync
```

## Development Guidelines

This project follows strict development principles prioritizing reliability and explicit error handling over graceful degradation.

### Core Principles

1. **Fail Fast Philosophy**

   - No graceful degradation when components malfunction
   - Raise exceptions immediately for any error condition
   - Better to fail explicitly than continue with broken functionality

2. **Strict Testing Standards**

   - Never skip tests due to missing dependencies or API keys
   - All tests must execute with real integrations when possible
   - Raise clear exceptions if required API keys are missing
   - Integration tests are mandatory, not optional

3. **Explicit Error Handling**
   - Use exceptions for all error conditions
   - No silent failures or try/except blocks that continue on error
   - API key validation must raise descriptive exceptions
   - File system errors should immediately abort operations

### Error Handling Rules

```python
# ✅ Good: Explicit failure
def analyze_image(api_key: str, image_path: Path):
    if not api_key:
        raise ValueError("API key is required for image analysis")
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    # Continue with analysis...

# ❌ Bad: Silent degradation
def analyze_image(api_key: str, image_path: Path):
    if not api_key:
        logger.warning("No API key provided, skipping analysis")
        return None  # Silent failure
```

### Testing Philosophy

```python
# ✅ Good: Fail if API key missing
def test_image_analysis():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.fail("OPENAI_API_KEY required for integration tests")
    # Run real test...

# ❌ Bad: Skip test
def test_image_analysis():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("No API key available")  # Hides test coverage gaps
```

### Component Reliability

- **Configuration**: Fail immediately if required config is missing
- **API Clients**: Raise exceptions on authentication or connection failures
- **File Operations**: Abort on any file system errors
- **Model Loading**: Fail fast if models are unavailable or incompatible

This approach ensures that:

- Issues are discovered early in development
- Production deployments are more reliable
- Test coverage accurately reflects real usage scenarios
- Debugging is easier with explicit error messages

## Examples

See the `examples/` directory for:

- **`sample_usage.py`**: Comprehensive programmatic usage examples
- Different analysis scenarios and configuration options
- Batch processing examples with progress tracking

Run the examples:

```bash
uv run python examples/sample_usage.py
```

## Troubleshooting

This project follows a **fail-fast philosophy**. When errors occur, the application will immediately terminate with clear error messages rather than attempting graceful recovery.

### Common Issues

1. **API Key Errors**

   **Expected Behavior**: Application fails immediately with descriptive error message.

   ```bash
   # Verify API keys are properly set
   echo $OPENAI_API_KEY
   echo $GEMINI_API_KEY
   echo $ANTHROPIC_API_KEY

   # Expected error if missing:
   # ValueError: API key is required for model 'gpt-4o'
   ```

2. **Model Not Found**

   **Expected Behavior**: Immediate failure with specific model name.

   ```bash
   # Check LiteLLM documentation for correct model names
   # https://docs.litellm.ai/docs/providers

   # Example error:
   # litellm.exceptions.NotFoundError: Model 'invalid-model' not found
   ```

3. **Media Format Issues**

   **Expected Behavior**: File validation fails immediately before API calls.

   ```bash
   # Supported image formats: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp
   # Supported audio formats: .mp3, .wav, .m4a, .flac, .ogg
   # Image size limits (default: 10MB), Audio size limits (default: 100MB)

   # Example errors:
   # FileNotFoundError: Media file not found: /path/to/missing.jpg
   # ValueError: File size exceeds 10MB limit: large_image.png
   # ValueError: Audio file exceeds 100MB limit: long_recording.wav
   # ValueError: Unsupported format: .txt
   ```

4. **Audio-Specific Errors**

   **Expected Behavior**: Audio mode validation and transcription failures.

   ```bash
   # Example errors:
   # ClickException: --audio-mode is required when --type is 'audio'
   # ClickException: --audio-mode should not be used when --type is 'image'
   # ValueError: Invalid audio file: corrupted.mp3
   ```

5. **Import Errors**

   **Expected Behavior**: Module import failures prevent startup.

   ```bash
   # Make sure you're using uv run or have activated the virtual environment
   uv run media-analyzer --help

   # Expected error if not properly installed:
   # ModuleNotFoundError: No module named 'media_analyzer_cli'
   ```

### Error Philosophy

Unlike many applications that attempt to gracefully handle errors, this tool is designed to:

- **Fail immediately** when dependencies are missing
- **Reject invalid inputs** before processing begins
- **Abort operations** on any component failure
- **Provide explicit error messages** for all failure modes

This approach ensures that issues are discovered early and fixed properly rather than masked by fallback behavior.

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
media-analyzer --type image --model gemini/gemini-2.5-flash --path image.jpg --log-level DEBUG
```

## Performance

### Benchmarks

- **Single Image**: < 5 seconds typical response time
- **Batch Processing**: ~100 images in 3-5 minutes (concurrency=5)
- **Memory Usage**: < 500MB for large batch operations

### Optimization Tips

1. **Adjust Concurrency**: Start with 3-5, increase based on API limits
2. **File Size**: Optimize images to under 5MB for faster processing
3. **Batch Size**: Process 50-100 images per batch for optimal performance

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest`
5. Submit a pull request

## Changelog

### v0.1.0

- Initial release
- Multi-model support via LiteLLM
- Batch processing with concurrency
- Multiple output formats (JSON, Markdown, CSV)
- Progress tracking with tqdm
- Comprehensive error handling and retries
- Modern UV package management
