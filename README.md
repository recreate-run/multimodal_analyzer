# Multimodal Analyzer CLI

AI-powered media analysis tool using multiple LLM providers through LiteLLM. Analyze images, audio, and video files with customizable prompts and output formats.

## Features

- **Multi-model Support**: Use Gemini, OpenAI, Claude, and more through LiteLLM
- **Image, Audio & Video Analysis**: Single files or batch process entire directories
- **Streaming JSON Input**: Multi-turn conversations via stdin JSONL for interactive analysis
- **Hybrid File Input**: Specify files by directory path OR explicit file lists from multiple locations
- **Automatic Image Preprocessing**: Images > 500KB are automatically converted to JPEG for optimal processing
- **Concurrent Processing**: Configurable concurrency with progress tracking
- **Multiple Output Formats**: JSON, Markdown, Text, and streaming JSON export
- **Custom Prompts**: Flexible analysis with custom or predefined prompts

## Installation

### Prerequisites

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install from Source (Recommended for Users)

To install and use the tool system-wide:

```bash
# Clone the repository
git clone https://github.com/sarath-menon/multimodal-analyzer.git
cd multimodal-analyzer

# Install globally with uv
uv tool install .
```

After installation, the `multimodal-analyzer` command will be available system-wide.

### Development Setup

For development and contributing:

```bash
# Clone the repository
git clone https://github.com/sarath-menon/multimodal-analyzer.git
cd multimodal-analyzer

# Install dependencies
uv sync

# Run commands with uv run prefix
uv run multimodal-analyzer --help
```

### Verify Installation

```bash
# Check if installation worked
multimodal-analyzer --version

# Or for development setup
uv run multimodal-analyzer --version
```

### Reinstalling

To update or reinstall:

```bash
cd multimodal-analyzer
git pull
uv tool install --force-reinstall .
```

## Hybrid File Input Support

The Multimodal Analyzer CLI supports two flexible input modes:

### Directory Path Mode (`--path`)

Use `--path` to analyze files from directories or single files:

```bash
# Single file
multimodal-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg

# Directory (all supported files)
multimodal-analyzer --type image --model gemini/gemini-2.5-flash --path ./photos/

# Recursive directory scan
multimodal-analyzer --type image --model gemini/gemini-2.5-flash --path ./dataset/ --recursive
```

### Explicit File List Mode (`--files`)

Use `--files` to specify exact files from multiple locations:

```bash
# Multiple files from different directories
multimodal-analyzer --type image --model gemini/gemini-2.5-flash \
  --files /home/user/photo1.jpg \
  --files /work/project/chart.png \
  --files ./local/screenshot.jpg

# Audio files from various locations
multimodal-analyzer --type audio --model gemini/gemini-2.5-flash \
  --files recording1.mp3 \
  --files /meetings/call.wav \
  --audio-mode transcript
```

### When to Use Each Mode

- **Use `--path`** for processing all files in a directory or subdirectories
- **Use `--files`** for selective processing of specific files from multiple locations
- **Cannot use both** `--path` and `--files` simultaneously (mutually exclusive)

## Image Analysis Usage

### Basic Image Commands

```bash
# Analyze single image
multimodal-analyzer --type image --model gemini/gemini-2.5-flash --path photo.jpg

# Batch process directory
multimodal-analyzer --type image --model azure/gpt-4.1-mini --path ./photos/ --output markdown

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

# Analyze specific images from multiple directories
multimodal-analyzer --type image --model gpt-4o-mini \
  --files ./screenshots/chart1.png \
  --files ./photos/diagram.jpg \
  --files /tmp/analysis_image.png \
  --prompt "Compare these visuals" --word-count 200
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

# Transcribe specific audio files from different locations
multimodal-analyzer --type audio --model whisper-1 \
  --files ./meetings/standup.mp3 \
  --files ./interviews/candidate1.wav \
  --files /recordings/conference_call.m4a \
  --audio-mode transcript --output markdown --output-file transcripts.md
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

# Analyze specific videos from multiple projects
multimodal-analyzer --type video --model gemini/gemini-2.5-flash \
  --files ./project1/demo.mp4 \
  --files ./project2/presentation.avi \
  --files /shared/training_video.mov \
  --video-mode description --prompt "Focus on key features demonstrated" \
  --word-count 300 --output json --output-file video_summaries.json
```

