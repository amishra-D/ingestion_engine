USE friskit_sample;
GO

CREATE OR ALTER PROCEDURE dbo.usp_GetTradeBook
(
    -- Access / Authorization
    @Role           VARCHAR(20),
    @UserId         VARCHAR(30) = NULL,
    @AccountCode    VARCHAR(30) = NULL,
    @GroupCode      VARCHAR(10) = NULL,

    -- Keyset Bidirectional Pagination
    @StartCursor    BIGINT = NULL,   -- Provided when navigating backward (PREV)
    @EndCursor      BIGINT = NULL,   -- Provided when navigating forward (NEXT)
    @Limit          INT = 10
)
AS
BEGIN
    SET NOCOUNT ON;

    -- 1. Clamp & sanitize limit
    IF @Limit IS NULL OR @Limit <= 0
        SET @Limit = 10;
    IF @Limit > 5000
        SET @Limit = 5000;

    -- Treat <= 0 or empty cursors as NULL
    IF @StartCursor <= 0 SET @StartCursor = NULL;
    IF @EndCursor <= 0 SET @EndCursor = NULL;

    -- 2. Determine pagination direction:
    --    - If @StartCursor is provided -> BACKWARD (previous page)
    --    - Else (if @EndCursor is provided or initial load) -> FORWARD (next page)
    DECLARE @IsBackward BIT = CASE WHEN @StartCursor IS NOT NULL THEN 1 ELSE 0 END;
    DECLARE @FetchLimit INT = @Limit + 1; -- +1 lookahead row to determine HasNext / HasPrev

    -- 3. Base filtered CTE applying RBAC & Cursor seek predicate
    ;WITH AuthorizedTrades AS (
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
        FROM dbo.vw_TradeBook TB
        WHERE
            -- RBAC Authorization Predicates
            (
                (@Role = 'ADMIN')
                OR (@Role = 'BROKER' AND TB.AccountCode = @AccountCode)
                OR (@Role = 'DEALER' AND TB.UserID = @UserId)
                OR (@Role = 'GROUP' AND EXISTS (
                    SELECT 1
                    FROM dbo.Config_DealerMap DM
                    WHERE DM.GroupCode = @GroupCode
                      AND DM.DealerCode = TB.UserID
                      AND DM.AccountCode = TB.AccountCode
                ))
            )
            -- Keyset Seek Predicates (Default sort is id DESC)
            AND (
                -- Forward pagination: seek older trades (id < @EndCursor)
                (@IsBackward = 0 AND (@EndCursor IS NULL OR TB.id < @EndCursor))
                -- Backward pagination: seek newer trades (id > @StartCursor)
                OR (@IsBackward = 1 AND TB.id > @StartCursor)
            )
    ),
    FetchedRows AS (
        SELECT TOP (@FetchLimit)
            *,
            ROW_NUMBER() OVER(
                ORDER BY
                    CASE WHEN @IsBackward = 1 THEN id END ASC,
                    CASE WHEN @IsBackward = 0 THEN id END DESC
            ) AS RowNum
        FROM AuthorizedTrades
        ORDER BY
            CASE WHEN @IsBackward = 1 THEN id END ASC,
            CASE WHEN @IsBackward = 0 THEN id END DESC
    ),
    PageWindow AS (
        -- Trim the extra lookahead row, keeping only @Limit rows
        SELECT *
        FROM FetchedRows
        WHERE RowNum <= @Limit
    ),
    SummaryMeta AS (
        SELECT
            COUNT(*) AS FetchedCount,
            -- StartCursor = Highest ID in page (first displayed row)
            CAST(MAX(id) AS NVARCHAR(50)) AS StartCursor,
            -- EndCursor = Lowest ID in page (last displayed row)
            CAST(MIN(id) AS NVARCHAR(50)) AS EndCursor
        FROM PageWindow
    )
    SELECT
        P.id,
        P.SQLDateTime,
        P.DateTime,
        P.TradeNum,
        P.OrderNum,
        P.UserID,
        P.TerminalID,
        P.CTCLID,
        P.AlgoID,
        P.AccountCode,
        P.MemberCode,
        P.ScripCode,
        P.Exchange,
        P.OptType,
        P.ExpiryDate,
        P.StrikePrice,
        P.ScripDescription,
        P.BuySellFlag,
        P.TradeQty,
        P.TradePrice,
        P.MainTradeID,
        P.SecurityType,
        P.ReferenceText,
        P.PendingQty,
        P.CustomID,

        -- Pagination edge cursors
        ISNULL(M.StartCursor, '') AS StartCursor,
        ISNULL(M.EndCursor, '') AS EndCursor,

        -- Calculate HasPrev and HasNext flags based on lookahead & direction
        CAST(
            CASE
                WHEN @IsBackward = 1 THEN
                    -- If we were going backward and found more than @Limit rows, there is still more backward
                    CASE WHEN (SELECT COUNT(*) FROM FetchedRows) > @Limit THEN 1 ELSE 0 END
                ELSE
                    -- If going forward, we have a previous page only if we started past an EndCursor
                    CASE WHEN @EndCursor IS NOT NULL THEN 1 ELSE 0 END
            END AS BIT
        ) AS HasPrev,

        CAST(
            CASE
                WHEN @IsBackward = 1 THEN
                    -- If going backward, we always have a next page (the page we came from)
                    1
                ELSE
                    -- If going forward, check if lookahead row exists
                    CASE WHEN (SELECT COUNT(*) FROM FetchedRows) > @Limit THEN 1 ELSE 0 END
            END AS BIT
        ) AS HasNext

    FROM PageWindow P
    CROSS JOIN SummaryMeta M
    ORDER BY P.id DESC;
