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
        # Stage 1: requests
        try:
            resp = self._session.get(url, timeout=15)
            return FetchResult(status_code=resp.status_code, html=resp.text)
        except Exception:
            pass

        # Stage 2: Playwright headless
        try:
            return self._fetch_with_playwright(url, headless=True)
        except Exception:
            pass

        # Stage 3: Playwright headed
        try:
            return self._fetch_with_playwright(url, headless=False)
        except Exception as e:
            return FetchResult(status_code=0, html="", error=str(e))

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
