"""Field-level parsers shared by both spiders.

Each function decodes one presentation quirk of books.toscrape.com into a
usable value, and returns None on unexpected input (never raises): a broken
field must be logged and skipped by the caller, not crash the crawl.
"""

import re

# The rating lives in a CSS class ("star-rating Three"), not in any text node.
RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

# Real stock only appears on product pages, as "In stock (22 available)".
STOCK_RE = re.compile(r"\((\d+) available\)")


def parse_price(raw: str | None) -> float | None:
    """Decode a price string like '£51.77' into a float (51.77)."""
    if raw is None:
        return None
    match = re.search(r"\d+\.\d+", raw)
    return float(match.group()) if match else None


def parse_rating(css_class: str | None) -> int | None:
    """Decode a 'star-rating Three' CSS class into an int (3)."""
    if css_class is None:
        return None
    # The rating word is the last class token; unknown words map to None.
    return RATING_WORDS.get(css_class.split()[-1])


def parse_count(raw: str | None) -> int | None:
    """Decode a bare integer string like '0' into an int (0).

    Strict on purpose: the site shows a bare digit, so any surrounding text
    means the page changed — return None and let the caller log it.
    """
    if raw is None:
        return None
    return int(raw) if raw.strip().isdigit() else None


def parse_stock(availability: str | None) -> int | None:
    """Decode 'In stock (22 available)' into an int (22)."""
    if availability is None:
        return None
    match = STOCK_RE.search(availability)
    return int(match.group(1)) if match else None
