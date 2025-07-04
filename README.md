# Media Analyzer CLI

AI-powered media analysis tool using multiple LLM providers through LiteLLM. Analyze images, audio, and video files with customizable prompts and output formats.

## Features

- **Multi-model Support**: Use Gemini, OpenAI, Claude, and more through LiteLLM
- **Image, Audio & Video Analysis**: Single files or batch process entire directories
- **Concurrent Processing**: Configurable concurrency with progress tracking
- **Multiple Output Formats**: JSON, Markdown, and Text export
- **Custom Prompts**: Flexible analysis with custom or predefined prompts

## Installation

**Global Installation (Recommended)**

```bash
# Install media-analyzer globally
uv tool install media-analyzer
```

**Development Installation**

```bash
git clone <repository-url>
cd media-analyzer
uv sync
```

## Usage

### Basic Commands

```bash
# Analyze single image
media-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg

# Batch process directory
media-analyzer --type image --model gpt-4o-mini --path ./photos/ --output markdown

# Transcribe audio
media-analyzer --type audio --model whisper-1 --path audio.mp3 --audio-mode transcript

# Analyze audio content
media-analyzer --type audio --model gpt-4o-mini --path podcast.wav --audio-mode description

# Analyze video content (Gemini only)
media-analyzer --type video --model gemini/gemini-2.5-flash --path video.mp4 --video-mode description

# Development installation (prefix with uv run)
uv run media-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg
```

## Configuration

Set your API keys via environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key" 
export GEMINI_API_KEY="your-gemini-key"
```

Optional configuration via environment variables:

```bash
# Video analysis settings
export MAX_VIDEO_SIZE_MB=2048        # Maximum video file size (default: 2048MB)

# General settings
export MAX_CONCURRENCY=5             # Maximum concurrent requests (default: 5)
export TIMEOUT_SECONDS=30            # Request timeout (default: 30)
```

## Examples

### Image Analysis

```bash
# Custom prompt with word count
media-analyzer --type image --model claude-3-sonnet-20240229 --path chart.jpg \
  --prompt "Analyze this chart focusing on data insights" --word-count 300

# Recursive batch processing
media-analyzer --type image --model gpt-4o-mini --path ./dataset/ \
  --recursive --concurrency 5 --output json --output-file results.json
```

### Audio Processing

```bash
# Batch transcription
media-analyzer --type audio --model whisper-1 --path ./audio/ \
  --audio-mode transcript --output text --output-file transcripts.txt

# Content analysis with custom prompts
media-analyzer --type audio --model gpt-4o-mini --path podcast.wav \
  --audio-mode description --prompt "Summarize key insights" --word-count 200
```

### Video Analysis

```bash
# Single video analysis
media-analyzer --type video --model gemini/gemini-2.5-flash --path presentation.mp4 \
  --video-mode description --word-count 150

# Batch video processing with custom prompts
media-analyzer --type video --model gemini/gemini-2.5-flash --path ./videos/ \
  --video-mode description --prompt "Describe the visual content and any audio" \
  --recursive --output markdown --output-file video_analysis.md

# Video analysis with detailed output
media-analyzer --type video --model gemini/gemini-2.5-flash --path tutorial.mp4 \
  --video-mode description --verbose --word-count 200
```

## Models

Supports any model available through [LiteLLM](https://docs.litellm.ai/docs/providers).

**Video Analysis**: Currently restricted to Gemini models only due to native multimodal video support.

## Command Line Options

```
Options:
  -t, --type [image|audio|video]  Analysis type: image, audio, or video (required)
  -m, --model TEXT                LiteLLM model (required)
  -p, --path PATH                 Media file or directory path (required)
  --audio-mode [transcript|description] Audio analysis mode (required for audio type)
  --video-mode [description]      Video analysis mode (required for video type)
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

### Running Tests

**Important**: All tests require valid API keys and fail immediately if missing.


# Run tests
uv run pytest
uv run pytest --cov  # with coverage
```

### Development Philosophy

- **Fail Fast**: Raise exceptions immediately rather than graceful degradation
- **Explicit Testing**: Never skip tests due to missing API keys - fail instead
- **Clear Errors**: All error conditions must raise descriptive exceptions

## Examples

See the `examples/` directory for:

- **`sample_usage.py`**: Comprehensive programmatic usage examples
- Different analysis scenarios and configuration options
- Batch processing examples with progress tracking

Run the examples:

```bash
uv run python examples/sample_usage.py
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
media-analyzer --type image --model gemini/gemini-2.5-flash --path image.jpg --log-level DEBUG
```
