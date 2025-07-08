# AI Agent Planning Guide for Implementation Tasks

This guide helps the AI agent create detailed implementation plans for software development tasks.
---

## 1  Task Overview

| Field            | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| **Task Name**    | (Copy from `product_design/implementation_plan.md`)              |
| **Description**  | Concise statement of objective & business value (≤ 2 sentences). |
| **Dependencies** | Bullet list of prerequisite tasks (IDs or filenames).            |

---

## 2  Implementation Steps & Todo Lists

Break the task into numbered steps. Each step embeds its own todo list so progress is trackable in a single place.

```markdown
### 1. <Summative Step Name>

- **Files:** `path/to/file.py` (create/modify)
- **Details:** One‑sentence goal of this step.
- **Tests:** *List specific test files and scenarios (Planning AI: apply internal framework to determine these)*
- **Verification:** Commands (e.g., `ruff check .`, `pytest`).

**Todo**
- [ ] Create directory `src/path/to/module`
  - [ ] Add `src/path/to/file.py`
    - [ ] Implement <function/class>
    - [ ] Error handling for <edge case>
- [ ] Add tests `tests/path/to/test_file.py`
  - [ ] test_component_happy_path_with_real_api
  - [ ] test_component_error_handling_fails_fast
  - [ ] test_component_specific_scenario
- [ ] Run verification commands
```

### Rules for Editing tasks

1. **If you add a new task**, ensure that all other parts of the document are also updated accordingly (test sections, pseudocode examplesetc.)
2. **Finished tasks should not be modified** under any circumstances!. Any updates to be made should be included as part of a new task. This preserves task completion history and prevents scope creep.


## 3  Testing Strategy

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

For each feature/component, specify:

```markdown
**Test Plan for [Feature/Component]**

**Integration Tests:**
- `tests/integration/test_<workflow>.py`
  - `test_complete_workflow_success()`
  - `test_workflow_fails_fast_on_error()`
  - `test_workflow_with_real_api_calls()`

**End-to-End Tests:**
- `tests/storyboard/test_<feature>.py`
  - `test_full_pipeline_integration()`
```

### 3.3 Test Structure

```
tests/
├── integration/    # Multi-component workflows
└── storyboard/     # Complete end-to-end pipelines
```

### 3.4 Essential Test Patterns

**Integration Test Template:**
```python
class TestFeatureIntegration:
    def setup_method(self):
        require_api_credentials()

    def test_complete_workflow(self):
        # Test full user workflow with real components
        result = run_cli_command(['feature', '--input', 'data'])
        assert result.exit_code == 0
        assert 'expected output' in result.output

    def test_workflow_fails_fast(self):
        # Test fail-fast behavior
        result = run_cli_command(['feature', '--invalid'])
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
- Run integration tests: `uv run pytest tests/integration/`
- Run end-to-end tests: `uv run pytest tests/storyboard/`
- Update test structure if needed: `uv run python generate_test_structure.py`

---

## 5  Enhanced Pseudocode Format

Use AI‑centric data‑flow notation for workflows; traditional pseudocode for non‑AI logic.

### 5.1 AI Workflow Example

```
CLASS StoryGeneratorWorkflow INHERITS BaseWorkflow:
  DATAFLOW: generates a short story from a prompt
  user_prompt → llm_call METHOD: openai.chat_completion(system="You are a storyteller", user=user_prompt) → draft
        draft → quality_evaluator METHOD: openai.chat_completion(system="Rate story", user=draft) → score
  IF score < 0.8: ITERATE up to 3 times
  RETURN finalized_story
```

### 5.2 Traditional Logic Example

```
FUNCTION process_data(input):
    IF not input:
        RAISE ValueError("Empty input")
    result = transform(input)
    RETURN validate(result)
```
