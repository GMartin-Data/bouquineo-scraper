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

_Sections below (installation, usage, design rationale) are completed as the
project progresses._

## Author

Grégory Martin
