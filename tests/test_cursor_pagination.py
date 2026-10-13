import asyncio
import base64
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

from pydantic import ValidationError

from src.features.Tradebook.Application.DTO.Inputs.BiDirectionalPaginationDTO import (
    BiDirectionalPaginationDTO,
)
from src.features.Tradebook.Application.DTO.Inputs.TradeBookDTO import TradeBookDTO
from src.features.Tradebook.Application.DTO.Inputs.UserdataDTO import UserDataDTO
from src.features.Tradebook.Domain.entities.Paginationdata import PaginationData
from src.features.Tradebook.Domain.value_objects.cursor import (
    decode_cursor,
    encode_cursor,
)
from src.features.Tradebook.Infrastructure.repositories.get_trade import (
    GetTradeRepository,
)
from src.features.Tradebook.Presentation.schemas.UserRequest import UserRequest
from src.shared.database.sp_executor import StoredProcedureExecutor


class TestCursorValueObject(unittest.TestCase):
    def test_encode_positive_int(self):
        encoded = encode_cursor(500)
        self.assertEqual(encoded, "NTAw")

    def test_encode_numeric_string(self):
        encoded = encode_cursor("500")
        self.assertEqual(encoded, "NTAw")

    def test_encode_already_encoded_cursor(self):
        already_encoded = "NTAw"
        self.assertEqual(encode_cursor(already_encoded), "NTAw")

    def test_encode_empty_or_none_or_zero(self):
        self.assertIsNone(encode_cursor(None))
        self.assertIsNone(encode_cursor(""))
        self.assertIsNone(encode_cursor("   "))
        self.assertIsNone(encode_cursor(0))
        self.assertIsNone(encode_cursor("0"))
        self.assertIsNone(encode_cursor(-10))

    def test_decode_valid_base64(self):
        self.assertEqual(decode_cursor("NTAw"), 500)
        self.assertEqual(decode_cursor("NDkx"), 491)

    def test_decode_direct_int(self):
        self.assertEqual(decode_cursor(500), 500)

    def test_decode_empty_or_none(self):
        self.assertIsNone(decode_cursor(None))
        self.assertIsNone(decode_cursor(""))
        self.assertIsNone(decode_cursor("   "))

    def test_decode_invalid_base64_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            decode_cursor("500")  # Invalid padding / non-base64
        self.assertIn("Invalid Base64 cursor", str(ctx.exception))

    def test_decode_non_numeric_base64_raises_error(self):
        non_numeric_b64 = base64.b64encode(b"not_a_number").decode()
        with self.assertRaises(ValueError) as ctx:
            decode_cursor(non_numeric_b64)
        self.assertIn("numeric ID", str(ctx.exception))

    def test_decode_non_positive_numeric_raises_error(self):
        zero_b64 = base64.b64encode(b"0").decode()
        with self.assertRaises(ValueError) as ctx:
            decode_cursor(zero_b64)
        self.assertIn("positive", str(ctx.exception))

    def test_round_trip(self):
        trade_id = 987654321
        encoded = encode_cursor(trade_id)
        decoded = decode_cursor(encoded)
        self.assertEqual(decoded, trade_id)


class TestUserRequestSchemaValidation(unittest.TestCase):
    def test_valid_cursor_start_decoded(self):
        b64_val = encode_cursor(1234)
        req = UserRequest(cursor_start=b64_val)
        self.assertEqual(req.cursor_start, 1234)

    def test_valid_cursor_end_decoded(self):
        b64_val = encode_cursor(5678)
        req = UserRequest(cursor_end=b64_val)
        self.assertEqual(req.cursor_end, 5678)

    def test_direct_int_cursor_accepted(self):
        req = UserRequest(cursor_start=1234)
        self.assertEqual(req.cursor_start, 1234)

    def test_empty_string_cursor_becomes_none(self):
        req = UserRequest(cursor_start="")
        self.assertIsNone(req.cursor_start)

    def test_both_cursors_provided_raises_error(self):
        b64_1 = encode_cursor(100)
        b64_2 = encode_cursor(200)
        with self.assertRaises(ValidationError) as ctx:
            UserRequest(cursor_start=b64_1, cursor_end=b64_2)
        self.assertIn("Provide only one cursor per request", str(ctx.exception))

    def test_unencoded_string_cursor_rejected(self):
        with self.assertRaises(ValidationError):
            UserRequest(cursor_start="123")


class TestPaginationDataEntity(unittest.TestCase):
    def test_pagination_data_holds_raw_values_without_post_init(self):
        p = PaginationData(cursor_start=500, cursor_end=491, has_prev=True, has_next=False)
        self.assertEqual(p.cursor_start, 500)
        self.assertEqual(p.cursor_end, 491)
        self.assertTrue(p.has_prev)
        self.assertFalse(p.has_next)

    def test_pagination_data_handles_empty_or_none(self):
        p = PaginationData(cursor_start=None, cursor_end=None)
        self.assertIsNone(p.cursor_start)
        self.assertIsNone(p.cursor_end)