END;
GO

-- =========================================================================
-- PRIVILEGE MANAGEMENT & RBAC VERIFICATION TEST SUITE
-- =========================================================================

-- -------------------------------------------------------------------------
-- 1. ADMIN PRIVILEGE TESTS (Full Access & Impersonation)
-- -------------------------------------------------------------------------
-- 1A. Admin sees ALL trades (Unrestricted audit query)
PRINT '>>> TEST 1A: ADMIN unrestricted query (all trades across entire firm)';
EXEC dbo.usp_GetTradeBook
    @Role = 'ADMIN',
    @Limit = 5;

-- 1B. Admin impersonates a specific Dealer view ('SUP')
PRINT '>>> TEST 1B: ADMIN filtering for Dealer SUP';
EXEC dbo.usp_GetTradeBook
    @Role = 'ADMIN',
    @UserId = 'SUP',
    @Limit = 5;

-- 1C. Admin impersonates a specific Broker Account ('90068')
PRINT '>>> TEST 1C: ADMIN filtering for Broker Account 90068';
EXEC dbo.usp_GetTradeBook
    @Role = 'ADMIN',
    @AccountCode = '90068',
    @Limit = 5;

-- 1D. Admin impersonates a specific Group ('HO')
PRINT '>>> TEST 1D: ADMIN filtering for Head Office Group HO';
EXEC dbo.usp_GetTradeBook
    @Role = 'ADMIN',
    @GroupCode = 'HO',
    @Limit = 5;


-- -------------------------------------------------------------------------
-- 2. BROKER PRIVILEGE TESTS (AccountCode Segregation)
-- -------------------------------------------------------------------------
-- 2A. Broker '90068' views all trades under their clearing account
-- Expected: Sees trades executed by dealers SUP, D001, D002 under account 90068
PRINT '>>> TEST 2A: BROKER 90068 query (all dealers under this account)';
EXEC dbo.usp_GetTradeBook
    @Role = 'BROKER',
    @AccountCode = '90068',
    @Limit = 5;

-- 2B. Broker '90069' views trades under their account
-- Expected: Sees trades executed by dealers D003, D004 under account 90069
PRINT '>>> TEST 2B: BROKER 90069 query';
EXEC dbo.usp_GetTradeBook
    @Role = 'BROKER',
    @AccountCode = '90069',
    @Limit = 5;

