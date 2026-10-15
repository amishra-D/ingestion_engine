# Testing Architecture & Documentation Hub

Welcome to the automated testing documentation for the **Ingestion Engine & TradeBook Platform**.

The testing documentation is segregated into two specialized guides:

---

## 📑 Testing Documentation Index

### 1. 📘 [Unit Testing Architecture & Test Catalog](file:///d:/ingestion_engine/docs/tests/unit_tests.md)
* **Testing Philosophy**: Clean Architecture isolation, pure in-memory test harness, and sub-second execution.
* **Fixtures Architecture**: Complete reference for [`tests/conftest.py`](file:///d:/ingestion_engine/tests/conftest.py), including mock ports (`ILoginRepository`, `IGetTradesRepository`), mock use cases, and JWT security token fixtures.
* **Full Test Catalog**: Exhaustive breakdown of all 13 unit tests across [`test_login.py`](file:///d:/ingestion_engine/tests/unit_tests/test_login.py) and [`test_tradebook.py`](file:///d:/ingestion_engine/tests/unit_tests/test_tradebook.py).

### 2. 🚀 [Developer Testing Guide & Command Reference](file:///d:/ingestion_engine/docs/tests/testing_guide.md)
* **Fast CLI Command Reference**: Running all tests, single files, single test functions, or filtering by keyword (`-k`).
* **Command Line Flags**: Verbosity (`-vv`), stdout printing (`-s`), early exit (`-x`), and short tracebacks (`--tb=short`).
* **Code Coverage Profiling**: Generating terminal coverage summaries and interactive HTML reports via `pytest-cov`.
* **Interactive Debugging**: Using `breakpoint()`, `--pdb`, and inspecting `AsyncMock` call histories.
* **Gotchas & Solutions**: Resolving `ModuleNotFoundError` on Windows and async loop scoping.
* **Step-by-Step Tutorial**: How to write a new unit test for an incoming feature or route.

---

## 🗂️ Test Directory Layout

```text
tests/
├── conftest.py                     # Centralized pytest fixtures, mock ports & token generators
├── unit_tests/                     # Isolated unit tests (Zero database dependency)
│   ├── test_login.py               # Auth Use Case & Presentation route unit tests (8 tests)
│   └── test_tradebook.py           # TradeBook RBAC & Keyset pagination unit tests (5 tests)
└── integration_tests/              # Reserved for future live database integration suites
```

---

## ⚡ Quick Start

Run the entire unit test suite:

```bash
uv run python -m pytest
```
