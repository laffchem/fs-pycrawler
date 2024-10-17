import asyncio
import logging
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from utils import create_filename, create_timestamp, fetch_url
from pages import seed_pages
import os

# Set up logging configuration to log to both console and a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("logs", create_filename())),  # Log to file
        logging.StreamHandler(),  # Log to console
    ],
)

visited_urls: set[str] = set()  # To ignore duplicate URLs


async def main() -> None:
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=20, headless=False, browser_type="chromium"
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        url = context.request.url
        status_code = context.response.status
        context.log.info(f"Processing {url} with status {status_code}...")

        # Only process the page if it has not been visited yet
        if url not in visited_urls:
            if "/category/" or "/product" in url:
                fetched_status = await fetch_url(url)
                visited_urls.add(url)
                await context.enqueue_links()
                data = {
                    "url": url,
                    "status": fetched_status,
                }

            # Check if the status code is between 400 and 600 for logging and dataset
            if fetched_status >= 400 and fetched_status < 600:
                logging.info(
                    f"{create_timestamp()} - {url: str} - Status Code: {fetched_status: int}"
                )
                await context.push_data(data)

        # Handle pagination if there is a "Next" button or pagination element
        has_next_page = await context.page.evaluate(
            "() => document.querySelector('div.arrow.right') !== null"
        )

        if has_next_page:
            context.log.info(f"Clicking pagination arrow on {url}")
            await context.page.click("div.arrow.right")
            await context.page.wait_for_selector("div.arrow.right", state="attached")
            await request_handler(context)

    await crawler.run(seed_pages)
    await crawler.export_data("results.json")

    stats = crawler.request_queue.stats()  # type: ignore
    logging.info(f"Final request statistics: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
