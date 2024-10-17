from datetime import datetime

import aiohttp


def create_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Create a filename using the timestamp
    return f"fs-404-{timestamp}.log"


def create_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


async def fetch_url(url: str) -> int:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            await response.text()
            return response.status
