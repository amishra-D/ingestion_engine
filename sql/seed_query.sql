INSERT INTO dbo.Config_DealerMap
(
    Exchange,
    TerminalID,
    DealerName,
    DealerCode,
    LastUpdateTime,
    GroupCode,
    AccountCode,
    IsCustodian
)
VALUES
('NSE', 'TERM001', 'SUP Dealer',    'SUP',  GETDATE(), 'HO', '90068', 0),
('NSE', 'TERM002', 'Dealer One',    'D001', GETDATE(), 'HO', '90068', 0),
('NSE', 'TERM003', 'Dealer Two',    'D002', GETDATE(), 'HO', '90068', 0),
('NSE', 'TERM004', 'Dealer Three',  'D003', GETDATE(), 'HO', '90069', 0),
('NSE', 'TERM005', 'Dealer Four',   'D004', GETDATE(), 'GRP2', '90069', 0);

USE friskit_sample;
GO

INSERT INTO dbo.tbTradeBook
(
    SQLDateTime,
    DateTime,
    TradeNum,
    OrderNum,
    UserID,
    TerminalID,
    CTCLID,
    AlgoID,
    AccountCode,
    MemberCode,
    ScripCode,
    Exchange,
    OptType,
    ExpiryDate,
    StrikePrice,
    ScripDescription,
    BuySellFlag,
    TradeQty,
    TradePrice,
    MainTradeID,
    SecurityType,
    ReferenceText,
    PendingQty,
    CustomID
)
VALUES

-- ============================================
-- BROKER 90068 / DEALER SUP
-- ============================================
(
    '2026-10-08 09:15:01.100',
    '2026-10-08 09:15:01.100',
    'TRD0001',
    'ORD0001',
    'SUP',
    'TERM001',
    'CTCL001',
    'ALGO001',
    '90068',
    'MEM001',
    'NIFTY',
    'NSE',
    'CE',
    '2026-10-29',
    25000.000000,
    'NIFTY 25000 CE',
    'BUY',
    100,
    250.500000,
    1,
    'FUTOPT',
    'SEED',
    0,
    NULL
),

(
    '2026-10-08 09:15:02.100',
    '2026-10-08 09:15:02.100',
    'TRD0002',
    'ORD0002',
    'SUP',
    'TERM001',
    'CTCL001',
    'ALGO001',
    '90068',
    'MEM001',
    'NIFTY',
    'NSE',
    'CE',
    '2026-10-29',
    25000.000000,
    'NIFTY 25000 CE',
    'SELL',
    50,
    255.200000,
    2,
    'FUTOPT',
    'SEED',
    0,
    NULL
),

-- ============================================
-- BROKER 90068 / DEALER D001
-- ============================================
(
    '2026-10-08 09:16:01.100',
    '2026-10-08 09:16:01.100',
    'TRD0003',
    'ORD0003',
    'D001',
    'TERM002',
    'CTCL002',
    'ALGO001',
    '90068',
    'MEM001',
    'BANKNIFTY',
    'NSE',
    'PE',
    '2026-10-29',
    55000.000000,
    'BANKNIFTY 55000 PE',
    'BUY',
    200,
    310.500000,
    3,
    'FUTOPT',
    'SEED',
    0,
    NULL
),

-- ============================================
-- BROKER 90068 / DEALER D002
-- ============================================
(
    '2026-10-08 09:17:01.100',
    '2026-10-08 09:17:01.100',
    'TRD0004',
    'ORD0004',
    'D002',
    'TERM003',
    'CTCL003',
    'ALGO001',
    '90068',
    'MEM001',
    'NIFTY',
    'NSE',
    'CE',
    '2026-10-29',
    25100.000000,
    'NIFTY 25100 CE',
    'SELL',
    75,
    180.250000,
    4,
    'FUTOPT',
    'SEED',
    0,
    NULL
),

-- ============================================
-- BROKER 90069 / DEALER D003
-- ============================================
(
    '2026-10-08 09:18:01.100',
    '2026-10-08 09:18:01.100',
    'TRD0005',
    'ORD0005',
    'D003',
    'TERM004',
    'CTCL004',
    'ALGO001',
    '90069',
    'MEM001',
    'NIFTY',
    'NSE',
    'PE',
    '2026-10-29',
    25000.000000,
    'NIFTY 25000 PE',
    'BUY',
    100,
    220.100000,
    5,
    'FUTOPT',
    'SEED',
    0,
    NULL
),

-- ============================================
-- BROKER 90069 / DEALER D004
-- ============================================
(
    '2026-10-08 09:19:01.100',
    '2026-10-08 09:19:01.100',
    'TRD0006',
    'ORD0006',
    'D004',
    'TERM005',
    'CTCL005',
    'ALGO001',
    '90069',
    'MEM001',
    'BANKNIFTY',
    'NSE',
    'CE',
    '2026-10-29',
    55000.000000,
    'BANKNIFTY 55000 CE',
    'SELL',
    150,
    340.750000,
    6,
    'FUTOPT',
    'SEED',
    0,
    NULL
);
GO

-- ============================================
-- SEED USER ACCOUNTS (Passwords: 'admin123', 'dealer123')
-- ============================================
INSERT INTO dbo.UserAccount (Username, PasswordHash, Role, isActive)
VALUES 
('admin', HASHBYTES('SHA2_512', 'admin123'), 'ADMIN', 1),
('SUP', HASHBYTES('SHA2_512', 'dealer123'), 'DEALER', 1),
('D001', HASHBYTES('SHA2_512', 'dealer123'), 'DEALER', 1),
('broker1', HASHBYTES('SHA2_512', 'broker123'), 'BROKER', 1);
GO