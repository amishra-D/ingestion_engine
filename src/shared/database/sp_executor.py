from typing import Any

from src.shared.database.connection import Database


class StoredProcedureExecutor:
    def __init__(self, database: Database):
        self.database = database

    async def execute(
        self,
        procedure_name: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        async with self.database.acquire_cursor() as cursor:
            if params:
                parameter_names = ", ".join(f"@{name} = ?" for name in params)
                sql = f"EXEC {procedure_name} {parameter_names}"
                values = list(params.values())
                await cursor.execute(sql, values)
            else:
                await cursor.execute(f"EXEC {procedure_name}")

            if cursor.description is None:
                return []

            rows = await cursor.fetchall()
            columns = [column[0] for column in cursor.description]

            return [dict(zip(columns, row)) for row in rows]