-- Books table: one row per catalogue product, keyed by UPC.
-- Idempotent (IF NOT EXISTS): applied by db/load.py on every run.
--
-- Money columns are NUMERIC, never FLOAT: exact decimal arithmetic is the
-- rule for prices in a database, even when the source is a JSON float.

CREATE TABLE IF NOT EXISTS books (
    upc            TEXT PRIMARY KEY,          -- proven unique at load time
    title          TEXT NOT NULL,             -- human label, NOT the key (note 02)
    category       TEXT,
    price_excl_tax NUMERIC(6, 2),
    price_incl_tax NUMERIC(6, 2),
    tax            NUMERIC(6, 2),
    stock          INTEGER,                   -- NULL = quantity unknown, not zero
    rating         SMALLINT CHECK (rating BETWEEN 1 AND 5),
    num_reviews    INTEGER,
    description    TEXT,                      -- missing on some product pages
    url            TEXT NOT NULL UNIQUE
);
