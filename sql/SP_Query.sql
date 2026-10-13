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