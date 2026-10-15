# Table Specification: `dbo.Config_DealerMap`

## 1. Description & Purpose

`dbo.Config_DealerMap` defines the multi-tenant organizational structure of the trading platform. It establishes the mapping between market execution entities:
* Which **Exchange** and **Terminal** a dealer uses
* Which clearing **AccountCode** (Broker) the dealer belongs to
* Which administrative **GroupCode** has visibility over the dealer
* Whether the dealer operates under **Custodian** status

This table is critical for **Tier 3 (GROUP)** and **Tier 2 (BROKER)** RBAC enforcement in [`dbo.usp_GetTradeBook`](file:///d:/ingestion_engine/sql/SP_Query.sql#L72-L78).

---

## 2. DDL Definition

Source: [`sql/Tables_DDL_queries.sql`](file:///d:/ingestion_engine/sql/Tables_DDL_queries.sql#L39-L66)

```sql
CREATE TABLE dbo.Config_DealerMap
(
    DealerMap_ID      UNIQUEIDENTIFIER NOT NULL
                      CONSTRAINT DF_Config_DealerMap_DealerMap_ID
                      DEFAULT NEWSEQUENTIALID(),
    Exchange          VARCHAR(12) NOT NULL,
    TerminalID        VARCHAR(30) NOT NULL,
    DealerName        VARCHAR(50) NULL,
    DealerCode        VARCHAR(30) NOT NULL,
    LastUpdateTime    DATETIME2(3) NOT NULL
                      CONSTRAINT DF_Config_DealerMap_LastUpdateTime
                      DEFAULT SYSUTCDATETIME(),
    GroupCode         VARCHAR(10) NULL,
    AccountCode       VARCHAR(30) NOT NULL,
    IsCustodian       BIT NOT NULL
                      CONSTRAINT DF_Config_DealerMap_IsCustodian
                      DEFAULT 0,
    CONSTRAINT PK_Config_DealerMap
        PRIMARY KEY CLUSTERED (DealerMap_ID),
    CONSTRAINT UQ_Config_DealerMap
        UNIQUE
        (
            Exchange,
            TerminalID,
            AccountCode,
            DealerCode
        )
);
GO
```

---

## 3. Detailed Column Dictionary

| Column Name | Data Type | Nullable | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| **`DealerMap_ID`** | `UNIQUEIDENTIFIER` | **No** | `NEWSEQUENTIALID()` | Primary Key UUID, generated sequentially for optimal clustered B-tree insertion. |
| **`Exchange`** | `VARCHAR(12)` | **No** | None | Exchange identifier (e.g., `'NSE'`, `'BSE'`). |
| **`TerminalID`** | `VARCHAR(30)` | **No** | None | Physical / virtual terminal workstation ID (e.g., `'TERM001'`). |
| **`DealerName`** | `VARCHAR(50)` | **Yes** | `NULL` | Full human-readable name of the dealer operator. |
| **`DealerCode`** | `VARCHAR(30)` | **No** | None | Business dealer code matching `tbTradeBook.UserID` (e.g., `'SUP'`, `'D001'`). |
| **`LastUpdateTime`**| `DATETIME2(3)` | **No** | `SYSUTCDATETIME()`| Timestamp of the last configuration update in UTC. |
| **`GroupCode`** | `VARCHAR(10)` | **Yes** | `NULL` | Group classification tag for branch or desk reporting (e.g., `'HO'`, `'GRP2'`). |
| **`AccountCode`** | `VARCHAR(30)` | **No** | None | Broker clearing account code matching `tbTradeBook.AccountCode` (e.g., `'90068'`). |
| **`IsCustodian`** | `BIT` | **No** | `0` | Flag indicating whether the entity operates as a custodian participant (`1`) or direct participant (`0`). |

---

## 4. Key Constraints & Business Invariants

1. **Clustered Primary Key (`PK_Config_DealerMap`)**:
   - Clustered on `DealerMap_ID`. Uses `NEWSEQUENTIALID()` to avoid page-split fragmentation typical of random UUIDs.
2. **Unique Composite Constraint (`UQ_Config_DealerMap`)**:
   - Columns: `(Exchange, TerminalID, AccountCode, DealerCode)`.
   - Prevents duplicate mappings for the same dealer on a specific terminal and account.
3. **RBAC Join Predicate**:
   - In stored procedure queries for `Role = 'GROUP'`:
     ```sql
     EXISTS (
         SELECT 1
         FROM dbo.Config_DealerMap DM
         WHERE DM.GroupCode = @GroupCode
           AND DM.DealerCode = TB.UserID
           AND DM.AccountCode = TB.AccountCode
     )
     ```

---

## 5. Seed Data Baseline

Source: [`sql/seed_query.sql`](file:///d:/ingestion_engine/sql/seed_query.sql#L1-L17)

| TerminalID | DealerCode | DealerName | GroupCode | AccountCode | Exchange | IsCustodian |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| `TERM001` | `SUP` | SUP Dealer | `HO` | `90068` | `NSE` | `0` |
| `TERM002` | `D001` | Dealer One | `HO` | `90068` | `NSE` | `0` |
| `TERM003` | `D002` | Dealer Two | `HO` | `90068` | `NSE` | `0` |
| `TERM004` | `D003` | Dealer Three | `HO` | `90069` | `NSE` | `0` |
| `TERM005` | `D004` | Dealer Four | `GRP2` | `90069` | `NSE` | `0` |
