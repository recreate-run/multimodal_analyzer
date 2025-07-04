# Video Analysis Implementation Plan

## 1 Task Overview

| Field            | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| **Task Name**    | Add Video Analysis Support to Media Analyzer CLI                |
| **Description**  | Extend the existing media analyzer to support video analysis using Gemini models, leveraging their native multimodal capabilities for video understanding. This enables users to analyze video content with description mode and optional custom prompts. |
| **Dependencies** | None (extends existing image/audio analysis architecture)        |

---

## 2 Implementation Steps & Todo Lists

### 1. Create Video Utilities Module

- **Files:** `src/media_analyzer_cli/utils/video.py` (create)
- **Details:** Build video processing utilities for file discovery, validation, and metadata extraction using ffmpeg.
- **Tests:** `tests/test_utils.py` (modify) - extend existing utils tests with video functionality
- **Verification:** `uv run pytest tests/test_utils.py -k video`

**Todo**
- [ ] Create `src/media_analyzer_cli/utils/video.py`
  - [ ] Implement `find_videos()` function for file discovery
  - [ ] Implement `validate_video_file()` function with ffmpeg probe
  - [ ] Implement `get_video_info()` function for metadata extraction
  - [ ] Add `SUPPORTED_VIDEO_FORMATS` constants
  - [ ] Add `is_video_file()` helper function
  - [ ] Error handling for ffmpeg failures (fail-fast)
- [ ] Update tests `tests/test_utils.py`
  - [ ] `test_find_videos_recursive_with_real_files()`
  - [ ] `test_validate_video_file_fails_fast()`
  - [ ] `test_get_video_info_with_real_video()`
  - [ ] `test_is_video_file_format_detection()`
- [ ] Run verification: `uv run pytest tests/test_utils.py -k video`

### 2. Add Video Support to LiteLLM Model

- **Files:** `src/media_analyzer_cli/models/litellm_model.py` (modify)
- **Details:** Add video analysis method to LiteLLMModel class for Gemini integration with base64 encoding and proper MIME type handling.
- **Tests:** `tests/test_models.py` (modify) - extend existing model tests
- **Verification:** `uv run pytest tests/test_models.py -k video`

**Todo**
- [ ] Modify `src/media_analyzer_cli/models/litellm_model.py`
  - [ ] Add `_encode_video()` method for base64 encoding
  - [ ] Add `_validate_video()` method for file validation
  - [ ] Implement `analyze_video()` method for Gemini video analysis
  - [ ] Support video mode: "description" only (future extensibility via mode parameter)
  - [ ] Add MIME type mapping for video formats
  - [ ] Error handling for Gemini-only restriction (fail-fast)
- [ ] Update tests `tests/test_models.py`
  - [ ] `test_litellm_model_video_analysis_with_real_api()`
  - [ ] `test_litellm_model_video_validation_fails_fast()`
  - [ ] `test_litellm_model_video_mode_validation()`
  - [ ] `test_litellm_model_non_gemini_model_fails_fast()`
- [ ] Run verification: `uv run pytest tests/test_models.py -k video`

### 3. Create VideoAnalyzer Core Module

- **Files:** `src/media_analyzer_cli/video_analyzer.py` (create)
- **Details:** Build VideoAnalyzer class following existing ImageAnalyzer/AudioAnalyzer patterns with async processing and batch support.
- **Tests:** `tests/test_video_analyzer.py` (create)
- **Verification:** `uv run pytest tests/test_video_analyzer.py`

**Todo**
- [ ] Create `src/media_analyzer_cli/video_analyzer.py`
  - [ ] Implement VideoAnalyzer class with Config integration
  - [ ] Add `analyze_single_video()` method with async processing
  - [ ] Add `analyze_batch()` method with concurrency control
  - [ ] Add `analyze_batch_with_progress()` method with tqdm progress tracking
  - [ ] Add main `analyze()` method handling files and directories
  - [ ] Add `_format_output()` method for output formatting
  - [ ] Error handling following fail-fast philosophy
- [ ] Create tests `tests/test_video_analyzer.py`
  - [ ] `test_video_analyzer_single_file_with_real_api()`
  - [ ] `test_video_analyzer_batch_processing_with_real_api()`
  - [ ] `test_video_analyzer_error_handling_fails_fast()`
  - [ ] `test_video_analyzer_mode_validation()`
  - [ ] `test_video_analyzer_directory_processing()`
- [ ] Run verification: `uv run pytest tests/test_video_analyzer.py`

### 4. Update CLI Integration

- **Files:** `src/media_analyzer_cli/cli.py` (modify)
- **Details:** Add video type to CLI options and integrate VideoAnalyzer into the main command flow.
- **Tests:** `tests/test_cli.py` (modify) - extend existing CLI tests
- **Verification:** `uv run pytest tests/test_cli.py -k video`

**Todo**
- [ ] Modify `src/media_analyzer_cli/cli.py`
  - [ ] Update `--type` choice to include "video"
  - [ ] Add `--video-mode` option with choice ["description"] (validate only "description" is supported)
  - [ ] Add video analysis branch in `main()` function
  - [ ] Import VideoAnalyzer and integrate workflow
  - [ ] Add validation for video-mode requirement
- [ ] Update tests `tests/test_cli.py`
  - [ ] `test_cli_video_analysis_with_real_api()`
  - [ ] `test_cli_video_mode_validation_fails_fast()`
  - [ ] `test_cli_video_batch_processing()`
  - [ ] `test_cli_video_help_display()`
