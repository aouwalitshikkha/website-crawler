# === CONFIG ===
SEED_URL = "https://www.designmonks.co/"
PAGE_LIMIT = 0            # 0 = unlimited crawl
OUTPUT_FILE = "results.xlsx"
MIN_DELAY = 1.0           # seconds
MAX_DELAY = 3.0           # seconds
SAVE_INTERVAL = 10        # save progress every N pages
USE_ASYNC = True          # batch-check external links via async

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
)
crawler.crawl()
