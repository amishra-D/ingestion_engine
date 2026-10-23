# Developer Testing Guide & Command Reference

This guide provides practical command-line instructions, debugging workflows, and conventions for running and authoring tests in the repository.

---

## 1. Fast Command Reference

All tests should be executed using **`uv`** with `python -m pytest` to ensure `PYTHONPATH` includes the repository root on Windows:

| Goal | Command |
| :--- | :--- |
| **Run all unit tests** | `uv run python -m pytest` |
| **Verbose output with test names** | `uv run python -m pytest -v` |
| **Print stdout/print statements** | `uv run python -m pytest -s` |
| **Run only Auth tests** | `uv run python -m pytest tests/unit_tests/test_login.py` |
| **Run only TradeBook tests** | `uv run python -m pytest tests/unit_tests/test_tradebook.py` |
| **Run a specific test function** | `uv run python -m pytest tests/unit_tests/test_login.py::test_login_use_case_success` |
| **Filter by expression / keyword** | `uv run python -m pytest -k "escalation"` |
| **Stop immediately on first failure**| `uv run python -m pytest -x` |
| **Drop into PDB on test failure** | `uv run python -m pytest --pdb` |
| **Run tests with code coverage** | `uv run python -m pytest --cov=src --cov-report=term-missing` |

---

## 2. Running Test Suites

### 2.1 Standard Execution
```bash
uv run python -m pytest
```
* **Expected Result**: 13 passed in under 1 second.

### 2.2 Verbose & Show Print Output
When debugging print statements or latency diagnostics added in code:
```bash
uv run python -m pytest -vv -s
```

### 2.3 Filtering Tests by Keyword (`-k`)
You can filter tests by name or substring:
```bash
# Match tests with 'escalation' or 'snooping' in the name
uv run python -m pytest -k "escalation or snooping" -v

# Run only presentation route tests
uv run python -m pytest -k "route" -v
```

### 2.4 Short Traceback on Failures (`--tb=short`)
To keep terminal output clean when diagnosing exceptions:
```bash
uv run python -m pytest --tb=short
```

---

## 3. Code Coverage Profiling

To check test coverage across the `src/` directory:

### 3.1 Terminal Summary with Missing Lines
```bash
uv run python -m pytest --cov=src --cov-report=term-missing
```

### 3.2 Generating an HTML Coverage Report
```bash
uv run python -m pytest --cov=src --cov-report=html
```
The report is generated in `htmlcov/index.html`. You can open it in any web browser to inspect line-by-line coverage.

---

## 4. Debugging Workflows

### 4.1 Interactive Debugger (`breakpoint()` or `--pdb`)
Drop straight into the Python interactive debugger upon any assertion failure:
```bash
uv run python -m pytest --pdb
```

Alternatively, insert `breakpoint()` directly inside any test or source file:
```python
@pytest.mark.asyncio
async def test_debug_example(mock_trade_repo):
    breakpoint()  # Drops execution into pdb interactive shell here
    use_case = GetTradeUseCase(repository=mock_trade_repo)
```
Run with `-s` so the debugger stdin/stdout is not captured by pytest:
```bash
uv run python -m pytest tests/unit_tests/test_tradebook.py -s
```

### 4.2 Inspecting AsyncMock Calls
When an assertion fails like `assert mock.assert_called_once_with(...)`, inspect the exact mock history:

```python
# Print all calls made to the mock
print(mock_login_repo.mock_calls)

# Print call arguments list
print(mock_login_repo.get_by_username.call_args_list)

# Inspect last call arguments
print(mock_login_repo.get_by_username.call_args)
```

---

## 5. Common Testing Gotchas & Solutions

### ❌ `ModuleNotFoundError: No module named 'src'`
* **Cause**: Running bare `pytest` on Windows without `src/` installed in editable mode or without `PYTHONPATH=.`.
* **Fix**: Always execute via `uv run python -m pytest`. The `python -m` invocation automatically injects the current working directory into `sys.path`.

### ❌ `PytestUnhandledCoroutineWarning` or un-awaited coroutine
* **Cause**: Forgetting `@pytest.mark.asyncio` on an `async def test_*` function.
* **Fix**: Ensure all asynchronous tests are decorated:
  ```python
  import pytest


  @pytest.mark.asyncio
  async def test_my_async_code():
      result = await some_async_call()
      assert result is not None
  ```

---

## 6. How to Write a New Unit Test (Step-by-Step)

Follow this standardized pattern when creating tests for a new use case or route:

```python
# 1. Imports
from unittest.mock import AsyncMock
import pytest
from src.features.MyFeature.Application.DTO.Inputs.MyInputDTO import MyInputDTO
from src.features.MyFeature.Application.use_cases.MyUseCase import MyUseCase


# 2. Decorate with pytest.mark.asyncio
@pytest.mark.asyncio
async def test_my_use_case_success():
    # 3. Arrange: Setup mock repository & ports
    mock_repo = AsyncMock()
    mock_repo.get_data.return_value = {"id": 1, "status": "active"}

    use_case = MyUseCase(repository=mock_repo)
    dto = MyInputDTO(item_id=1)

    # 4. Act: Execute the use case
    result = await use_case.execute(dto)

    # 5. Assert: Verify return values and mock interactions
    assert result.status == "active"
    mock_repo.get_data.assert_called_once_with(1)
```
