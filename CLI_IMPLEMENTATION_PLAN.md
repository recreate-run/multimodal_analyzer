# Media Analyzer CLI - Implementation Plan

## Project Overview

A command-line tool for analyzing images using multiple AI models through LiteLLM (unified interface for Gemini, OpenAI, Anthropic, etc.) with customizable prompts and output configurations.

### Core Features

- Multi-model support via LiteLLM (Gemini, OpenAI, Claude, and more)
- Single image or batch folder processing
- Customizable description word count
- Custom prompt support with default fallback
- Output formats: JSON, Markdown, CSV
- Progress tracking for batch operations with async processing
- Comprehensive error handling with Loguru logging
- Modern UV package management following best practices

## Project Setup (Following Simon Willison's Workflow)

### 1. Initial Project Creation

```bash
# Option 1: Use cookiecutter template for best practices
uvx cookiecutter gh:simonw/click-app
# Answer prompts:
#   app_name: media-analyzer
#   description: AI-powered image analysis tool
#   hyphenated: media-analyzer
#   underscored: media_analyzer

# Option 2: Manual setup (if customizing structure)
mkdir media-analyzer && cd media-analyzer
```

### 2. Modern pyproject.toml Configuration

```toml
[project]
name = "media-analyzer"
version = "0.1.0"
description = "AI-powered image analysis tool using multiple LLM providers"
readme = "README.md"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
requires-python = ">=3.10"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "click>=8.1.0",           # CLI framework
    "pillow>=10.0.0",         # Image processing
    "litellm>=1.72.2",        # Unified LLM interface
    "aiofiles>=24.0.0",       # Async file I/O
    "python-dotenv>=1.0.0",   # Environment management
    "pyyaml>=6.0.0",          # Config files
    "tenacity>=8.0.0",        # Retry logic
    "tqdm>=4.66.0",           # Progress bars
    "loguru>=0.7.2",          # Advanced logging
    "pandas>=2.0.0",          # CSV export
    "rich>=13.0.0",           # Terminal formatting
    "nest-asyncio>=1.6.0",    # Nested async support
]

# CRITICAL: Build system required for CLI script installation
[build-system]
requires = ["setuptools>=64", "wheel"]
build-backend = "setuptools.build_meta"

# CLI entry point - enables 'uv run media-analyzer'
[project.scripts]
media-analyzer = "media_analyzer_cli.cli:main"

# Project URLs
[project.urls]
Homepage = "https://github.com/yourusername/media-analyzer"
Repository = "https://github.com/yourusername/media-analyzer"
Issues = "https://github.com/yourusername/media-analyzer/issues"

# Modern uv dev dependencies (PEP 735)
[tool.uv]
dev-dependencies = [
    "pytest>=8.4.0",
    "pytest-asyncio>=1.0.0",
    "pytest-cov>=4.0.0",
    "black>=24.0.0",
    "ruff>=0.4.0",
    "mypy>=1.0.0",
    "types-pillow>=10.0.0",
    "types-pyyaml>=6.0.0",
]

# Alternative legacy format (if PEP 735 not available)
[project.optional-dependencies]
dev = [
    "pytest>=8.4.0",
    "pytest-asyncio>=1.0.0",
    "pytest-cov>=4.0.0",
    "black>=24.0.0",
    "ruff>=0.4.0",
    "mypy>=1.0.0",
    "types-pillow>=10.0.0",
    "types-pyyaml>=6.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--cov=media_analyzer --cov-report=term-missing"

[tool.black]
line-length = 88
target-version = ['py310']

[tool.ruff]
target-version = "py310"
line-length = 88
select = ["E", "F", "I", "N", "UP", "S", "B", "A", "C4", "ICN", "PIE", "T20", "Q"]
ignore = ["S101"]  # Allow assert statements in tests

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Modern UV Development Workflow

### Project Setup (One Command)

```bash
cd media-analyzer

# Install all dependencies including dev tools
uv sync

# That's it! No need to activate virtual environments
```

### Daily Development Commands

```bash
# Run the CLI tool directly
uv run media-analyzer --help

# Alternative: run as module
uv run python -m media_analyzer --help

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src/

# Run all quality checks together
uv run pytest && uv run black . && uv run ruff check . && uv run mypy src/
```

### Adding Dependencies

```bash
# Add runtime dependency
uv add pillow

# Add dev dependency (if using optional-dependencies)
uv add --dev pytest-mock

# Add dev dependency (if using tool.uv.dev-dependencies)
# Edit pyproject.toml and run:
uv sync
```

## Architecture Design

### Component Structure

```
media-analyzer/
├── src/
│   └── media_analyzer/          # Note: underscored package name
│       ├── __init__.py
│       ├── cli.py                   # Main CLI entry point
│       ├── analyzer.py              # Core image analysis logic
│       ├── models/
│       │   ├── __init__.py
│       │   └── litellm_model.py     # Unified LiteLLM implementation
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── image.py             # Image processing utilities
│       │   ├── output.py            # Output formatting
│       │   └── prompts.py           # Prompt management
│       └── config.py                # Configuration management
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_analyzer.py
│   └── test_models.py
├── examples/
│   └── sample_usage.py
├── .env.example
├── .gitignore
├── pyproject.toml                   # Modern UV configuration
├── README.md
└── uv.lock                         # Auto-generated lockfile
```

## Component Implementation Details

### 1. CLI Interface (`cli.py`)

```python
import click
from typing import Optional
from pathlib import Path
import asyncio
from loguru import logger

