# Website Crawler

A multi-threaded Python website crawler that maps internal link structures, detects broken pages, and exports results to Excel. Supports async HTTP fetching with automatic fallback to synchronous requests and headless browser rendering.

## Features

- **BFS crawl** — Same-domain breadth-first traversal with configurable batch size
- **Async-first** — Uses `aiohttp` by default, falls back to `requests`, then Playwright headless Chromium
- **3 Excel sheets** — Link Graph, Broken Links (error pages & external), Error References (broken URL → source mapping)
- **Page size tracking** — Captures HTML byte size for every crawled page
- **Social link filtering** — Excludes Facebook, Twitter/X, LinkedIn, Instagram, etc. from reports
- **External link validation** — Checks outbound link status via HEAD (fallback GET) with caching
- **Incremental saving** — Writes progress to xlsx every N pages (configurable)
- **Politeness delays** — Random delay between batches (1–3s configurable)

## Installation

```bash
git clone <repo-url>
cd crawlingsite
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python main.py
```

Enter a domain name when prompted (e.g. `example.com`). The crawler will:
1. Start BFS from `https://www.{domain}/`
2. Crawl same-domain pages in parallel batches
3. Check external outbound link status
4. Save results to `{domain}.xlsx`

### Configuration (edit `main.py`)

| Variable | Default | Description |
|---|---|---|
| `PAGE_LIMIT` | `0` | Max pages to crawl (`0` = unlimited) |
| `MIN_DELAY` | `1.0` | Min politeness delay (seconds) |
| `MAX_DELAY` | `3.0` | Max politeness delay (seconds) |
| `SAVE_INTERVAL` | `10` | Save Excel every N pages |
| `USE_ASYNC` | `True` | Use async aiohttp (falls back to sync) |
| `BATCH_SIZE` | `5` | Pages per concurrent batch |

## Output

The crawler produces a single Excel file named after the crawled domain, e.g. `example.com.xlsx`.

### Sheet 1: Link Graph

Every discovered page with its connections.

| Column | Description |
|---|---|
| URL | Page address |
| Status Code | HTTP response status |
| Page Size | HTML size (B / KB / MB) |
| All Inbound Links | Pages linking to this URL |
| All External Outbound Links | External links found on this page (social filtered) |

### Sheet 2: Broken Links

Pages involved in broken connections.

| Column | Description |
|---|---|
| URL | Page address |
| Status Code | HTTP response status |
| Page Size | HTML size (B / KB / MB) |
| Broken Inbound Links | Inbound links to this error page (shown when page is 4xx/5xx) |
| Broken External Outbound Links | Non-200 external links (social filtered) |

### Sheet 3: Error References

Flat mapping of every broken URL to the pages referencing it.

| Column | Description |
|---|---|
| Error Page | The non-200 URL (internal or external, social excluded) |
| Reference Page | The page that contains a link to the error URL |

## Project structure

```
crawlingsite/
├── main.py                 # Entry point and config
├── crawler/
│   ├── crawler.py          # BFS orchestration
│   ├── fetcher.py          # HTTP fetch with fallback chain
│   ├── parser.py           # HTML link extraction
│   ├── exporter.py         # Excel export (3 sheets)
│   └── models.py           # Data classes
├── requirements.txt
├── AGENTS.md               # AI agent instructions
└── README.md
```

## Requirements

- Python 3.10+
- `requests`, `aiohttp`, `beautifulsoup4`, `lxml`, `openpyxl`, `playwright` (see `requirements.txt`)

## License

MIT
