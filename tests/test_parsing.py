"""Unit tests for the field parsers — the one deterministic, I/O-free layer.

Contract under test: valid input → decoded value; unexpected input → None
(never an exception), so that a broken page gets logged and skipped instead
of killing the crawl.
"""

import pytest

from bouquineo.parsing import parse_count, parse_price, parse_rating, parse_stock


class TestParsePrice:
    def test_nominal(self):
        assert parse_price("£51.77") == 51.77

    def test_no_number(self):
        assert parse_price("free") is None

    def test_none_input(self):
        assert parse_price(None) is None


class TestParseRating:
    @pytest.mark.parametrize(
        ("css_class", "expected"),
        [("star-rating One", 1), ("star-rating Three", 3), ("star-rating Five", 5)],
    )
    def test_nominal(self, css_class, expected):
        assert parse_rating(css_class) == expected

    def test_unknown_word(self):
        assert parse_rating("star-rating Six") is None

    def test_none_input(self):
        assert parse_rating(None) is None


class TestParseCount:
    def test_nominal(self):
        assert parse_count("0") == 0

    def test_not_a_number(self):
        assert parse_count("many") is None

    def test_none_input(self):
        assert parse_count(None) is None


class TestParseStock:
    def test_nominal(self):
        assert parse_stock("In stock (22 available)") == 22

    def test_out_of_stock_text(self):
        # No "(N available)" pattern: unknown quantity, not zero.
        assert parse_stock("Out of stock") is None

    def test_none_input(self):
        assert parse_stock(None) is None
