# === CONFIG ===
SEED_URL = "https://example.com"
PAGE_LIMIT = 0            # 0 = unlimited crawl
OUTPUT_FILE = "results.xlsx"
MIN_DELAY = 1.0           # seconds
MAX_DELAY = 3.0           # seconds

# === RUN ===
from crawler.crawler import Crawler
from crawler.exporter import ExcelExporter

crawler = Crawler(
    seed_url=SEED_URL,
    limit=PAGE_LIMIT,
    min_delay=MIN_DELAY,
    max_delay=MAX_DELAY,
)
results = crawler.crawl()
ExcelExporter.export(results, OUTPUT_FILE)
