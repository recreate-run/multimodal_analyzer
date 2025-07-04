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


## 3  Testing Output Requirements

**FOR PLANNING AI AGENT**: Apply the Internal Testing Framework (§4) to determine specific test requirements. Output only the final test decisions, not the decision-making process.

**FOR IMPLEMENTER**: This section contains the specific test files and scenarios determined by the planning AI agent.

### 3.1 Test Specification Format

For each component/feature, specify:

```markdown
**Test Plan for [Component/Feature]**

**New Test Files:**
- `tests/unit/<module>/test_<component>.py`
  - `test_component_happy_path_with_real_api()`
  - `test_component_error_handling_fails_fast()`
  - `test_component_specific_scenario()`

**Modified Test Files:**
- `tests/integration/test_<workflow>.py`
  - UPDATE: `test_existing_workflow()` - change assertions for new API
  - REMOVE: `test_old_behavior()` - obsolete after API change
  - ADD: `test_new_workflow_step()`

**Test Categories:**
- Unit tests: Individual component validation
- Integration tests: Multi-component workflows
- Storyboard tests: End-to-end pipeline validation
```

### 3.2 Essential Test Patterns

**Key Requirements:**
- **Fail-fast philosophy** with real API integration
- **No mocking** (`unittest.mock`, `@patch` forbidden)
- **Credential validation** via `require_api_credentials()`
- **Real LLM API calls** for authentic testing

**Test Structure:**
```
tests/
├── unit/           # Individual component validation
├── integration/    # Multi-component workflows
└── storyboard/     # End-to-end generation pipeline
```

---

## 4  Internal Testing Framework (AI Agent Use Only)

**INSTRUCTIONS FOR PLANNING AI AGENT**: Use this framework internally to determine test requirements. Do NOT copy this content to task plans. Output only the final test decisions from §3.1.

**NOTE**: This section is for the AI agent creating the implementation plan, not the AI agent executing the finished plan.

**CRITICAL FIRST STEP**: Always read `tests/test_structure.yaml` to understand existing test coverage before making testing decisions.

### 4.1 Test Discovery & Decision Framework

**Step 1: Understand Current Coverage**
```bash
# Read existing test structure
cat tests/test_structure.yaml
```

**Step 2: Test Decision Matrix**

| **Scenario** | **Action** | **Location** |
|-------------|------------|--------------|
| Component has **no tests** | Create new test file | `tests/unit/<module>/test_<component>.py` |
| Component has **partial coverage** | Extend existing test | Add test methods to existing file |
| New **integration pathway** | Create integration test | `tests/integration/test_<workflow>.py` |
| New **end-to-end workflow** | Create storyboard test | `tests/storyboard/test_<feature>.py` |
| **Modifying existing code** | Update existing tests | Modify corresponding test file |

**Step 3: Gap Analysis Template**
```markdown
**Testing Gap Analysis for [Component/Feature]**
- [ ] Existing coverage: [Review tests/test_structure.yaml]
- [ ] Missing unit tests: [List components without tests]
- [ ] Missing integration tests: [List workflows without tests]
- [ ] Test modification needed: [List tests requiring updates]
```

### 4.2 Test Ecosystem Patterns

**Current Structure:**
```
tests/
├── unit/           # Individual component validation
├── integration/    # Multi-component workflows
└── storyboard/     # End-to-end generation pipeline
```

**Key Patterns to Follow:**
- **Fail-fast philosophy** with real API integration
- **No mocking** (`unittest.mock`, `@patch` forbidden)
- **Credential validation** via `require_api_credentials()`
- **Real LLM API calls** for authentic testing

### 4.3 Test Categories & When to Use

| **Category** | **Purpose** | **When to Add** | **Example** |
|-------------|-------------|----------------|-------------|
| **Unit** | Validate individual components | New modules, functions, classes | `tests/unit/api/test_text_client.py` |
| **Integration** | Test component interactions | New workflows, cross-module features | `tests/integration/test_strategy_system.py` |
| **Storyboard** | End-to-end pipeline validation | New strategies, complete workflows | `tests/storyboard/test_basic_strategy.py` |

### 4.4 Test Creation Guidelines

