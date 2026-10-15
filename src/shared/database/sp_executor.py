
from typing import Any
import time

from src.shared.database.connection import Database

Row = dict[str, Any] # for a single row
ResultSet = list[Row] # for all the rows in a set

# Directly referenced by the Infrastructure level repositories,can acquire cursor and execute the db operations
class StoredProcedureExecutor:
    def __init__(self, database: Database):
        self.database = database

# 1. Method used to call a stored procedure for multiple result sets    
    async def execute_result_sets(
        self,
        procedure_name: str,
        params: dict[str, Any] | None = None,
    ) -> list[ResultSet]:
        """
        Execute a stored procedure and fetch every result set.
        Returns:
            [
                [row1, row2, ...],  # Result set 1
                [row1, ...],        # Result set 2
            ]
        """
        async with self.database.acquire_cursor() as cursor:
            if params:                                  # Parameter construction for the SQL query
                parameter_names = ", ".join(
                    f"@{name} = ?" for name in params
                )
                sql = f"EXEC {procedure_name} {parameter_names}"
                values = list(params.values())
            else:
                sql = f"EXEC {procedure_name}"
                values = []
            execute_start = time.perf_counter() # Start counter to measure just the SP execution time
            await cursor.execute(sql, values)
            execute_elapsed = time.perf_counter() - execute_start

            result_sets: list[ResultSet] = []
            fetch_start = time.perf_counter()

            while True:
                # Some statements may not produce a row set.
                if cursor.description is not None:
                    columns = [
                        column[0] for column in cursor.description
                    ]
                    rows = await cursor.fetchall()

                    result_sets.append([
                        dict(zip(columns, row))
                        for row in rows
                    ])
                # Advance to the next result set.
                has_next = await cursor.nextset()

                if not has_next:
                    break
            fetch_elapsed = time.perf_counter() - fetch_start # End counter to measure just the SP execution time
            print(
                f"Execute time: {execute_elapsed * 1000:.2f} ms"
            )
            print(
                f"Fetch and result-set processing time: "
                f"{fetch_elapsed * 1000:.2f} ms"
            )

            return result_sets

# 1. Method used to call a stored procedure for a single result sets
    # async def execute(
    #     self,
    #     procedure_name: str,
    #     params: dict[str, Any] | None = None,
    # ) -> ResultSet:
    #     """
    #     Backward-compatible method: return the first row set.
    #     """
    #     result_sets = await self.execute_result_sets(
    #         procedure_name,
    #         params,
    #     )
    #     return result_sets[0] if result_sets else []
