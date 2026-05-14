import time
import random
from collections import deque

from .fetcher import WebFetcher
from .parser import LinkParser
from .models import PageData


class Crawler:
    def __init__(self, seed_url: str, limit: int = 0,
                 min_delay: float = 1, max_delay: float = 3):
        if not seed_url.startswith(("http://", "https://")):
            seed_url = "https://" + seed_url
        self.seed_url = seed_url.rstrip("/")
        self.limit = limit
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.domain = LinkParser.get_domain(self.seed_url)
        self.fetcher = WebFetcher()

    def crawl(self) -> dict[str, PageData]:
        pages: dict[str, PageData] = {}
        visited: set[str] = set()
        queue: deque[str] = deque()
        pending: set[str] = set()

        queue.append(self.seed_url)
        pending.add(self.seed_url)
        start_time = time.time()

        while queue:
            if self.limit > 0 and len(visited) >= self.limit:
                break

            url = queue.popleft()
            pending.discard(url)

            if url in visited:
                continue
            visited.add(url)

            print(f"[{len(visited)}] Fetching: {url}")
            result = self.fetcher.fetch(url)

            if url in pages:
                page = pages[url]
                page.status_code = result.status_code
            else:
                page = PageData(url=url, status_code=result.status_code)
                pages[url] = page

            if result.html and result.status_code == 200:
                links = LinkParser.extract_links(
                    result.html, url, self.domain
                )
                for link in links:
                    page.outbound.add(link)

                    if link not in pages:
                        pages[link] = PageData(
                            url=link, status_code=0
                        )
                    pages[link].inbound.add(url)

                    if link not in visited and link not in pending:
                        queue.append(link)
                        pending.add(link)

            elapsed = time.time() - start_time
            print(
                f"  Status: {result.status_code} | "
                f"Outbound: {len(page.outbound)} | "
                f"Queue: {len(queue)} | "
                f"Elapsed: {elapsed:.1f}s"
            )

            if queue:
                delay = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)

        self.fetcher.close()

        total_time = time.time() - start_time
        success = sum(
            1 for p in pages.values() if p.status_code == 200
        )
        errors = sum(
            1 for p in pages.values()
            if p.status_code and p.status_code >= 400
        )
        uncrawled = sum(
            1 for p in pages.values() if p.status_code == 0
        )
        print(
            f"\n=== Crawl Complete ==="
            f"\n  Pages crawled: {len(visited)}"
            f"\n  Total URLs tracked: {len(pages)}"
            f"\n  Successful (200): {success}"
            f"\n  Errors (4xx/5xx): {errors}"
            f"\n  Uncrawled (discovered only): {uncrawled}"
            f"\n  Time: {total_time:.1f}s"
        )
        return pages
