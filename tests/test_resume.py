"""Unit tests for the resume layer: re-reading the output JSONL as state.

Contract under test: seen_urls never raises — it runs precisely after a
crash, so it must survive whatever state the crash left on disk (missing
file, truncated final line) and treat bad lines as "not collected".
"""

from bouquineo.resume import seen_urls


def test_nominal(tmp_path):
    path = tmp_path / "books.jsonl"
    path.write_text(
        '{"upc": "a", "url": "https://site/book-1"}\n'
        '{"upc": "b", "url": "https://site/book-2"}\n',
        encoding="utf-8",
    )
    assert seen_urls(path) == {"https://site/book-1", "https://site/book-2"}


def test_missing_file(tmp_path):
    # First run ever: no output file yet -> nothing seen, full crawl.
    assert seen_urls(tmp_path / "books.jsonl") == set()


def test_truncated_last_line(tmp_path):
    # A kill mid-write leaves a partial JSON line: the good lines must
    # survive, the broken one counts as "not collected" (will be re-crawled).
    path = tmp_path / "books.jsonl"
    path.write_text(
        '{"upc": "a", "url": "https://site/book-1"}\n'
        '{"upc": "b", "url": "https://si',
        encoding="utf-8",
    )
    assert seen_urls(path) == {"https://site/book-1"}


def test_unicode_line_separator_in_description(tmp_path):
    # U+2028/U+2029 appear RAW inside real descriptions (json.dumps with
    # ensure_ascii=False does not escape them). They are NOT line breaks:
    # the line must parse and its url must count as seen — regression test
    # for the str.splitlines() bug found while loading the full catalogue.
    path = tmp_path / "books.jsonl"
    description = "part one\u2028part two\u2029end"
    path.write_text(
        f'{{"description": "{description}", "url": "https://site/book-1"}}\n',
        encoding="utf-8",
    )
    assert seen_urls(path) == {"https://site/book-1"}


def test_line_without_url_key(tmp_path):
    # Valid JSON but no url field: unusable as state, skip it silently.
    path = tmp_path / "books.jsonl"
    path.write_text('{"upc": "a"}\n', encoding="utf-8")
    assert seen_urls(path) == set()
