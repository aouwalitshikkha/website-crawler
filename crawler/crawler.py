import time
import random
from collections import deque

from .fetcher import WebFetcher
from .parser import LinkParser
from .models import PageData
from .exporter import ExcelExporter


class Crawler:
    def __init__(self, seed_url: str, limit: int = 0,
                 min_delay: float = 1, max_delay: float = 3,
                 export_path: str = "results.xlsx",
                 save_interval: int = 10,
                 use_async: bool = True):
        if not seed_url.startswith(("http://", "https://")):
            seed_url = "https://" + seed_url
        self.seed_url = seed_url.rstrip("/")
        self.limit = limit
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.export_path = export_path
        self.save_interval = save_interval
        self.use_async = use_async
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
        external_count = 0

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
                links = LinkParser.extract_links(result.html, url)
                new_external: list[str] = []
                for link in links:
                    if LinkParser.is_external(link, self.domain):
                        if link not in page.external_outbound:
                            new_external.append(link)
                    else:
                        if link not in pages:
                            pages[link] = PageData(url=link, status_code=0)
                        pages[link].inbound.add(url)
                        if link not in visited and link not in pending:
                            queue.append(link)
                            pending.add(link)

                if new_external:
                    if self.use_async:
                        statuses = self.fetcher.fetch_statuses_batch(
                            new_external
                        )
                    else:
                        statuses = {}
                        for link in new_external:
                            statuses[link] = self.fetcher.fetch_status(link)
                    page.external_outbound.update(statuses)
                    external_count += len(new_external)

            elapsed = time.time() - start_time
            print(
                f"  Status: {result.status_code} | "
                f"External: {len(page.external_outbound)} | "
                f"Queue: {len(queue)} | "
                f"Elapsed: {elapsed:.1f}s"
            )

            if len(visited) % self.save_interval == 0:
                ExcelExporter.export(pages, self.export_path)

            if queue:
                delay = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)

        self.fetcher.close()

        ExcelExporter.export(pages, self.export_path)

        total_time = time.time() - start_time
        success = sum(1 for p in pages.values() if p.status_code == 200)
        errors = sum(
            1 for p in pages.values()
            if p.status_code and p.status_code >= 400
        )
        uncrawled = sum(1 for p in pages.values() if p.status_code == 0)
        print(
            f"\n=== Crawl Complete ==="
            f"\n  Pages crawled: {len(visited)}"
            f"\n  Total URLs tracked (internal): {len(pages)}"
            f"\n  External links checked: {external_count}"
            f"\n  Successful (200): {success}"
            f"\n  Errors (4xx/5xx): {errors}"
            f"\n  Uncrawled (discovered only): {uncrawled}"
            f"\n  Time: {total_time:.1f}s"
        )
        return pages
