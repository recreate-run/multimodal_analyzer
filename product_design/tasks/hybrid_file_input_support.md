# Hybrid File Input Support for Media Analyzer CLI

## 1 Task Overview

| Field            | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| **Task Name**    | Hybrid File Input Support for Media Analyzer CLI                |
| **Description**  | Add support for both folder paths (--path) AND explicit file lists (--files) to enable flexible batch processing. Users can either scan directories or specify exact files from multiple locations. |
| **Dependencies** | None                                                            |

---

## 2 Implementation Steps & Todo Lists

### 1. Update CLI Interface with Mutually Exclusive Options

- **Files:** `src/multimodal_analyzer_cli/cli.py` (modify)
- **Details:** Replace single --path option with mutually exclusive --path and --files options using click.option groups.
- **Tests:** `tests/test_cli.py` - modify existing test_basic_image_analysis() and test_missing_required_options()
- **Verification:** `uv run pytest tests/test_cli.py::TestCLI::test_basic_image_analysis -v`

**Todo**
- [ ] Import click.option and create mutually exclusive group
  - [ ] Replace current `@click.option("--path", ...)` with option group
  - [ ] Add `@click.option("--path", ...)` for directory/single file (existing behavior)
  - [ ] Add `@click.option("--files", multiple=True, ...)` for explicit file list (new behavior)
  - [ ] Add validation logic in main() function
- [ ] Update main() function signature and parameter handling
  - [ ] Change `path: str` to `path: str | None`
  - [ ] Add `files: tuple[str, ...] | None` parameter
  - [ ] Add validation: exactly one of path/files must be provided
  - [ ] Add validation: both path and files cannot be provided simultaneously
- [ ] Update analyzer instantiation calls
  - [ ] Pass appropriate file source to ImageAnalyzer.analyze()
  - [ ] Pass appropriate file source to AudioAnalyzer.analyze()
  - [ ] Pass appropriate file source to VideoAnalyzer.analyze()

### 2. Create File Validation Utilities

- **Files:** `src/multimodal_analyzer_cli/utils/file_discovery.py` (create)
- **Details:** Create utility functions to validate and process explicit file lists with fail-fast error handling.
- **Tests:** Integration tested via CLI tests (no separate unit tests per guidelines)
- **Verification:** `uv run pytest tests/test_cli.py::TestCLI::test_files_mode_analysis -v`

**Todo**
- [ ] Create new utility module `src/multimodal_analyzer_cli/utils/file_discovery.py`
  - [ ] Implement `validate_file_list(files: list[str], media_type: str) -> list[Path]`
    - [ ] Convert string paths to Path objects
    - [ ] Check each file exists (raise FileNotFoundError if not)
    - [ ] Validate file extensions for media type (raise ValueError for unsupported)
    - [ ] Ensure no mixed media types in list
  - [ ] Implement `get_files_by_type(files: list[Path], media_type: str) -> list[Path]`
    - [ ] Filter files by media type (image/audio/video)
    - [ ] Return sorted list of valid files
  - [ ] Implement `ensure_files_exist(files: list[Path]) -> None`
    - [ ] Check all files exist and are readable
    - [ ] Raise FileNotFoundError immediately on first missing file

### 3. Update Analyzer Classes for Hybrid Input

- **Files:** `src/multimodal_analyzer_cli/image_analyzer.py`, `src/multimodal_analyzer_cli/audio_analyzer.py`, `src/multimodal_analyzer_cli/video_analyzer.py` (modify)
- **Details:** Update each analyzer's analyze() method to accept either path or file_list parameter while preserving existing functionality.
- **Tests:** Integration tested via CLI tests in test_cli.py
- **Verification:** `uv run pytest tests/test_cli.py -v`

**Todo**
- [ ] Update ImageAnalyzer.analyze() method signature
  - [ ] Add optional `file_list: list[Path] | None = None` parameter
  - [ ] Modify file discovery logic at line 46-48 to use file_list when provided
  - [ ] Preserve existing find_images(path, recursive) behavior when file_list is None
  - [ ] Update validation to handle both input modes
- [ ] Update AudioAnalyzer.analyze() method signature
  - [ ] Add optional `file_list: list[Path] | None = None` parameter
  - [ ] Modify file discovery logic at line 172 to use file_list when provided
  - [ ] Preserve existing get_media_files(path, recursive) behavior when file_list is None
  - [ ] Update validation to handle both input modes
- [ ] Update VideoAnalyzer.analyze() method signature
  - [ ] Add optional `file_list: list[Path] | None = None` parameter
  - [ ] Modify file discovery logic to use file_list when provided
  - [ ] Preserve existing find_videos(path, recursive) behavior when file_list is None
  - [ ] Update validation to handle both input modes

### 4. Update CLI Tests for Hybrid Input

- **Files:** `tests/test_cli.py` (modify)
- **Details:** Modify existing path test and add one new files mode test with real API calls.
- **Tests:** Self-testing integration tests
- **Verification:** `uv run pytest tests/test_cli.py -v`

**Todo**
- [ ] Modify existing `test_basic_image_analysis()` method
  - [ ] Ensure it continues to test --path mode functionality
  - [ ] Update assertions if needed for new CLI structure
  - [ ] Verify single file and directory processing still works
- [ ] Add new `test_files_mode_analysis()` method
  - [ ] Create multiple test image files in isolated filesystem
  - [ ] Test --files option with explicit file list
  - [ ] Use real API calls with require_api_credentials()
  - [ ] Verify batch processing works with explicit file list
  - [ ] Test fail-fast behavior on invalid file in list
- [ ] Update `test_missing_required_options()` method
  - [ ] Test that neither --path nor --files results in error
  - [ ] Test that both --path and --files results in error
  - [ ] Verify proper error messages for mutually exclusive options