-- 2C. Broker '90068' inspects a specific dealer under their account ('SUP')
PRINT '>>> TEST 2C: BROKER 90068 inspecting specific dealer SUP';
EXEC dbo.usp_GetTradeBook
    @Role = 'BROKER',
    @AccountCode = '90068',
    @UserId = 'SUP',
    @Limit = 5;

-- 2D. Broker querying without AccountCode
-- Expected: 0 rows returned (security safeguard: AccountCode is required)
PRINT '>>> TEST 2D: BROKER without AccountCode (Expected: 0 rows)';
EXEC dbo.usp_GetTradeBook
    @Role = 'BROKER',
    @AccountCode = NULL,
    @Limit = 5;


-- -------------------------------------------------------------------------
-- 3. DEALER PRIVILEGE TESTS (Individual Terminal Segregation)
-- -------------------------------------------------------------------------
-- 3A. Dealer 'SUP' queries their own tradebook
-- Expected: Returns strictly trades where UserID = 'SUP'
PRINT '>>> TEST 3A: DEALER SUP querying own trades';
EXEC dbo.usp_GetTradeBook
    @Role = 'DEALER',
    @UserId = 'SUP',
    @Limit = 5;

-- 3B. Dealer 'D001' queries their own tradebook
-- Expected: Returns strictly trades where UserID = 'D001'
PRINT '>>> TEST 3B: DEALER D001 querying own trades';
EXEC dbo.usp_GetTradeBook
    @Role = 'DEALER',
    @UserId = 'D001',
    @Limit = 5;

-- 3C. Dealer querying without UserId
-- Expected: 0 rows returned (security safeguard: UserID is required)
PRINT '>>> TEST 3C: DEALER without UserId (Expected: 0 rows)';
EXEC dbo.usp_GetTradeBook
    @Role = 'DEALER',
    @UserId = NULL,
    @Limit = 5;


-- -------------------------------------------------------------------------
-- 4. GROUP PRIVILEGE TESTS (Branch / Head Office Mapping via Config_DealerMap)
-- -------------------------------------------------------------------------
-- 4A. Group 'HO' (Head Office)
-- Expected: Sees trades for mapped dealers (SUP, D001, D002, D003) under mapped accounts (90068, 90069)
PRINT '>>> TEST 4A: GROUP HO (Head Office - mapped to dealers SUP, D001, D002, D003)';
EXEC dbo.usp_GetTradeBook
    @Role = 'GROUP',
    @GroupCode = 'HO',
    @Limit = 5;

-- 4B. Group 'GRP2' (Branch 2)
-- Expected: Sees trades for mapped dealer D004 under account 90069
PRINT '>>> TEST 4B: GROUP GRP2 (Branch 2 - mapped to dealer D004)';
EXEC dbo.usp_GetTradeBook
    @Role = 'GROUP',
    @GroupCode = 'GRP2',
    @Limit = 5;

-- 4C. Non-existent Group
-- Expected: 0 rows returned
PRINT '>>> TEST 4C: Non-existent GROUP UNKNOWN (Expected: 0 rows)';
EXEC dbo.usp_GetTradeBook
    @Role = 'GROUP',
    @GroupCode = 'UNKNOWN',
    @Limit = 5;


-- -------------------------------------------------------------------------
-- 5. COMBINED RBAC + KEYSET PAGINATION TESTS
-- -------------------------------------------------------------------------
-- 5A. Forward seek (Next Page for Broker 90068 after EndCursor)
PRINT '>>> TEST 5A: BROKER 90068 Forward Seek (Next Page after EndCursor = 5000)';
EXEC dbo.usp_GetTradeBook
    @Role = 'BROKER',
    @AccountCode = '90068',
    @EndCursor = 5000,
    @Limit = 5;

-- 5B. Backward seek (Previous Page for Dealer SUP before StartCursor)
PRINT '>>> TEST 5B: DEALER SUP Backward Seek (Prev Page before StartCursor = 4000)';
EXEC dbo.usp_GetTradeBook
    @Role = 'DEALER',
    @UserId = 'SUP',
    @StartCursor = 4000,
    @Limit = 5;
GO