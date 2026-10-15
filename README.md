# Ingestion Engine & TradeBook Platform

A high-throughput financial trade processing, simulated market ingestion, and keyset-paginated query system built with **FastAPI**, **Python 3.13**, **aioodbc**, and **Microsoft SQL Server**.

---

## 1. Documentation Index

The platform documentation is organized into focused domains for engineering, database design, testing, and system architecture:

### 🚀 Developer Onboarding & Architecture ([`docs/DEVELOPER_GUIDE.md`](file:///d:/ingestion_engine/docs/DEVELOPER_GUIDE.md))
* **[Developer Onboarding & Debugging Guide](file:///d:/ingestion_engine/docs/DEVELOPER_GUIDE.md)**: 60-second system mental model, vertical slice architecture feasibility analysis, step-by-step diagnostic handbook, and the 6-step recipe for adding new features.
* **[System Architecture Specification](file:///d:/ingestion_engine/docs/architecture.md)**: Clean Architecture principles, CQRS read-optimization, and empirical latency benchmarks.

### 🧪 Testing Documentation ([`docs/tests/`](file:///d:/ingestion_engine/docs/tests/README.md))
* **[Unit Testing Architecture & Test Catalog](file:///d:/ingestion_engine/docs/tests/unit_tests.md)**: Pure in-memory testing philosophy (zero database dependencies), fixture catalog (`conftest.py`), and test breakdown across `test_login.py` and `test_tradebook.py`.
* **[Developer Testing Guide & Command Reference](file:///d:/ingestion_engine/docs/tests/testing_guide.md)**: Practical CLI commands, flags (`-v`, `-s`, `-k`, `--pdb`), coverage profiling, mock debugging, and authoring tutorials.

### 🗄️ Database Documentation ([`docs/Database/`](file:///d:/ingestion_engine/docs/Database/README.md))
* **[Database Architecture & Context](file:///d:/ingestion_engine/docs/Database/README.md)**: Relational design, async `aioodbc` connection pooling, and multi-tier RBAC partitioning.
* **[Data Models & Entity Mappings](file:///d:/ingestion_engine/docs/Database/Datamodels/data_models_overview.md)**: Relational overview, domain entity hydration, and direct DTO projections.
* **[Table: `dbo.tbTradeBook`](file:///d:/ingestion_engine/docs/Database/Datamodels/tbTradeBook.md)**: Trade ledger table schema, column dictionaries, and monotonic sequence keys.
* **[Table: `dbo.Config_DealerMap`](file:///d:/ingestion_engine/docs/Database/Datamodels/Config_DealerMap.md)**: Multi-tenant dealer, account, terminal, and group mappings.
* **[Table: `dbo.UserAccount`](file:///d:/ingestion_engine/docs/Database/Datamodels/UserAccount.md)**: User credentials, SHA-512 binary password hashes, roles, and login auditing.
* **[Stored Procedure: `dbo.usp_GetTradeBook`](file:///d:/ingestion_engine/docs/Database/Stored%20Procedures/usp_GetTradeBook.md)**: Bidirectional keyset pagination, CTE query pipeline, lookahead boundary flags, and SQL test suite.
* **[Views: `dbo.vw_TradeBook`](file:///d:/ingestion_engine/docs/Database/Views/vw_TradeBook.md)**: Data abstraction view, physical decoupling, and indexing capabilities.

---

## 2. Architecture Quick Summary

* **Clean Architecture with Feature Slices**: Segregated Domain, Application, Infrastructure, and Presentation layers inside `src/features/`.
* **Dual-Layer RBAC Security**:
  - Application Policy: [`TradeBookAccessPolicy`](file:///d:/ingestion_engine/src/features/Tradebook/Domain/policies/TradeBookAccessPolicy.py) prevents role escalation and cross-dealer snooping.
  - Database Engine Defense: [`dbo.usp_GetTradeBook`](file:///d:/ingestion_engine/sql/SP_Query.sql) independently enforces role predicates in SQL.
* **Read-Optimized Direct Projection**: Zero entity allocation overhead on high-volume trade queries; direct streaming from database rowsets into [`TradeBookPageOutDto`](file:///d:/ingestion_engine/src/features/Tradebook/Application/DTO/Outputs/TradeBookPageOutDto.py).

---

## 3. Fast Command Cheat Sheet

```bash
# Run all unit tests
uv run python -m pytest

# Run tests with verbose output and print statements
uv run python -m pytest -vv -s

# Run tests with line-by-line coverage report
uv run python -m pytest --cov=src --cov-report=term-missing
```