## Streaming JSON Input

Enable interactive, multi-turn conversations by providing JSON messages via stdin. Each line of input is a complete JSON message in JSONL format, allowing continuous analysis without re-launching the CLI.

### Basic Streaming Usage

```bash
# Start streaming mode for image analysis
echo '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"Explain this image"},{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,..."}}]}}' | \
  multimodal-analyzer --type image --model gemini/gemini-2.5-flash -p . --input-format stream-json --output stream-json
```

### Streaming Requirements

- **Required flags**: `--input-format stream-json` + `--output stream-json` + `-p`
- **Incompatible with**: `--files`, `--output-file`, batch processing options
- **Current support**: Image analysis only (audio/video coming soon)

### Message Format

**Input Message Structure:**

```json
{
  "type": "user",
  "message": {
    "role": "user", 
    "content": [
      {"type": "text", "text": "Describe this image"},
      {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<base64-data>"}}
    ]
  }
}
```

**Response Format:**

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": "AI analysis response..."
  },
  "metadata": {
    "success": true,
    "model": "gemini/gemini-2.5-flash"
  }
}
```

### Interactive Usage Examples

```bash
# Multi-turn conversation with different images
cat input.jsonl | multimodal-analyzer --type image --model gemini/gemini-2.5-flash -p . --input-format stream-json --output stream-json

# Real-time processing with custom prompts
echo '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"What colors do you see?"},{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,..."}}]}}' | \
  multimodal-analyzer --type image --model gpt-4o-mini -p . --input-format stream-json --output stream-json --word-count 50
```

## Models

Supports any model available through [LiteLLM](https://docs.litellm.ai/docs/providers).

## Command Line Options

```
Options:
  -t, --type [image|audio|video]  Analysis type: image, audio, or video (required)
  -m, --model TEXT                LiteLLM model (required)
  -p, --path PATH                 Media file or directory path (mutually exclusive with --files)
  -f, --files TEXT                Explicit list of media files to analyze (mutually exclusive with --path)
  --audio-mode [transcript|description] Audio analysis mode (required for audio type)
  --video-mode [description]      Video analysis mode (required for video type)
  -w, --word-count INTEGER        Target description word count [default: 100]
  --prompt TEXT                   Custom analysis prompt
  -o, --output [json|markdown|text|stream-json] Output format [default: json]
  --input-format [stream-json]    Input format for streaming mode (requires --output stream-json and -p)
  --output-file TEXT              Save results to file
  -r, --recursive                 Process directories recursively (only with --path)
  -c, --concurrency INTEGER       Concurrent requests [default: 3]
  --log-level [DEBUG|INFO|WARNING|ERROR] Logging level [default: INFO]
  -v, --verbose                   Show detailed output including model info
  --version                       Show version and exit
  --help                          Show help and exit
```

**Standard Mode**: You must specify either `--path` OR `--files`, but not both. Use `--path` for directory processing and `--files` for explicit file lists.

**Streaming Mode**: Requires `--input-format stream-json`, `--output stream-json`, and `-p`. Cannot be used with `--files` or `--output-file`.

## Output Schema

### JSON Output Format (Batch Mode)

Results are returned as an array of objects, one per analyzed file:

```json
[
  {
    "image_path": "path/to/image.jpg",
    "analysis": "AI-generated analysis text...",
    "success": true
  }
]
```

### Streaming JSON Output Format

Each response is a single JSON object written immediately to stdout:

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": "AI-generated analysis text..."
  },
  "metadata": {
    "success": true,
    "model": "gemini/gemini-2.5-flash"
  }
}
```

### Error Handling

**Batch Mode** - Failed analyses include error details:

```json
[
  {
    "image_path": "path/to/image.jpg",
    "analysis": null,
    "success": false,
    "error": "Error message"
  }
]
```

**Streaming Mode** - Errors are returned as immediate JSON responses:

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": ""
  },
  "metadata": {
    "success": false,
    "model": "gemini/gemini-2.5-flash",
    "error": "Error message"
  }
}
```

## Authentication

### Google OAuth

For Gemini models, you can use OAuth authentication instead of API keys:

```bash
# Authenticate with Google OAuth
multimodal-analyzer auth login

# Check authentication status
multimodal-analyzer auth status

# Clear stored credentials
multimodal-analyzer auth logout
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
