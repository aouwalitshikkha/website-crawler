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
                 use_async: bool = True,
                 batch_size: int = 5):
        if not seed_url.startswith(("http://", "https://")):
            seed_url = "https://" + seed_url
        self.seed_url = seed_url.rstrip("/")
        self.limit = limit
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.export_path = export_path
        self.save_interval = save_interval
        self.use_async = use_async
        self.batch_size = batch_size
        self.domain = LinkParser.get_domain(self.seed_url)
        self.fetcher = WebFetcher()
        self._external_cache: dict[str, int] = {}

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

            batch: list[str] = []
            while queue and len(batch) < self.batch_size:
                url = queue.popleft()
                pending.discard(url)
                if url not in visited:
                    batch.append(url)
            if not batch:
                continue

            batch_set = set(batch)
            print(
                f"[{len(visited)+1}-{len(visited)+len(batch)}] "
                f"Batch of {len(batch)}..."
            )

            if self.use_async:
                results = self.fetcher.fetch_batch(batch)
            else:
                results = {}
                for url in batch:
                    results[url] = self.fetcher.fetch(url)

            for url in batch:
                visited.add(url)
                result = results[url]

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
                            if link not in self._external_cache:
                                new_external.append(link)
                        else:
                            if link not in pages:
                                pages[link] = PageData(
                                    url=link, status_code=0
                                )
                            pages[link].inbound.add(url)
                            if (link not in visited
                                    and link not in pending
                                    and link not in batch_set):
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
                                statuses[link] = self.fetcher.fetch_status(
                                    link
                                )
                        self._external_cache.update(statuses)

                    for link in links:
                        if (LinkParser.is_external(link, self.domain)
                                and link in self._external_cache):
                            page.external_outbound[link] = \
                                self._external_cache[link]

                elapsed = time.time() - start_time
                print(
                    f"  {url[:70]:70s} "
                    f"St:{result.status_code} "
                    f"Ex:{len(page.external_outbound)} "
                    f"Q:{len(queue)} "
                    f"{elapsed:.0f}s"
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
            f"\n  External links checked: {len(self._external_cache)}"
            f"\n  Successful (200): {success}"
            f"\n  Errors (4xx/5xx): {errors}"
            f"\n  Uncrawled (discovered only): {uncrawled}"
            f"\n  Time: {total_time:.1f}s"
        )
        return pages
