# === CONFIG ===
SEED_URL = "https://www.designmonks.co/"
PAGE_LIMIT = 0            # 0 = unlimited crawl
OUTPUT_FILE = "results.xlsx"
MIN_DELAY = 1.0           # seconds between batches
MAX_DELAY = 3.0
SAVE_INTERVAL = 10        # save progress every N pages
USE_ASYNC = True          # async-first for both crawling & external checks
BATCH_SIZE = 5            # pages to crawl concurrently per batch

# === RUN ===
from crawler.crawler import Crawler

crawler = Crawler(
    seed_url=SEED_URL,
    limit=PAGE_LIMIT,
    min_delay=MIN_DELAY,
    max_delay=MAX_DELAY,
    export_path=OUTPUT_FILE,
    save_interval=SAVE_INTERVAL,
    use_async=USE_ASYNC,
    batch_size=BATCH_SIZE,
)
crawler.crawl()
