# Table Specification: `dbo.UserAccount`

## 1. Description & Purpose

`dbo.UserAccount` is the primary identity, credentials, and security role store for all platform actors. It powers:
* Operator authentication via username and SHA-512 password hash verification.
* Role-Based Access Control (RBAC) role assignment (`ADMIN`, `BROKER`, `DEALER`, `GROUP`).
* Account status enforcement (`isActive`).
* Audit trail tracking (`CreatedAt`, `UpdatedAt`, `LastLoginAt`).

---

## 2. DDL Definition

Source: [`sql/Tables_DDL_queries.sql`](file:///d:/ingestion_engine/sql/Tables_DDL_queries.sql#L72-L84)

```sql
CREATE TABLE dbo.UserAccount
(
    UserId         INT IDENTITY(1,1) NOT NULL,
    Username       VARCHAR(50) NOT NULL,
    PasswordHash   BINARY(64) NOT NULL,
    Role           VARCHAR(20) NOT NULL 
                   CONSTRAINT DF_UserAccount_Role DEFAULT 'DEALER',
    isActive       BIT NOT NULL 
                   CONSTRAINT DF_UserAccount_isActive DEFAULT 1,
    CreatedAt      DATETIME2(3) NOT NULL 
                   CONSTRAINT DF_UserAccount_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt      DATETIME2(3) NOT NULL 
                   CONSTRAINT DF_UserAccount_UpdatedAt DEFAULT SYSUTCDATETIME(),
    LastLoginAt    DATETIME2(3) NOT NULL 
                   CONSTRAINT DF_UserAccount_LastLoginAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_UserAccount PRIMARY KEY CLUSTERED (UserId),
    CONSTRAINT UQ_UserAccount_Username UNIQUE (Username)
);
GO
```

---

## 3. Detailed Column Dictionary

| Column Name | Data Type | Nullable | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| **`UserId`** | `INT IDENTITY(1,1)` | **No** | Auto | Primary key surrogate identifier for the user account. |
| **`Username`** | `VARCHAR(50)` | **No** | None | Unique login username. Unique index target for fast lookups. |
| **`PasswordHash`**| `BINARY(64)` | **No** | None | 64-byte raw binary cryptographic hash generated via SHA-512 (`HASHBYTES('SHA2_512', password)`). |
| **`Role`** | `VARCHAR(20)` | **No** | `'DEALER'` | Assigned RBAC role: `'ADMIN'`, `'BROKER'`, `'DEALER'`, or `'GROUP'`. |
| **`isActive`** | `BIT` | **No** | `1` | Account state flag (`1` = active, `0` = locked / deactivated). |
| **`CreatedAt`** | `DATETIME2(3)` | **No** | `SYSUTCDATETIME()` | Account creation UTC timestamp with 3 decimal precision. |
| **`UpdatedAt`** | `DATETIME2(3)` | **No** | `SYSUTCDATETIME()` | Account modification UTC timestamp. |
| **`LastLoginAt`** | `DATETIME2(3)` | **No** | `SYSUTCDATETIME()` | Timestamp of the most recent successful login event. |

---

## 4. Key Constraints & Security Details

1. **Clustered Primary Key (`PK_UserAccount`)**:
   - Clustered on `UserId`.
2. **Unique Username Index (`UQ_UserAccount_Username`)**:
   - Ensures no duplicate usernames exist across the system.
   - Powers the fast single-row index seek during login:
     ```sql
     SELECT UserId, Username, PasswordHash, Role, isActive, CreatedAt, UpdatedAt, LastLoginAt
     FROM [dbo].[UserAccount]
     WHERE Username = ?;
     ```
3. **Cryptographic Password Storage**:
   - Stored strictly as **`BINARY(64)`**, representing the raw 512-bit digest output of SHA-512.
   - In SQL Server seeding:
     ```sql
     HASHBYTES('SHA2_512', 'admin123')
     ```
   - In Python validation ([`UserAccount.verify_password`](file:///d:/ingestion_engine/src/features/Auth/Domain/entities/user_account.py#L18-L21)):
     ```python
     computed_hash = hashlib.sha512(plain_password.encode("utf-8")).digest()
     return hmac.compare_digest(self.password_hash, computed_hash)
     ```
   - The use of `hmac.compare_digest` guarantees constant-time comparison, eliminating timing attack vulnerabilities.

---

## 5. Lifecycle Updates

Upon successful credential validation, the application updates `LastLoginAt` and `UpdatedAt` asynchronously via [`LoginRepository.update_last_login()`](file:///d:/ingestion_engine/src/features/Auth/Infrastructure/repositories/LoginRepository.py#L34-L42):

```sql
UPDATE [dbo].[UserAccount]
SET LastLoginAt = SYSUTCDATETIME(),
    UpdatedAt = SYSUTCDATETIME()
WHERE UserId = ?;
```
