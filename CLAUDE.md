# Bouquineo — Competitor Price & Stock Scraper

Training brief (2 days): scrape https://books.toscrape.com (1,000 books, static HTML,
legal sandbox) into PostgreSQL to answer: which titles are out of stock / low stock,
and which are the best rated. Full spec: `../brief_scraping/brief-scraping.md`.

## Stack (decided 2026-09-08)

- Python 3.14.7 (pinned via `.python-version`), managed with **uv** (brief requirement)
- **Scrapy 2.18** — two dedicated spiders, one per brief phase:
  - `listing` (D1): 50 list pages → `data/listing.jsonl` (title, price, rating, detail URL)
  - `books` (D2): 1,000 product pages → `data/books.jsonl` (UPC, prices, tax, real stock,
    reviews, description, category)
- **Resume strategy (option A)**: the output JSONL *is* the state. Items are appended
  line-by-line as collected; on startup the spider re-reads the file and skips URLs
  already seen. No DB dependency during crawling.
- **PostgreSQL** in Docker (`docker-compose.yml`, DB only — the scraper runs on host).
- **Loading**: separate scripts, decoupled from scraping (landing-zone pattern):
  `db/schema.sql` (creation) + `db/load.py` (psycopg3, plain SQL, upsert
  `ON CONFLICT (upc)` — idempotent, re-runs create no duplicates).
- Politeness: `DOWNLOAD_DELAY = 0.5`, explicit nominative `USER_AGENT`,
  `CLOSESPIDER_ERRORCOUNT` guard. Rationale documented in README.
- Sample mode: spider argument (`-a limit=N`) — required for the live demo.
- `jq` for JSONL inspection during dev/demo (never a code dependency).

## Layout

Canonical Scrapy layout (flat, `scrapy.cfg` at root) — this is an application, not an
installable library, so a `src/` layout would fight the framework for no benefit.
Non-Scrapy assets live in `db/` (SQL + loader) and `data/` (JSONL outputs).

## Conventions

- **Direct commits on `main`** — declared exemption from the branch→PR workflow:
  individual 2-day training project; evaluation looks at commit regularity, not
  branch discipline. Conventional Commits still apply.
- Code, comments, docstrings, commits: English. `journal.md` and `notes_obs.md`
  (French-facing deliverables): French.
- **Pedagogical mode**: Claude writes the code; every notion used is synthesized in
  `../brief_scraping/notes/` (one file per topic, French). Greg must be able to
  explain all code during the demo — notes are written for that purpose.
- `journal.md` doubles as the progress checkpoint (brief deliverable + session
  discipline in one artifact).

## Commands

```bash
uv sync                                      # install env
docker compose up -d                         # start Postgres
uv run scrapy crawl listing                  # D1: list pages → data/listing.jsonl
uv run scrapy crawl books                    # D2: product pages → data/books.jsonl
uv run scrapy crawl books -a limit=20        # sample mode (demo)
uv run python db/load.py                     # load JSONL → PostgreSQL (idempotent)
```

## Do NOT

- No DB access from spiders (resume must work without Postgres up).
- No extra features beyond the brief (robust-first, no over-engineering).
- Never lower `DOWNLOAD_DELAY` below 0.5s, even for tests — use `-a limit=N` instead.
