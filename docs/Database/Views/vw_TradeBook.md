# Views Architecture & `dbo.vw_TradeBook`

## 1. Role of Views in the System

In the Ingestion Engine architecture, SQL Server Views act as a decoupling layer between physical storage tables and application query mechanisms (such as stored procedures and reporting endpoints).

Specifically, [`dbo.usp_GetTradeBook`](file:///d:/ingestion_engine/sql/SP_Query.sql#L65) does not query `dbo.tbTradeBook` directly; instead, it executes against the abstraction view **`dbo.vw_TradeBook`**:

```sql
;WITH AuthorizedTrades AS (
    SELECT
        TB.id,
        TB.SQLDateTime,
        ...
    FROM dbo.vw_TradeBook TB
    WHERE ...
)
```

```mermaid
flowchart LR
    Caller["Application Client<br/>GetTradeRepository"] --> SP["Stored Procedure<br/>dbo.usp_GetTradeBook"]
    SP --> View["View Abstraction<br/>dbo.vw_TradeBook"]
    View --> Table["Physical Storage Table<br/>dbo.tbTradeBook"]
```

---

## 2. Definition & DDL Specification

The baseline view definition mirrors the physical schema of [`dbo.tbTradeBook`](file:///d:/ingestion_engine/sql/Tables_DDL_queries.sql#L5-L34), projecting the active columns required for trade book presentation:

```sql
USE friskit_sample;
GO

CREATE OR ALTER VIEW dbo.vw_TradeBook
AS
SELECT
    TB.id,
    TB.SQLDateTime,
    TB.DateTime,
    TB.TradeNum,
    TB.OrderNum,
    TB.UserID,
    TB.TerminalID,
    TB.CTCLID,
    TB.AlgoID,
    TB.AccountCode,
    TB.MemberCode,
    TB.ScripCode,
    TB.Exchange,
    TB.OptType,
    TB.ExpiryDate,
    TB.StrikePrice,
    TB.ScripDescription,
    TB.BuySellFlag,
    TB.TradeQty,
    TB.TradePrice,
    TB.MainTradeID,
    TB.SecurityType,
    TB.ReferenceText,
    TB.PendingQty,
    TB.CustomID
FROM dbo.tbTradeBook TB;
GO
```

---

## 3. Architectural Rationale & Benefits

### 3.1 Schema Decoupling & Physical Independence
* **Storage Isolation**: Physical table changes (such as column renames, internal audit fields, compression options, or data type migrations) can be adapted inside the view without modifying stored procedure contracts or Python application code.
* **Hot Partitioning / Archiving**: If `dbo.tbTradeBook` is partitioned into active (intraday) and historical (archived) tables, `vw_TradeBook` can act as a `UNION ALL` partitioned view to provide seamless transparent queries across historical and live trade logs.

### 3.2 Dynamic Data Masking & Column Scoping
* Views allow enforcing column-level security or formatting adjustments (e.g. masking sensitive clearing account segments or standardizing timestamp formatting) before data reaches consumers.

### 3.3 Indexed (Materialized) View Capabilities
In SQL Server Enterprise editions, if high-volume aggregate queries or join lookups are required, a view created `WITH SCHEMABINDING` can support a unique clustered index, materializing pre-computed result sets to disk while keeping update operations transparent.

---

## 4. Performance Considerations

* **Query Optimizer Inlining**: Simple 1:1 projection views in SQL Server are inlined directly into the query execution tree. There is **zero performance penalty** compared to selecting directly from `dbo.tbTradeBook`.
* **Index Inheritance**: The underlying clustered index on `dbo.tbTradeBook(id)` is utilized directly during seek operations (`TB.id < @EndCursor` or `TB.id > @StartCursor`).
* **Clean Boundary Rule**: The application code strictly uses `dbo.vw_TradeBook` through `dbo.usp_GetTradeBook`, ensuring no ad-hoc SQL queries bypass the abstraction layer.
