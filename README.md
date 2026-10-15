# Ingestion Engine & TradeBook Platform

A high-throughput financial trade processing, simulated market ingestion, and keyset-paginated query system built with **FastAPI**, **Python 3.13**, **aioodbc**, and **Microsoft SQL Server**.

---

## 1. Documentation Index

The platform documentation is organized by domain and architecture components:

### 🗄️ Database Documentation ([`docs/Database/`](file:///d:/ingestion_engine/docs/Database/README.md))
* **[Database Architecture & Context](file:///d:/ingestion_engine/docs/Database/README.md)**: Relational design, async `aioodbc` connection pooling, and multi-tier RBAC partitioning.
* **[Data Models & Entity Mappings](file:///d:/ingestion_engine/docs/Database/Datamodels/data_models_overview.md)**: Conceptual data models, domain entity hydration, and direct DTO projections.
* **[Table: `dbo.tbTradeBook`](file:///d:/ingestion_engine/docs/Database/Datamodels/tbTradeBook.md)**: Trade ledger table schema, column dictionaries, and monotonic sequence keys.
* **[Table: `dbo.Config_DealerMap`](file:///d:/ingestion_engine/docs/Database/Datamodels/Config_DealerMap.md)**: Multi-tenant dealer, account, terminal, and group mappings.
* **[Table: `dbo.UserAccount`](file:///d:/ingestion_engine/docs/Database/Datamodels/UserAccount.md)**: User credentials, SHA-512 binary password hashes, roles, and login auditing.
* **[Stored Procedure: `dbo.usp_GetTradeBook`](file:///d:/ingestion_engine/docs/Database/Stored%20Procedures/usp_GetTradeBook.md)**: Bidirectional keyset pagination, CTE query pipeline, lookahead boundary flags, and SQL test suite.
* **[Views: `dbo.vw_TradeBook`](file:///d:/ingestion_engine/docs/Database/Views/vw_TradeBook.md)**: Data abstraction view, physical decoupling, and indexing capabilities.

### 🧪 Unit Testing Documentation ([`docs/tests/`](file:///d:/ingestion_engine/docs/tests/README.md))
* **[Unit Testing Architecture & Suite Guide](file:///d:/ingestion_engine/docs/tests/README.md)**: Pure in-memory unit testing philosophy, mock ports, fixture catalog (`conftest.py`), test suite breakdown (`test_login.py`, `test_tradebook.py`), and test execution commands.

### 📐 System Architecture ([`docs/architecture.md`](file:///d:/ingestion_engine/docs/architecture.md))
* System architecture specification, Clean Architecture principles, CQRS patterns, and performance latency profiles.

---

## 2. Architecture Quick Summary

* **Clean Architecture**: Decoupled Domain, Application, Infrastructure, and Presentation layers.
* **Dual-Layer RBAC Security**:
  - Application Policy: [`TradeBookAccessPolicy`](file:///d:/ingestion_engine/src/features/Tradebook/Domain/policies/TradeBookAccessPolicy.py) prevents role escalation and cross-dealer snooping.
  - Database Engine Defense: [`dbo.usp_GetTradeBook`](file:///d:/ingestion_engine/sql/SP_Query.sql) independently enforces role predicates in SQL.
* **Read-Optimized Direct Projection**: Zero entity allocation overhead on high-volume trade queries; direct streaming from database rowsets into [`TradeBookPageOutDto`](file:///d:/ingestion_engine/src/features/Tradebook/Application/DTO/Outputs/TradeBookPageOutDto.py).

---

## 3. Running Unit Tests

Execute the 13 automated unit tests in-memory with `pytest`:

```bash
uv run python -m pytest
```