- [ ] Create `tests/test_cli_video.py`
  - [ ] `test_cli_video_end_to_end_with_real_gemini_api()`
- [ ] Run verification: `uv run pytest tests/test_cli.py -k video`

### 5. Update Configuration and Output

- **Files:** `src/media_analyzer_cli/config.py`, `src/media_analyzer_cli/utils/output.py` (modify)
- **Details:** Add video-specific configuration settings and output formatting methods.
- **Tests:** `tests/test_models.py`, `tests/test_utils.py` (modify)
- **Verification:** `uv run pytest tests/`

**Todo**
- [ ] Modify `src/media_analyzer_cli/config.py`
  - [ ] Add `supported_video_formats` list constant
  - [ ] Add `max_video_size_mb` setting (default 2048MB for Gemini 2.0)
  - [ ] Add video-specific timeout settings if needed
- [ ] Modify `src/media_analyzer_cli/utils/output.py`
  - [ ] Add `format_video_results()` method following existing patterns
  - [ ] Support video-specific output formats (description/analysis only)
  - [ ] Add video metadata display in verbose mode
- [ ] Update existing tests for new configuration
  - [ ] Update config tests for new video settings
  - [ ] Update output formatter tests for video results
- [ ] Run verification: `uv run pytest tests/`

### 6. Update Documentation

- **Files:** `README.md` (modify)
- **Details:** Add video analysis examples and usage documentation following existing patterns.
- **Tests:** Manual testing of documented examples
- **Verification:** `uv run media-analyzer --help`, manual example testing

**Todo**
- [ ] Update `README.md`
  - [ ] Add "Video Analysis" to Features section
  - [ ] Add video examples to Usage section
  - [ ] Update command line options table with video options
  - [ ] Add video-specific configuration examples
  - [ ] Update installation requirements if needed
- [ ] Test documented examples manually
  - [ ] Test single video analysis example
  - [ ] Test batch video processing example
  - [ ] Test video description mode with custom prompts
- [ ] Run verification: `uv run media-analyzer --help`

---

## 3 Testing Output Requirements

**Test Plan for Video Analysis**

**New Test Files:**
- `tests/test_video_analyzer.py`
  - `test_video_analyzer_single_file_with_real_api()`
  - `test_video_analyzer_batch_processing_with_real_api()`
  - `test_video_analyzer_error_handling_fails_fast()`
  - `test_video_analyzer_mode_validation()`
  - `test_video_analyzer_directory_processing()`

- `tests/test_cli_video.py`
  - `test_cli_video_end_to_end_with_real_gemini_api()`

**Modified Test Files:**
- `tests/test_models.py`
  - ADD: `test_litellm_model_video_analysis_with_real_api()`
  - ADD: `test_litellm_model_video_validation_fails_fast()`
  - ADD: `test_litellm_model_video_mode_validation()`
  - ADD: `test_litellm_model_non_gemini_model_fails_fast()`

- `tests/test_cli.py`
  - ADD: `test_cli_video_analysis_with_real_api()`
  - ADD: `test_cli_video_mode_validation_fails_fast()`
  - ADD: `test_cli_video_batch_processing()`
  - ADD: `test_cli_video_help_display()`

- `tests/test_utils.py`
  - ADD: `test_find_videos_recursive_with_real_files()`
  - ADD: `test_validate_video_file_fails_fast()`
  - ADD: `test_get_video_info_with_real_video()`
  - ADD: `test_is_video_file_format_detection()`

**Test Categories:**
- Unit tests: Individual VideoAnalyzer component validation
- Integration tests: Video analysis with real Gemini API calls  
- CLI tests: End-to-end video analysis workflows

**Key Testing Requirements:**
- **Fail-fast philosophy** with real API integration
- **No mocking** (`unittest.mock`, `@patch` forbidden)
- **Credential validation** via `require_api_credentials()`
- **Real Gemini API calls** for authentic video testing
- **Real video files** for testing (mp4, mov, etc.)

---

## 4 Enhanced Pseudocode Format

### 4.1 AI Workflow Example

```
CLASS VideoAnalyzer INHERITS BaseMediaAnalyzer:
  DATAFLOW: analyzes video files using Gemini models
  
  video_file → validate_video() METHOD: ffmpeg_probe(video_path) → validation_result
  video_file → encode_video() METHOD: base64_encode(video_bytes) → encoded_video
  encoded_video → gemini_api_call METHOD: litellm.completion(model="gemini-2.5-flash", content=[text_prompt, video_data]) → analysis_result
  
  MODES:
    - "description": Visual and audio content analysis (only supported mode)
    - Future modes: Can be added later via mode parameter
  
  METHODS:
    analyze_single_video(model, video_path, mode, prompt, word_count)
    analyze_batch(video_files, model, mode, concurrency)
    _validate_video_file(video_path) → RAISE ValueError IF invalid
    _format_video_output(results, format_type)
  
  ERROR_HANDLING: fail-fast on all validation and API errors
```

### 4.2 Traditional Logic Example

```
FUNCTION validate_video_file(video_path):
    IF not video_path.exists():
        RAISE FileNotFoundError("Video file does not exist")
    IF video_path.suffix not in SUPPORTED_VIDEO_FORMATS:
        RAISE ValueError("Unsupported video format")
    result = ffmpeg.probe(video_path)
    IF result has no video streams:
        RAISE ValueError("No video streams found")
    RETURN True
```