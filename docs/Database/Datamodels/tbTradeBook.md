# Table Specification: `dbo.tbTradeBook`

## 1. Description & Purpose

`dbo.tbTradeBook` is the high-volume transaction ledger of the trading platform. It logs individual trade executions received from market feeds or produced by the simulated ingestion engine.

The table is designed for high insert throughput, append-only persistence, and high-frequency keyset-paginated read queries.

---

## 2. DDL Definition

Source: [`sql/Tables_DDL_queries.sql`](file:///d:/ingestion_engine/sql/Tables_DDL_queries.sql#L5-L34)

```sql
CREATE TABLE dbo.tbTradeBook
(
    id               INT IDENTITY(1,1) NOT NULL,
    SQLDateTime      NVARCHAR(80) NOT NULL,
    DateTime         NVARCHAR(80) NOT NULL,
    TradeNum         NVARCHAR(80) NOT NULL,
    OrderNum         NVARCHAR(80) NOT NULL,
    UserID           NVARCHAR(20) NOT NULL,
    TerminalID       NVARCHAR(20) NOT NULL,
    CTCLID           NVARCHAR(20) NOT NULL,
    AlgoID           NVARCHAR(20) NOT NULL,
    AccountCode      NVARCHAR(20) NOT NULL,
    MemberCode       NVARCHAR(20) NOT NULL,
    ScripCode        NVARCHAR(20) NOT NULL,
    Exchange         NVARCHAR(20) NOT NULL,
    OptType          NVARCHAR(20) NOT NULL,
    ExpiryDate       NVARCHAR(80) NOT NULL,
    StrikePrice      NUMERIC(20,6) NOT NULL,
    ScripDescription NVARCHAR(80) NOT NULL,
    BuySellFlag      NVARCHAR(4) NOT NULL,
    TradeQty         INT NOT NULL,
    TradePrice       NUMERIC(20,6) NOT NULL,
    MainTradeID      INT NOT NULL,
    SecurityType     NVARCHAR(20) NOT NULL,
    ReferenceText    NVARCHAR(50) NOT NULL,
    PendingQty       INT NOT NULL,
    CustomID         INT NULL,
    CONSTRAINT PK_tbTradeBook PRIMARY KEY CLUSTERED (id)
);
GO
```

---

## 3. Detailed Column Dictionary

| Column Name | Data Type | Nullable | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| **`id`** | `INT IDENTITY(1,1)` | **No** | Auto | Primary key and surrogate identifier. Clustered index anchor for pagination. |
| **`SQLDateTime`** | `NVARCHAR(80)` | **No** | None | Database system timestamp string when trade record was written. |
| **`DateTime`** | `NVARCHAR(80)` | **No** | None | Exchange trade execution timestamp string. |
| **`TradeNum`** | `NVARCHAR(80)` | **No** | None | Unique trade reference number issued by the exchange. |
| **`OrderNum`** | `NVARCHAR(80)` | **No** | None | Exchange order reference number associated with the trade. |
| **`UserID`** | `NVARCHAR(20)` | **No** | None | Dealer or trader identifier who placed the order (e.g., `'SUP'`, `'D001'`). |
| **`TerminalID`** | `NVARCHAR(20)` | **No** | None | Terminal device code that initiated the trade (e.g., `'TERM001'`). |
| **`CTCLID`** | `NVARCHAR(20)` | **No** | None | Computer-to-Computer Link ID assigned by the exchange. |
| **`AlgoID`** | `NVARCHAR(20)` | **No** | None | Algorithmic trading strategy or engine identifier. |
| **`AccountCode`** | `NVARCHAR(20)` | **No** | None | Clearing / Broker account identifier (e.g., `'90068'`). |
| **`MemberCode`** | `NVARCHAR(20)` | **No** | None | Clearing member firm identifier (e.g., `'MEM001'`). |
| **`ScripCode`** | `NVARCHAR(20)` | **No** | None | Traded asset symbol (e.g., `'NIFTY'`, `'BANKNIFTY'`). |
| **`Exchange`** | `NVARCHAR(20)` | **No** | None | Exchange market identifier (e.g., `'NSE'`, `'BSE'`). |
| **`OptType`** | `NVARCHAR(20)` | **No** | None | Option contract type: `'CE'` (Call), `'PE'` (Put), or `'XX'`. |
| **`ExpiryDate`** | `NVARCHAR(80)` | **No** | None | Contract expiration date (e.g., `'2026-10-29'`). |
| **`StrikePrice`** | `NUMERIC(20,6)` | **No** | None | Contract strike price with 6 decimal places. |
| **`ScripDescription`** | `NVARCHAR(80)` | **No** | None | Human-readable contract description (e.g., `'NIFTY 25000 CE'`). |
| **`BuySellFlag`** | `NVARCHAR(4)` | **No** | None | Side indicator: `'BUY'` or `'SELL'`. |
| **`TradeQty`** | `INT` | **No** | None | Number of units / shares executed in this trade. |
| **`TradePrice`** | `NUMERIC(20,6)` | **No** | None | Execution price per unit with 6 decimal places. |
| **`MainTradeID`** | `INT` | **No** | None | Monotonically increasing external trade sequence identifier. |
| **`SecurityType`** | `NVARCHAR(20)` | **No** | None | Security classification (e.g., `'FUTOPT'`, `'EQUITY'`). |
| **`ReferenceText`** | `NVARCHAR(50)` | **No** | None | Operational tag or ingestion marker (e.g., `'SEED'`, `'LIVE'`). |
| **`PendingQty`** | `INT` | **No** | None | Unfilled remaining quantity of the parent order. |
| **`CustomID`** | `INT` | **Yes** | `NULL` | Optional client-defined tracking identifier. |

---

## 4. Key Constraints & Indexing

1. **Clustered Primary Key (`PK_tbTradeBook`)**:
   - Column: `id ASC`
   - Enables fast seeks for keyset pagination where queries seek older rows (`id < @EndCursor`) or newer rows (`id > @StartCursor`).
2. **Access Patterns & Recommended Non-Clustered Indexes**:
   - **Dealer Queries**: Index on `(UserID, id DESC)` to avoid full table scans when `Role = 'DEALER'`.
   - **Broker Queries**: Index on `(AccountCode, id DESC)` for broker-scoped queries.
   - **Group Queries**: Compound index supporting the join/lookup with `dbo.Config_DealerMap`.

---

## 5. Ingestion Engine Interaction

The background ingestion worker in [`src/ingestion_engine/engine.py`](file:///d:/ingestion_engine/src/ingestion_engine/engine.py) performs the following database operations on `dbo.tbTradeBook`:

1. **Counter Initialization**:
   ```sql
   SELECT COALESCE(MAX(MainTradeID), 0) FROM dbo.tbTradeBook;
   ```
2. **Batch Generation**:
   Generates synthetic records conforming strictly to valid dealer codes, accounts, and option strike steps.
3. **Continuous Insertion**:
   Issues batched inserts to simulate live market execution.
