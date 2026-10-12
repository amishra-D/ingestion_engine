use friskit_sample
go
CREATE OR ALTER PROCEDURE dbo.usp_GetTradeBook
(
    -- =========================================================
    -- ACCESS / AUTHORIZATION
    -- =========================================================
    @Role                   VARCHAR(20),
    @UserID                 VARCHAR(30) = NULL,
    @AccountCode            VARCHAR(30) = NULL,
    @GroupCode              VARCHAR(10) = NULL,

    -- =========================================================
    -- COLUMN / FILTER CONTROL
    -- =========================================================
    @ColDef                 VARCHAR(MAX) = NULL,
    @FilterClause           VARCHAR(MAX) = NULL,
    @DynamicValues          VARCHAR(MAX) = NULL,

    -- =========================================================
    -- SORTING
    -- =========================================================
    @OrderByClause          VARCHAR(MAX) = NULL,
    @ReverseOrderByClause   VARCHAR(MAX) = NULL,

    -- =========================================================
    -- TOKEN / CURSOR
    -- =========================================================
    @TokenColumns           VARCHAR(MAX) = NULL,
    @CursorID               BIGINT = NULL,

    -- =========================================================
    -- PAGINATION
    -- =========================================================
    @Limit                  INT = 50,
    @Direction              VARCHAR(10) = 'NEXT',
    @HasCursor              BIT = 0
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @ReturnCode INT = 0;

    BEGIN TRY

        /* =====================================================
           1. VALIDATE BASIC PARAMETERS
           ===================================================== */

        IF @Role NOT IN
        (
            'ADMIN',
            'BROKER',
            'DEALER',
            'GROUP'
        )
        BEGIN
            RETURN 1001;
        END;


        IF @Limit IS NULL OR @Limit <= 0
            SET @Limit = 50;

        IF @Limit > 5000
            SET @Limit = 5000;


        IF @Direction NOT IN ('NEXT', 'PREVIOUS')
        BEGIN
            RETURN 1002;
        END;


        /* =====================================================
           2. VALIDATE ACCESS PARAMETERS
           ===================================================== */

        IF @Role = 'DEALER'
           AND @UserID IS NULL
        BEGIN
            RETURN 1003;
        END;


        IF @Role = 'BROKER'
           AND @AccountCode IS NULL
        BEGIN
            RETURN 1004;
        END;


        IF @Role = 'GROUP'
           AND @GroupCode IS NULL
        BEGIN
            RETURN 1005;
        END;


        /* =====================================================
           3. DEFAULT COLUMN LIST
           ===================================================== */

        DECLARE @Columns NVARCHAR(MAX);

        SET @Columns =
        N'
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
        ';


        /* =====================================================
           4. OPTIONAL COLUMN SELECTION
           
           IMPORTANT:
           @ColDef is NOT blindly inserted into SQL.
           Only known columns are allowed.
           ===================================================== */

        IF @ColDef IS NOT NULL
        BEGIN

            SET @Columns = '';

            DECLARE @ColumnName VARCHAR(100);

            DECLARE ColumnCursor CURSOR LOCAL FAST_FORWARD
            FOR
                SELECT LTRIM(RTRIM(value))
                FROM STRING_SPLIT(@ColDef, ',');

            OPEN ColumnCursor;

            FETCH NEXT FROM ColumnCursor
            INTO @ColumnName;

            WHILE @@FETCH_STATUS = 0
            BEGIN

                IF @ColumnName IN
                (
                    'id',
                    'SQLDateTime',
                    'DateTime',
                    'TradeNum',
                    'OrderNum',
                    'UserID',
                    'TerminalID',
                    'CTCLID',
                    'AlgoID',
                    'AccountCode',
                    'MemberCode',
                    'ScripCode',
                    'Exchange',
                    'OptType',
                    'ExpiryDate',
                    'StrikePrice',
                    'ScripDescription',
                    'BuySellFlag',
                    'TradeQty',
                    'TradePrice',
                    'MainTradeID',
                    'SecurityType',
                    'ReferenceText',
                    'PendingQty',
                    'CustomID'
                )
                BEGIN

                    IF @Columns <> ''
                        SET @Columns = @Columns + ', ';

                    SET @Columns =
                        @Columns + 'TB.' + QUOTENAME(@ColumnName);

                END
                ELSE
                BEGIN
                    CLOSE ColumnCursor;
                    DEALLOCATE ColumnCursor;

                    RETURN 1006;
                END;

                FETCH NEXT FROM ColumnCursor
                INTO @ColumnName;
            END;

            CLOSE ColumnCursor;
            DEALLOCATE ColumnCursor;

        END;


        /* =====================================================
           5. BUILD AUTHORIZATION CONDITION
           ===================================================== */

        DECLARE @AccessCondition NVARCHAR(MAX);

        SET @AccessCondition =
        N'
        (
               @Role = ''ADMIN''

            OR (
                @Role = ''BROKER''
                AND TB.AccountCode = @AccountCode
            )

            OR (
                @Role = ''DEALER''
                AND TB.UserID = @UserID
            )

            OR (
                @Role = ''GROUP''
                AND EXISTS
                (
                    SELECT 1
                    FROM dbo.Config_DealerMap DM
                    WHERE DM.GroupCode = @GroupCode
                      AND DM.DealerCode = TB.UserID
                      AND DM.AccountCode = TB.AccountCode
                )
            )
        )
        ';


        /* =====================================================
           6. SORTING
           ===================================================== */

        DECLARE @OrderBy NVARCHAR(200);

        SET @OrderBy = N'TB.id DESC';

        IF @OrderByClause IS NOT NULL
        BEGIN

            IF @OrderByClause = 'id'
                SET @OrderBy = N'TB.id ASC';

            ELSE IF @OrderByClause = 'id_desc'
                SET @OrderBy = N'TB.id DESC';

            ELSE IF @OrderByClause = 'trade_num'
                SET @OrderBy = N'TB.TradeNum ASC';

            ELSE IF @OrderByClause = 'trade_num_desc'
                SET @OrderBy = N'TB.TradeNum DESC';

            ELSE IF @OrderByClause = 'price'
                SET @OrderBy = N'TB.TradePrice ASC';

            ELSE IF @OrderByClause = 'price_desc'
                SET @OrderBy = N'TB.TradePrice DESC';

            ELSE
                RETURN 1007;

        END;


        /* =====================================================
           7. CURSOR PAGINATION
           ===================================================== */

        DECLARE @CursorCondition NVARCHAR(MAX) = N'';

        IF @HasCursor = 1
        BEGIN

            IF @CursorID IS NULL
                RETURN 1008;

            IF @Direction = 'NEXT'
            BEGIN

                IF @OrderBy = N'TB.id DESC'
                    SET @CursorCondition =
                        N' AND TB.id < @CursorID ';

                ELSE
                    SET @CursorCondition =
                        N' AND TB.id > @CursorID ';

            END;

            IF @Direction = 'PREVIOUS'
            BEGIN

                IF @OrderBy = N'TB.id DESC'
                    SET @CursorCondition =
                        N' AND TB.id > @CursorID ';

                ELSE
                    SET @CursorCondition =
                        N' AND TB.id < @CursorID ';

            END;

        END;


        /* =====================================================
           8. BUILD FINAL QUERY
           ===================================================== */

        DECLARE @SQL NVARCHAR(MAX);

        SET @SQL =
        N'
        SELECT
            ' + @Columns + N',

            COUNT_BIG(*) OVER() AS TotalRecords

        FROM dbo.tbTradeBook TB

        WHERE
            ' + @AccessCondition + N'

            ' + @CursorCondition + N'

        ORDER BY
            ' + @OrderBy + N'

        OFFSET 0 ROWS
        FETCH NEXT @Limit ROWS ONLY;
        ';


        /* =====================================================
           9. EXECUTE
           ===================================================== */

        EXEC sp_executesql
            @SQL,

            N'
                @Role VARCHAR(20),
                @UserID VARCHAR(30),
                @AccountCode VARCHAR(30),
                @GroupCode VARCHAR(10),
                @CursorID BIGINT,
                @Limit INT
            ',

            @Role = @Role,
            @UserID = @UserID,
            @AccountCode = @AccountCode,
            @GroupCode = @GroupCode,
            @CursorID = @CursorID,
            @Limit = @Limit;


        RETURN @ReturnCode;

    END TRY

    BEGIN CATCH

        DECLARE @ErrorMessage NVARCHAR(4000);
        DECLARE @ErrorNumber INT;

        SELECT
            @ErrorMessage = ERROR_MESSAGE(),
            @ErrorNumber = ERROR_NUMBER();

        THROW;

    END CATCH
END;
GO

EXEC dbo.usp_GetTradeBook
    @Role = 'ADMIN'

EXEC dbo.usp_GetTradeBook
    @Role = 'GROUP',
    @GroupCode = 'HO';

EXEC dbo.usp_GetTradeBook
    @Role = 'ADMIN',
    @Limit = 10;