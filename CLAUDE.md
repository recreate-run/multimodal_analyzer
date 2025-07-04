# Coding

- use uv for complete python project management (eg. never use pip directly)
- use "uv add .." to add the dependencies and "uv run.." to run scripts
- check @pyproject.toml for dependencies

## Code style

1. As this is an early-stage startup, YOU MUST prioritize simple, readable code with minimal abstraction—avoid premature optimization. Focus on clear implementation that’s easy to understand and iterate on as the product evolves.
2. NEVER mock LLM API calls
3. DO NOT use preserve backward compatibility unless the user specifically requests it
4. Do not handle errors (eg. API failures) gracefully, raise exceptions immediately.

## Fail-Fast Error Handling Rules

**Code MUST fail immediately on errors. No graceful degradation.**

### ❌ FORBIDDEN:
- Empty exception handlers: `except Exception: pass`
- Returning defaults/None on API failures
- Retry logic, fallback responses, warning messages
- Test skipping with `self.skipTest()` - use `require_api_credentials()`
- Mocking API calls (`unittest.mock`, `@patch`)

### ✅ REQUIRED:
- Let exceptions propagate - never catch and mask
- Raise specific exceptions: `FileNotFoundError`, `KeyError`, `ValueError`
- Real API calls only in tests

**Philosophy**: Fail fast, no graceful degradation.

# MCP Usage
1. All linear issues must be created in the "Pixar quality video generation" project
