import asyncio
import unittest

import httpx
from fastapi import status

from src.app import app
from src.shared.security.jwt import create_access_token


class TestIngestionAPI(unittest.TestCase):
    def setUp(self):
        self.admin_token = create_access_token(
            user_id=1, username="admin", role="ADMIN"
        )
        self.dealer_token = create_access_token(
            user_id=2, username="SUP", role="DEALER"
        )

    def test_dealer_forbidden_from_controlling_ingestion(self):
        async def run_test():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                res = await client.post(
                    "/ingestion/start",
                    json={"interval_seconds": 1.0},
                    headers={"Authorization": f"Bearer {self.dealer_token}"},
                )
                self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        asyncio.run(run_test())

    def test_status_endpoint_accessible(self):
        async def run_test():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                res = await client.get("/ingestion/status")
                self.assertEqual(res.status_code, status.HTTP_200_OK)
                body = res.json()
                self.assertIn("is_running", body)
                self.assertIn("total_inserted", body)
                self.assertIn("seed_dealers_count", body)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
