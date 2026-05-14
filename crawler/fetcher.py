import asyncio
import requests
from .models import FetchResult


class WebFetcher:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        self._playwright = None
        self._browser = None

    def _get_playwright(self):
        if self._playwright is None:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
        return self._playwright

    def _get_browser(self, headless=True):
        pw = self._get_playwright()
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        self._browser = pw.chromium.launch(headless=headless)
        return self._browser

    def _fetch_with_playwright(self, url, headless=True):
        browser = self._get_browser(headless=headless)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            return FetchResult(status_code=200, html=html)
        finally:
            page.close()

    def fetch(self, url: str) -> FetchResult:
        try:
            resp = self._session.get(url, timeout=15)
            return FetchResult(status_code=resp.status_code, html=resp.text)
        except Exception:
            pass

        try:
            return self._fetch_with_playwright(url, headless=True)
        except Exception:
            pass

        try:
            return self._fetch_with_playwright(url, headless=False)
        except Exception as e:
            return FetchResult(status_code=0, html="", error=str(e))

    def fetch_status(self, url: str) -> int:
        try:
            resp = self._session.head(url, timeout=10, allow_redirects=True)
            return resp.status_code
        except Exception:
            try:
                resp = self._session.get(url, timeout=10, stream=True)
                return resp.status_code
            except Exception:
                return 0

    def fetch_statuses_batch(self, urls: list[str]) -> dict[str, int]:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._fetch_statuses_async(urls)
                )
            finally:
                loop.close()
        except Exception:
            return self._fetch_statuses_sequential(urls)

    async def _fetch_statuses_async(self,
                                    urls: list[str]) -> dict[str, int]:
        import aiohttp
        headers = dict(self._session.headers)
        connector = aiohttp.TCPConnector(limit=15)
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(
            headers=headers, connector=connector
        ) as session:

            async def check(url):
                try:
                    async with session.head(
                        url, timeout=timeout, allow_redirects=True
                    ) as resp:
                        return url, resp.status
                except Exception:
                    try:
                        async with session.get(
                            url, timeout=timeout
                        ) as resp:
                            return url, resp.status
                    except Exception:
                        return url, 0

            tasks = [check(url) for url in urls]
            results = await asyncio.gather(*tasks)
            return dict(results)

    def _fetch_statuses_sequential(self,
                                   urls: list[str]) -> dict[str, int]:
        result = {}
        for url in urls:
            result[url] = self.fetch_status(url)
        return result

    def close(self):
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