from .analyzer import ImageAnalyzer
from .config import Config

@click.command()
@click.option('--model', '-m', required=True,
              help='LiteLLM model (e.g., gemini/gemini-1.5-flash, gpt-4o)')
@click.option('--path', '-p', required=True, type=click.Path(exists=True),
              help='Image file or directory path')
@click.option('--word-count', '-w', default=100,
              help='Target description word count')
@click.option('--prompt', help='Custom analysis prompt')
@click.option('--output', '-o', type=click.Choice(['json', 'markdown', 'csv']),
              default='json', help='Output format')
@click.option('--output-file', help='Save results to file')
@click.option('--recursive', '-r', is_flag=True,
              help='Process directories recursively')
@click.option('--concurrency', '-c', default=3,
              help='Concurrent requests for batch processing')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default='INFO', help='Logging level')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed output including model, prompt, and metadata')
@click.version_option()
def main(model: str, path: str, word_count: int, prompt: Optional[str],
         output: str, output_file: Optional[str], recursive: bool,
         concurrency: int, log_level: str, verbose: bool) -> None:
    """AI-powered image analysis tool using multiple LLM providers."""

    # Configure logging
    logger.remove()
    logger.add(lambda msg: click.echo(msg, err=True), level=log_level)

    # Load configuration
    config = Config.load()

    # Create analyzer
    analyzer = ImageAnalyzer(config)

    # Run analysis
    try:
        result = asyncio.run(analyzer.analyze(
            model=model,
            path=Path(path),
            word_count=word_count,
            prompt=prompt,
            output_format=output,
            output_file=output_file,
            recursive=recursive,
            concurrency=concurrency,
            verbose=verbose
        ))

        if not output_file:
            click.echo(result)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise click.ClickException(str(e))

if __name__ == "__main__":
    main()
```

### 2. Simplified Development Workflow

**No Virtual Environment Activation Needed**

- `uv run` handles virtual environment automatically
- No more `source .venv/bin/activate` or `conda activate`
- Works consistently across different shells and systems

**One-Step Dependency Management**

```bash
# Install everything needed for development
uv sync

# Add new dependency and install immediately
uv add requests
```

**Immediate CLI Testing**

```bash
# Test the CLI immediately after uv sync
uv run media-analyzer --help

# No need for pip install -e . or setup.py develop
```

## Implementation Phases (Streamlined)

### Phase 1: Project Foundation

- [x] **Project Setup**: Use cookiecutter or manual setup with proper pyproject.toml
- [x] **UV Configuration**: Ensure build-system and scripts sections are correct
- [x] **Basic CLI**: Click-based command structure with entry point
- [x] **Configuration**: Environment and YAML config loading
- [x] **Verify Setup**: Ensure `uv run media-analyzer --help` works

### Phase 2: Core Functionality

- [x] **LiteLLM Integration**: Unified model interface
- [x] **Image Processing**: PIL-based validation and encoding
- [x] **Basic Analysis**: Single image processing
- [x] **Error Handling**: Retry logic and user-friendly errors
- [x] **Testing Setup**: Basic test structure with `uv run pytest`

### Phase 3: Advanced Features

- [x] **Async Processing**: Batch operations with concurrency
- [x] **Output Formats**: JSON, Markdown, CSV exporters
- [x] **Progress Tracking**: tqdm integration for batch operations
- [x] **Advanced Config**: YAML configuration files
- [x] **Comprehensive Testing**: Full test coverage

### Phase 4: Polish & Documentation

- [x] **Documentation**: README with usage examples
- [x] **Type Hints**: Complete mypy compliance
- [x] **Code Quality**: Black formatting, Ruff linting
- [x] **Examples**: Sample scripts and use cases
- [x] **Performance**: Benchmarking and optimization

### Phase 5: Verbose Output Enhancement

- [x] **Add Verbose Flag to CLI**: Add `--verbose` flag to CLI interface in `cli.py`
- [x] **Update Output Formatting**: Modify output formatters in `utils/output.py` to support verbose mode
- [x] **Update Analyzer for Verbose Mode**: Pass verbose parameter through analysis pipeline
- [x] **Update Documentation and Examples**: Add verbose flag usage to documentation and examples

#### Verbose Output Implementation Details

**Verbose Mode (--verbose or -v flag set):**

- **Output includes**: Full details with image path, model name, prompt used, analysis result, and metadata
- **Use case**: Development, debugging, and detailed analysis workflows
- **All formats**: JSON, Markdown, and Text formats include complete information

**Non-Verbose Mode (default when --verbose not set):**

- **Output includes**: Only image path and analysis result content
- **Use case**: Clean integration into other workflows, batch processing with minimal output
- **All formats**: JSON, Markdown, and Text formats show streamlined results

**Implementation Requirements:**

- Modify CLI interface to accept `--verbose/-v` flag
- Update output formatters to conditionally include metadata based on verbose parameter
- Ensure consistent behavior across all output formats (JSON, Markdown, CSV/Text)
- Pass verbose parameter through the entire analysis pipeline

## Quick Start Guide

### For Users

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo-url>
cd media-analyzer

# One command setup
uv sync

# Start using immediately
uv run media-analyzer --model gemini/gemini-1.5-flash --path photo.jpg
```

