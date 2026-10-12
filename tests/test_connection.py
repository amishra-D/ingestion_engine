import asyncio
import time

import httpx

URL = "http://127.0.0.1:8000/tradebook/get-tradebook"
PAYLOAD = {
    "role": "ADMIN",
    "userid": "USR001",
    "accountcode": "ACC001",
    "groupcode": "GRP001",
    "cursorid": 0,
    "limit": 10
}

async def send_request(client, req_id):
    start = time.perf_counter()
    response = await client.post(URL, json=PAYLOAD)
    duration = (time.perf_counter() - start) * 1000
    print(f"Request #{req_id}: Status {response.status_code} in {duration:.2f}ms")

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Fire 20 concurrent requests simultaneously
        tasks = [send_request(client, i) for i in range(1, 21)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())