from typing import Any

from src.features.Tradebook.Application.DTO.Inputs.Userdata import UserData
from src.features.Tradebook.Application.DTO.Outputs.TradeBookdto import TradeBookDto
from src.features.Tradebook.Application.ports.GetTradesRepository import (
    IGetTradesRepository,
)
from src.shared.database.sp_executor import StoredProcedureExecutor


class GetTradeRepository(IGetTradesRepository):

    def __init__(self,sp_executor:StoredProcedureExecutor):
        self.sp_executor=sp_executor

    async def execute_get_trade(self,user_data:UserData)->list[TradeBookDto]:

        params:dict[str,Any]={"AccountCode":user_data.accountcode,
                              "CursorID":user_data.cursorid,
                              "GroupCode":user_data.groupcode,
                              "Limit":user_data.limit,
                              "Role":user_data.role,
                              "UserId":user_data.userid}
        
        raw_trades=await self.sp_executor.execute("usp_GetTradeBook",params)
        return [
            TradeBookDto(
                trade_id=row["MainTradeID"],
                member_code=str(row["MemberCode"]),
                symbol=row["ScripCode"],
                quantity=row["TradeQty"],
                price=row["TradePrice"],
                trade_time=row["DateTime"],
            )
            for row in raw_trades
        ]