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
# Install multimodal-analyzer globally
uv build
uv tool install multimodal-analyzer
```

**Development Installation**

```bash
git clone <repository-url>
cd multimodal-analyzer
uv sync
```

## Image Analysis Usage

### Basic Image Commands

```bash
# Analyze single image
multimodal-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg

# Batch process directory
multimodal-analyzer --type image --model gpt-4o-mini --path ./photos/ --output markdown

# Development installation (prefix with uv run)
uv run multimodal-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg
```

### Advanced Image Analysis

```bash
# Custom prompt with word count
multimodal-analyzer --type image --model claude-3-sonnet-20240229 --path chart.jpg \
  --prompt "Analyze this chart focusing on data insights" --word-count 300

# Recursive batch processing
multimodal-analyzer --type image --model gpt-4o-mini --path ./dataset/ \
  --recursive --concurrency 5 --output json --output-file results.json
```

## Audio Analysis Usage

### Basic Audio Commands

```bash
# Transcribe audio
multimodal-analyzer --type audio --model whisper-1 --path audio.mp3 --audio-mode transcript

# Analyze audio content
multimodal-analyzer --type audio --model gpt-4o-mini --path podcast.wav --audio-mode description
```

### Advanced Audio Processing

```bash
# Batch transcription
multimodal-analyzer --type audio --model whisper-1 --path ./audio/ \
  --audio-mode transcript --output text --output-file transcripts.txt

# Content analysis with custom prompts
multimodal-analyzer --type audio --model gpt-4o-mini --path podcast.wav \
  --audio-mode description --prompt "Summarize key insights" --word-count 200
```

## Video Analysis Usage

**Note**: Video analysis is currently restricted to Gemini models only due to native multimodal video support.

### Basic Video Commands

```bash
# Analyze video content (Gemini only)
multimodal-analyzer --type video --model gemini/gemini-2.5-flash --path video.mp4 --video-mode description
```

### Advanced Video Analysis

```bash
# Single video analysis
multimodal-analyzer --type video --model gemini/gemini-2.5-flash --path presentation.mp4 \
  --video-mode description --word-count 150

# Batch video processing with custom prompts
multimodal-analyzer --type video --model gemini/gemini-2.5-flash --path ./videos/ \
  --video-mode description --prompt "Describe the visual content and any audio" \
  --recursive --output markdown --output-file video_analysis.md

# Video analysis with detailed output
multimodal-analyzer --type video --model gemini/gemini-2.5-flash --path tutorial.mp4 \
  --video-mode description --verbose --word-count 200
```

## Models

Supports any model available through [LiteLLM](https://docs.litellm.ai/docs/providers).


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
multimodal-analyzer --type image --model gemini/gemini-2.5-flash --path image.jpg --log-level DEBUG
```
