"""Spider `books` (phase D2): crawl the 1,000 product pages.

Start URLs come from data/listing.jsonl (the D1 output): the two spiders are
chained through the filesystem, not through code. Output is appended line by
line to data/books.jsonl — the file that will double as resume state.

Run: uv run scrapy crawl books   → data/books.jsonl
"""

import json
from pathlib import Path
from typing import ClassVar

import scrapy

from bouquineo.items import BookItem
from bouquineo.parsing import parse_count, parse_price, parse_rating, parse_stock


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains: ClassVar[list[str]] = ["books.toscrape.com"]

    listing_path = Path("data") / "listing.jsonl"

    async def start(self):
        """Emit one request per product URL collected by the listing spider."""
        for line in self.listing_path.read_text(encoding="utf-8").splitlines():
            yield scrapy.Request(json.loads(line)["url"], callback=self.parse)

    def parse(self, response):
        """Extract every enriched field of one product page.

        Scrapy contract (live check against a real product page):
        @url https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        @returns items 1 1
        @returns requests 0 0
        @scrapes upc title category price_excl_tax price_incl_tax tax stock rating num_reviews description url
        """
        # The striped table holds most fields as th/td rows: read it in one
        # pass into a dict, then decode each value.
        table = {
            row.css("th::text").get(): row.css("td::text").get()
            for row in response.css("table.table-striped tr")
        }
        yield BookItem(
            upc=table.get("UPC"),
            title=response.css("div.product_main h1::text").get(),
            category=response.css("ul.breadcrumb li:nth-child(3) a::text").get(),
            price_excl_tax=parse_price(table.get("Price (excl. tax)")),
            price_incl_tax=parse_price(table.get("Price (incl. tax)")),
            tax=parse_price(table.get("Tax")),
            stock=parse_stock(table.get("Availability")),
            rating=parse_rating(
                response.css("div.product_main p.star-rating::attr(class)").get()
            ),
            num_reviews=parse_count(table.get("Number of reviews")),
            description=response.css("#product_description ~ p::text").get(),
            url=response.url,
        )
