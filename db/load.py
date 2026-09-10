"""Load data/books.jsonl into PostgreSQL — idempotent upsert on UPC.

Decoupled from scraping (landing-zone pattern): the crawl never touches the
DB, this script never touches the network. Re-running it any number of times
converges to the same state (ON CONFLICT (upc) DO UPDATE), so a corrected
crawl just needs a reload.

The input is read STRICTLY: a malformed line crashes the load before any
write reaches the table. Loading is the moment to fail loudly — the DB must
never silently receive partial or corrupt data.

Run: uv run python db/load.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import LiteralString, cast

import psycopg
from dotenv import load_dotenv

BOOKS_PATH = Path("data") / "books.jsonl"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

COLUMNS = (
    "upc",
    "title",
    "category",
    "price_excl_tax",
    "price_incl_tax",
    "tax",
    "stock",
    "rating",
    "num_reviews",
    "description",
    "url",
)

UPSERT = f"""
    INSERT INTO books ({", ".join(COLUMNS)})
    VALUES ({", ".join(f"%({c})s" for c in COLUMNS)})
    ON CONFLICT (upc) DO UPDATE SET
        {", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS if c != "upc")}
"""


def conninfo() -> str:
    """Build the connection string from .env (fails loudly on a missing key)."""
    load_dotenv()
    return (
        f"host={os.environ['POSTGRES_HOST']} "
        f"port={os.environ['POSTGRES_PORT']} "
        f"dbname={os.environ['POSTGRES_DB']} "
        f"user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )


def main() -> None:
    # File iteration, not splitlines(): descriptions legally contain raw
    # U+2028/U+2029, which splitlines() mistakes for line breaks.
    with BOOKS_PATH.open(encoding="utf-8") as file:
        books = [json.loads(line) for line in file]
    # psycopg types queries as LiteralString to flag injection risks; our
    # schema and upsert are repo-owned text, so the casts are legitimate.
    schema = cast("LiteralString", SCHEMA_PATH.read_text(encoding="utf-8"))
    with psycopg.connect(conninfo()) as conn, conn.cursor() as cur:
        cur.execute(schema)
        cur.executemany(cast("LiteralString", UPSERT), books)
        row = cur.execute("SELECT count(*) FROM books").fetchone()
        assert row is not None
        total = row[0]
    # One transaction for everything: the load lands entirely or not at all.
    print(f"Upserted {len(books)} books from {BOOKS_PATH}; table now holds {total} rows.")


if __name__ == "__main__":
    main()