### For Contributors

```bash
# Setup development environment
uv sync

# Run tests
uv run pytest

# Check code quality
uv run black . && uv run ruff check . && uv run mypy src/

# Try the CLI
uv run media-analyzer --help
```

## Example Usage Patterns

### Single Image Analysis

```bash
# Basic usage
uv run media-analyzer --model gemini/gemini-1.5-flash --path ./photo.jpg

# With custom prompt and word count
uv run media-analyzer --model gpt-4o --path ./diagram.png \
  --prompt "Explain this technical diagram" --word-count 200

# Save as markdown report
uv run media-analyzer --model claude-3-sonnet-20240229 --path ./chart.jpg \
  --output markdown --output-file analysis.md
```

### Batch Processing

```bash
# Process folder with concurrency
uv run media-analyzer --model gemini/gemini-1.5-flash --path ./photos/ \
  --concurrency 5 --output csv --output-file results.csv

# Recursive directory processing
uv run media-analyzer --model gpt-4-vision-preview --path ./dataset/ \
  --recursive --word-count 150 --output json --output-file batch_results.json
```

### Advanced Configuration

```bash
# Using environment variables
OPENAI_API_KEY=sk-xxx uv run media-analyzer --model gpt-4o --path ./image.jpg

# Debug mode with detailed logging
uv run media-analyzer --model gemini/gemini-1.5-flash --path ./photo.jpg \
  --log-level DEBUG

# Verbose output with full details
uv run media-analyzer --model gpt-4o --path ./image.jpg --verbose

# Non-verbose output (clean, minimal)
uv run media-analyzer --model gpt-4o --path ./image.jpg
```

## Key Benefits of This Approach

1. **Modern Tooling**: Leverages latest uv best practices
2. **Zero Friction**: No virtual environment management needed
3. **Immediate Productivity**: `uv sync` and start coding
4. **Reproducible Builds**: uv.lock ensures consistent dependencies
5. **Professional Structure**: Follows established Python packaging standards
6. **Easy Distribution**: Proper build system enables publishing to PyPI

## Success Metrics

### Performance Targets

- Project setup: < 30 seconds with `uv sync`
- Single image analysis: < 5 seconds
- Batch of 100 images: < 5 minutes with concurrency
- Memory usage: < 500MB for 1000 images

### Developer Experience

- Zero-config development environment
- One-command testing and quality checks
- Clear error messages and helpful CLI help
- Comprehensive documentation with examples

### Phase 6: Audio Analysis Support

- [x] **CLI Interface Updates**: Add required `--type` parameter (image/audio) and `--audio-mode` parameter (transcript/description)
- [x] **Remove Backward Compatibility**: Require explicit type specification, raise error if not provided
- [x] **Audio Processing**: Add support for audio files and video-to-audio extraction using ffmpeg
- [x] **Environment Variables**: Support AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, GEMINI_API_KEY
- [x] **Audio Analysis Modes**: Implement transcript (raw transcription) and description (AI analysis of content)
- [x] **Output Formats**: Extend JSON, Markdown, and plain text formats for audio results
- [x] **Testing**: Add comprehensive tests without mocking, using real API calls
- [x] **Dependencies**: Add ffmpeg-python and pydub for audio/video processing

#### Audio Analysis Implementation Details

**Analysis Types (--type parameter, required):**

- `image`: Analyze image files (existing functionality)
- `audio`: Analyze audio files or extract audio from video files

**Audio Modes (--audio-mode parameter, required when type=audio):**

- `transcript`: Return raw transcription text using Whisper models
- `description`: Analyze transcribed content and provide AI-generated description/summary

**Supported Formats:**

- Audio: mp3, wav, m4a, flac, ogg
- Video: mp4, avi, mov, mkv (audio will be extracted)

**Environment Variables:**

- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `AZURE_OPENAI_KEY`: Azure OpenAI API key
- `GEMINI_API_KEY`: Google Gemini API key

**Breaking Changes:**

- Remove all backward compatibility
- `--type` parameter is now required for all operations
- Raise clear error if analysis type is not specified

**Audio Processing Workflow:**

1. Detect file type (audio vs video)
2. If video: extract audio to temporary file
3. If transcript mode: use Whisper via LiteLLM for transcription
4. If description mode: transcribe first, then analyze with specified LLM model
5. Format output in requested format (JSON, Markdown, plain text)

This modernized approach follows Simon Willison's proven uv workflow patterns while maintaining the robust architecture needed for a production-quality media analysis tool supporting both image and audio content.