class TestBiDirectionalPaginationDTO(unittest.TestCase):
    def test_dto_decodes_base64_cursor(self):
        dto = BiDirectionalPaginationDTO(cursor_start="NTAw", cursor_end=None, limit=10)
        self.assertEqual(dto.cursor_start, 500)
        self.assertIsNone(dto.cursor_end)

    def test_dto_accepts_raw_int_cursor(self):
        dto = BiDirectionalPaginationDTO(cursor_start=None, cursor_end=491, limit=10)
        self.assertEqual(dto.cursor_end, 491)

    def test_dto_handles_empty_cursor(self):
        dto = BiDirectionalPaginationDTO(cursor_start="", cursor_end=None, limit=10)
        self.assertIsNone(dto.cursor_start)


class TestGetTradeRepositoryPaginationFlow(unittest.TestCase):
    def setUp(self):
        self.mock_sp_executor = AsyncMock(spec=StoredProcedureExecutor)
        self.repository = GetTradeRepository(self.mock_sp_executor)

    def test_repository_encodes_sql_cursors_into_output_dto(self):
        # Result set 1: trades, Result set 2: pagination metadata
        self.mock_sp_executor.execute_result_sets.return_value = [
            [
                {
                    "MainTradeID": 500,
                    "MemberCode": "MEM01",
                    "ScripCode": "RELIANCE",
                    "TradeQty": 50,
                    "TradePrice": Decimal("2450.50"),
                    "DateTime": datetime.now(UTC),
                }
            ],
            [
                {
                    "StartCursor": 500,
                    "EndCursor": 491,
                    "HasPrev": True,
                    "HasNext": True,
                }
            ],
        ]

        query_dto = TradeBookDTO(
            user=UserDataDTO(role="ADMIN"),
            pagination=BiDirectionalPaginationDTO(limit=10),
        )

        res = asyncio.run(self.repository.execute_get_trade(query_dto))

        # Check that outbound cursors are Base64 encoded
        self.assertEqual(res.pagination.cursor_start, "NTAw")
        self.assertEqual(res.pagination.cursor_end, "NDkx")
        self.assertTrue(res.pagination.has_prev)
        self.assertTrue(res.pagination.has_next)

    def test_end_to_end_cursor_loop(self):
        """Simulate Client -> API -> SQL -> Response -> Client Next Page -> API -> SQL."""
        # 1. API responds with page 1 containing Base64 encoded cursors
        self.mock_sp_executor.execute_result_sets.return_value = [
            [
                {
                    "MainTradeID": 500,
                    "MemberCode": "MEM01",
                    "ScripCode": "TCS",
                    "TradeQty": 100,
                    "TradePrice": Decimal("3500.00"),
                    "DateTime": datetime.now(UTC),
                }
            ],
            [
                {
                    "StartCursor": 500,
                    "EndCursor": 491,
                    "HasPrev": False,
                    "HasNext": True,
                }
            ],
        ]
        page_1 = asyncio.run(
            self.repository.execute_get_trade(
                TradeBookDTO(
                    user=UserDataDTO(role="ADMIN"),
                    pagination=BiDirectionalPaginationDTO(limit=10),
                )
            )
        )

        # 2. Client receives Base64 cursor_end ("NDkx") and requests the next page
        next_page_cursor = page_1.pagination.cursor_end
        self.assertEqual(next_page_cursor, "NDkx")

        # 3. Client sends {cursor_end: "NDkx"} in next request
        next_request = UserRequest(cursor_end=next_page_cursor, limit=10)

        # 4. UserRequest schema decodes "NDkx" into integer 491
        self.assertEqual(next_request.cursor_end, 491)

        # 5. Application constructs TradeBookDTO with integer 491
        next_dto = TradeBookDTO(
            user=UserDataDTO(role="ADMIN"),
            pagination=BiDirectionalPaginationDTO(
                cursor_end=next_request.cursor_end,
                limit=next_request.limit,
            ),
        )

        # 6. Repository executes SP with integer EndCursor: 491
        self.mock_sp_executor.execute_result_sets.return_value = [[], []]
        asyncio.run(self.repository.execute_get_trade(next_dto))

        call_args = self.mock_sp_executor.execute_result_sets.call_args[0]
        sp_name = call_args[0]
        sp_params = call_args[1]

        self.assertEqual(sp_name, "usp_GetTradeBook")
        self.assertEqual(sp_params["EndCursor"], 491)
        self.assertIsNone(sp_params["StartCursor"])


if __name__ == "__main__":
    unittest.main()
