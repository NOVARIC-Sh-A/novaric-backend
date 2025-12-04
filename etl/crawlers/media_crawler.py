# etl/crawlers/media_crawler.py
import asyncio
from typing import List, Dict, Any
from playwright.async_api import async_playwright


class MediaCrawler:
    """
    Simple Playwright-based crawler to collect news snippets
    from Albanian media portals. You can extend/replace URLs
    as needed.
    """

    def __init__(self, urls: List[str] | None = None):
        self.urls = urls or [
            "https://top-channel.tv/lajmet/",
            "https://www.balkanweb.com/category/lajme/",
            "https://abcnews.al/kategoria/aktualitet/",
        ]

    async def _fetch_page(self, page, url: str) -> List[Dict[str, Any]]:
        print(f"[MediaCrawler] Visiting {url}")

        try:
            await page.goto(url, timeout=20000, wait_until="networkidle")
        except Exception as e:
            print(f"⚠ Failed to load {url}: {e}")
            return []

        # Try to wait for typical article containers
        try:
            await page.wait_for_selector("article, div.post, .post, .article", timeout=10000)
        except Exception:
            print(f"⚠ No recognizable article selector at: {url}")
            return []

        items = await page.locator("article, div.post, .post, .article").all()
        results: List[Dict[str, Any]] = []

        for item in items:
            try:
                # Try to extract a title
                title_el = item.locator("h1, h2, h3, a").first
                title = (await title_el.inner_text()).strip()
            except Exception:
                title = ""

            try:
                text = (await item.inner_text()).replace("\n", " ").strip()
            except Exception:
                text = ""

            if not text and not title:
                continue

            snippet = text or title
            snippet = snippet[:400]

            results.append(
                {
                    "source_url": url,
                    "title": title,
                    "snippet": snippet,
                }
            )

        print(f"[MediaCrawler] Extracted {len(results)} items from {url}")
        return results

    async def run(self) -> List[Dict[str, Any]]:
        """
        Crawl all configured URLs and return a list of
        { source_url, title, snippet } dicts.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            all_results: List[Dict[str, Any]] = []

            for url in self.urls:
                page_results = await self._fetch_page(page, url)
                all_results.extend(page_results)

            await browser.close()

        print(f"[MediaCrawler] Total items: {len(all_results)}")
        return all_results


if __name__ == "__main__":
    async def _test():
        crawler = MediaCrawler()
        data = await crawler.run()
        print(f"Sample: {data[:2]}")

    asyncio.run(_test())