---

## 3 Testing Strategy

**CRITICAL**: Tests MUST follow **integration-first approach** with **fail-fast philosophy**. We prioritize integration tests over unit tests.

### 3.1 Integration Tests First

**MANDATORY Requirements:**
- ✅ **MUST test complete user workflows** from CLI/API input to final output
- ✅ **MUST use real API calls** with `require_api_credentials()`
- ✅ **MUST fail immediately** on errors or missing dependencies
- ✅ **EXCEPTION: Unit tests permitted for LLM provider implementations only**
- ❌ **NEVER mock LLM API calls** (`unittest.mock`, `@patch` forbidden)
- ❌ **NEVER test individual functions** in isolation (except LLM providers)

### 3.2 Test Planning Template

**Test Plan for Hybrid File Input Support**

**Integration Tests:**
- `tests/test_cli.py`
  - `test_basic_image_analysis()` - verify --path mode still works with real API calls
  - `test_files_mode_analysis()` - verify --files mode works with multiple files and real API calls
  - `test_missing_required_options()` - verify proper validation of mutually exclusive options

**End-to-End Tests:**
- `tests/test_cli.py`
  - Complete CLI workflow testing via existing integration test framework
  - Real API calls using `require_api_credentials()` pattern
  - Fail-fast behavior on invalid inputs

### 3.3 Test Structure

```
tests/
├── test_cli.py              # CLI integration tests (modified)
├── test_cli_audio.py        # Audio CLI tests (unchanged)
├── test_cli_video.py        # Video CLI tests (unchanged)
└── test_utils.py           # Test utilities (unchanged)
```

### 3.4 Essential Test Patterns

**Integration Test Template:**
```python
class TestCLI:
    def setup_method(self):
        require_api_credentials()

    def test_files_mode_analysis(self):
        # Test full user workflow with real components
        model_name = get_primary_image_model()
        
        with self.runner.isolated_filesystem():
            # Create multiple test images
            with FileManager() as manager:
                img1 = manager.create_test_image()
                img2 = manager.create_test_image()
                shutil.copy2(img1, "test1.jpg")
                shutil.copy2(img2, "test2.jpg")
            
            result = self.runner.invoke(
                main,
                [
                    "--type", "image",
                    "--model", model_name,
                    "--files", "test1.jpg", "test2.jpg",
                    "--word-count", "30"
                ]
            )
            
            assert result.exit_code == 0
            assert len(result.output) > 0

    def test_workflow_fails_fast(self):
        # Test fail-fast behavior
        result = self.runner.invoke(
            main,
            [
                "--type", "image",
                "--model", "gpt-4o-mini",
                "--files", "nonexistent.jpg"
            ]
        )
        assert result.exit_code != 0
```

### 3.5 Test Requirements

**BEFORE implementing any feature:**
1. Read `tests/test_structure.yaml` to understand existing coverage
2. Identify which workflows need integration tests
3. Plan test consolidation to avoid duplicate test files

**DURING implementation:**
- Write tests that verify user-observable behavior only
- Use temporary files/databases for real I/O operations
- Test complete workflows, not individual functions

**AFTER implementation:**
- Run integration tests: `uv run pytest tests/test_cli.py -v`
- Run all tests: `uv run pytest --cov`
- Update test structure if needed: `uv run python generate_test_structure.py`

---

## 5 Enhanced Pseudocode Format

### 5.1 CLI Option Processing Logic

```
FUNCTION main(type_, model, path, files, ...):
    # Validate mutually exclusive options
    IF path AND files:
        RAISE ClickException("Cannot specify both --path and --files")
    IF NOT path AND NOT files:
        RAISE ClickException("Must specify either --path or --files")
    
    # Determine file source
    IF path:
        file_source = PathSource(path)
        file_list = None
    ELSE:
        file_source = FileListSource(files)
        file_list = validate_file_list(files, type_)
    
    # Create analyzer and process
    analyzer = create_analyzer(type_, config)
    result = analyzer.analyze(
        model=model,
        path=path,
        file_list=file_list,
        word_count=word_count,
        ...
    )
    
    IF NOT output_file:
        click.echo(result)
    
    RETURN result
```

### 5.2 Analyzer Update Pattern

```
FUNCTION analyze(model, path=None, file_list=None, recursive=False, ...):
    # Validate configuration
    config.validate()
    
    # Determine file discovery method
    IF file_list:
        media_files = validate_file_list(file_list, media_type)
        IF NOT media_files:
            RAISE ValueError("No valid files in list")
    ELSE:
        media_files = discover_files(path, recursive, supported_formats)
        IF NOT media_files:
            RAISE ValueError(f"No supported files found in {path}")
    
    # Process files
    IF len(media_files) == 1:
        results = [analyze_single_file(media_files[0])]
    ELSE:
        results = analyze_batch_with_progress(media_files, concurrency)
    
    # Format and return output
    formatted_output = format_output(results, output_format, verbose)
    
    IF output_file:
        save_to_file(formatted_output, output_file)
    
    RETURN formatted_output
```

### 5.3 File Validation Logic

```
FUNCTION validate_file_list(files, media_type):
    validated_files = []
    
    FOR file_path_str IN files:
        file_path = Path(file_path_str)
        
        IF NOT file_path.exists():
            RAISE FileNotFoundError(f"File not found: {file_path}")
        
        IF NOT is_supported_format(file_path, media_type):
            RAISE ValueError(f"Unsupported format: {file_path}")
        
        validated_files.append(file_path)
    
    IF NOT validated_files:
        RAISE ValueError("No valid files provided")
    
    RETURN sorted(validated_files)
```