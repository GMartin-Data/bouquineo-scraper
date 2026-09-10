# Bouquineo — Competitor Price & Stock Scraper

Scrapes the public catalogue of a competitor bookstore
([books.toscrape.com](https://books.toscrape.com), a legal training sandbox —
1,000 books, 50 categories, static HTML) into PostgreSQL, to answer:

> Which titles are out of stock or low on stock, and which are the best rated?

## Technologies

- **Python 3.14** managed with [uv](https://docs.astral.sh/uv/)
- **Scrapy 2.18** — two spiders: `listing` (list pages) and `books` (product pages)
- **PostgreSQL 17** (Docker) + **psycopg3** for the load step
- Output as JSONL (append-as-you-go), which doubles as the crash-resume state

## Installation

```bash
uv sync                  # Python env + dependencies (uv reads .python-version)
cp env.example .env      # local defaults work as-is
docker compose up -d     # PostgreSQL 17 (only needed for the load step)
```

## Usage

```bash
uv run scrapy crawl listing            # D1: 50 list pages  -> data/listing.jsonl
uv run scrapy crawl books              # D2: product pages  -> data/books.jsonl
uv run scrapy crawl books -a limit=20  # sample mode: only 20 NEW pages this run
uv run python db/load.py               # load JSONL -> PostgreSQL (idempotent)
uv run pytest && uv run scrapy check   # unit tests + live spider contracts
```

Interrupt `scrapy crawl books` anytime (Ctrl-C, kill, crash): the next run
re-reads `data/books.jsonl`, skips what was already collected, and continues.
`db/load.py` can be re-run at will — upsert on UPC, no duplicates ever.

## Design decisions

- **The output file IS the resume state.** Items are flushed to JSONL line by
  line as they are scraped; on startup the `books` spider re-reads its own
  output and skips known URLs. No checkpoint file, no DB dependency during
  crawling — whatever reached disk is exactly what was collected.
- **Decoupled loading (landing-zone pattern).** Spiders never touch the DB;
  `db/load.py` never touches the network. Fields are collected raw (even the
  ones the data proves dead — see `notes_obs.md`); conclusions about their
  usability belong to the observation note, not to the collector.
- **Two keys, two moments.** During the crawl, identity is the URL (the only
  identity known before the request). In the DB, identity is the UPC
  (`PRIMARY KEY`, upsert target) — titles are provably not unique.

### Politeness (self-imposed: robots.txt returns 404)

- `DOWNLOAD_DELAY = 0.5` with one request at a time: the full 1,000-page
  crawl takes ~10 minutes — fast enough for a working day, and a negligible
  load for the server (Scrapy also randomizes the delay to avoid a robotic
  request pattern).
- Nominative `USER_AGENT` with a contact email: the site can identify who
  crawls and why, and reach out.
- **Failure guard**: each failed request is logged and skipped (one dead page
  must not kill the crawl); past 10 failures (~1% of the catalogue) the
  spider stops itself — the site has likely changed, and every further
  request would be wasted load. `CLOSESPIDER_ERRORCOUNT` stays as a safety
  net against genuine code bugs.

## Deliverables (French)

- `journal.md` — daily log: decisions, milestones, incidents and their fixes.
- `notes_obs.md` — data observation note: dead fields, stock and rating
  profiles, the duplicate-title case, sandbox artifacts.

## Author

Grégory Martin