**For New Components:**
```python
# tests/unit/<module>/test_<component>.py
import pytest
from src.utils.test_utils import require_api_credentials
from src.<module> import <Component>

class Test<Component>:
    def setup_method(self):
        require_api_credentials()

    def test_happy_path_with_real_api(self):
        # Real API calls only - no mocking
        result = <Component>().process()
        assert result is not None

    def test_error_path_fails_fast(self):
        # Fail-fast error handling
        with pytest.raises(ValueError):
            <Component>().process(invalid_input)
```

**For Integration Tests:**
```python
# tests/integration/test_<workflow>.py
from src.utils.test_utils import require_api_credentials
from src.<module1> import <Component1>
from src.<module2> import <Component2>

class Test<Workflow>Integration:
    def setup_method(self):
        require_api_credentials()

    def test_end_to_end_workflow(self):
        # Test real component interaction
        result = <Component1>().process()
        output = <Component2>().transform(result)
        assert output.is_valid()
```

### 4.5 Test Modification Strategy

**When Modifying Existing Code:**
1. **Identify affected tests** from `tests/test_structure.yaml`
2. **Evaluate test relevance** - determine if tests remain valid for new implementation
3. **Apply appropriate action** based on test evaluation:
   - **Update tests** when behavior changes but concept remains valid
   - **Remove tests** when they validate obsolete/incorrect behavior
   - **Preserve tests** when they remain valid for new implementation
   - **Add new tests** for new functionality
4. **Document all changes** with clear reasoning in commit messages

**Test Evolution Decision Matrix:**

| **Scenario** | **Action** | **Rationale** |
|-------------|-----------|---------------|
| Function API changes | **Remove old tests**, add new | Old tests validate incorrect behavior |
| Function logic changes | **Update test assertions** | Same concept, different implementation |
| New parameters added | **Remove old tests**, add new | NEVER preserve backward compatibility |
| Complete reimplementation | **Remove all old tests**, create new | Old tests no longer relevant |
| Refactoring without behavior change | **Keep existing tests** | Validates same behavior |

**CRITICAL RULE: NEVER try to preserve backward compatibility** - this is an early-stage startup prioritizing rapid iteration over API stability.

**Example Modifications:**
```python
# SCENARIO 1: Breaking API change - REMOVE old tests
# Old function: get_data() -> dict
# New function: get_data() -> DataModel
# Action: Remove old test, create new

# REMOVE THIS TEST (validates old return type)
# def test_get_data_returns_dict(self):
#     result = get_data()
#     assert isinstance(result, dict)

# ADD NEW TEST (validates new return type)
def test_get_data_returns_model(self):
    result = get_data()
    assert isinstance(result, DataModel)
    assert result.is_valid()

# SCENARIO 2: Adding parameters - REMOVE old tests
# Function: process(input) -> now requires process(input, format="json")
# Action: Remove old test, create new (NO backward compatibility)

# REMOVE THIS TEST (validates old API)
# def test_process_simple_input(self):
#     result = process("data")
#     assert result.is_valid()

# ADD NEW TEST (validates new required API)
def test_process_with_required_format(self):
    # New API requires format parameter
    result = process("data", format="json")
    assert result.format == "json"
    assert result.is_valid()
```

**Documentation Requirements:**
- **Commit messages** must explain test changes: "Remove obsolete test_old_behavior - function now returns DataModel instead of dict"
- **Comments** in code when removing significant test coverage
- **Update test_structure.yaml** after major test reorganization

### 4.6 Quality Gates

**Before Implementation:**
- [ ] Read `tests/test_structure.yaml`
- [ ] Identify testing gaps and modification needs
- [ ] Plan test strategy (new vs modify)

**During Implementation:**
- [ ] Write tests following existing patterns
- [ ] Use real API calls with `require_api_credentials()`
- [ ] Implement fail-fast error handling

**After Implementation:**
- [ ] Run affected test categories: `uv run pytest tests/unit/`
- [ ] Verify integration tests: `uv run pytest tests/integration/`
- [ ] Update `tests/test_structure.yaml` if needed: `uv run python generate_test_structure.py`

### 4.7 Commands & Verification

```bash
# Run specific test categories
uv run pytest tests/unit/                    # Unit tests
uv run pytest tests/integration/             # Integration tests
uv run pytest tests/storyboard/              # End-to-end tests

# Run tests for specific module
uv run pytest tests/unit/<module>/           # Module-specific tests
uv run pytest tests/ -k "test_<component>"   # Component-specific tests
```

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
