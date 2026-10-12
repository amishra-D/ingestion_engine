create database friskit_sample
go
use friskit_sample
go
CREATE TABLE dbo.tbTradeBook
(
    id              INT IDENTITY(1,1) NOT NULL,
    SQLDateTime     NVARCHAR(80) NOT NULL,
    DateTime        NVARCHAR(80) NOT NULL,
    TradeNum        NVARCHAR(80) NOT NULL,
    OrderNum        NVARCHAR(80) NOT NULL,
    UserID          NVARCHAR(20) NOT NULL,
    TerminalID      NVARCHAR(20) NOT NULL,
    CTCLID          NVARCHAR(20) NOT NULL,
    AlgoID          NVARCHAR(20) NOT NULL,
    AccountCode     NVARCHAR(20) NOT NULL,
    MemberCode      NVARCHAR(20) NOT NULL,
    ScripCode       NVARCHAR(20) NOT NULL,
    Exchange        NVARCHAR(20) NOT NULL,
    OptType         NVARCHAR(20) NOT NULL,
    ExpiryDate      NVARCHAR(80) NOT NULL,
    StrikePrice     NUMERIC(20,6) NOT NULL,
    ScripDescription NVARCHAR(80) NOT NULL,
    BuySellFlag     NVARCHAR(4) NOT NULL,
    TradeQty        INT NOT NULL,
    TradePrice      NUMERIC(20,6) NOT NULL,
    MainTradeID     INT NOT NULL,
    SecurityType    NVARCHAR(20) NOT NULL,
    ReferenceText   NVARCHAR(50) NOT NULL,
    PendingQty      INT NOT NULL,
    CustomID        INT NULL,
    CONSTRAINT PK_tbTradeBook
        PRIMARY KEY CLUSTERED (id)
);
GO
USE friskit_sample;
GO

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

USE friskit_sample;
GO

CREATE TABLE dbo.UserAccount
(
    UserId         INT IDENTITY(1,1) NOT NULL,
    Username       VARCHAR(50) NOT NULL,
    PasswordHash   BINARY(64) NOT NULL,
    Role           VARCHAR(20) NOT NULL CONSTRAINT DF_UserAccount_Role DEFAULT 'DEALER',
    isActive       BIT NOT NULL CONSTRAINT DF_UserAccount_isActive DEFAULT 1,
    CreatedAt      DATETIME2(3) NOT NULL CONSTRAINT DF_UserAccount_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt      DATETIME2(3) NOT NULL CONSTRAINT DF_UserAccount_UpdatedAt DEFAULT SYSUTCDATETIME(),
    LastLoginAt    DATETIME2(3) NOT NULL CONSTRAINT DF_UserAccount_LastLoginAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_UserAccount PRIMARY KEY CLUSTERED (UserId),
    CONSTRAINT UQ_UserAccount_Username UNIQUE (Username)
);
GO