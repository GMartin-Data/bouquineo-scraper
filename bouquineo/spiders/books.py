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
from scrapy.exceptions import CloseSpider

from bouquineo.items import BookItem
from bouquineo.parsing import parse_count, parse_price, parse_rating, parse_stock
from bouquineo.resume import seen_urls


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains: ClassVar[list[str]] = ["books.toscrape.com"]

    listing_path = Path("data") / "listing.jsonl"
    # Must match the pipeline's data/<spider.name>.jsonl convention.
    output_path = Path("data") / "books.jsonl"

    # 10 failed requests ≈ 1% of the catalogue: above that the site has
    # likely changed and every further request is wasted — stop and
    # investigate. Enforced in the errback (see on_error).
    max_failures = 10

    def __init__(self, *args, limit=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Sample mode (-a limit=N): cap the NEW pages of this run. Counted
        # after the resume filter, so successive limited runs advance
        # through the catalogue instead of redoing the same pages.
        self.limit = int(limit) if limit is not None else None
        self.failures = 0

    async def start(self):
        """Emit one request per listing URL not already collected.

        A malformed listing.jsonl crashes loudly here, BEFORE any request:
        the D1 output is this spider's input contract — better fail fast
        than crawl on corrupt fuel.
        """
        seen = seen_urls(self.output_path)
        if seen:
            self.logger.info("Resume: %d books already collected, skipping them", len(seen))
        emitted = 0
        # File iteration, not splitlines(): see the warning in resume.py.
        with self.listing_path.open(encoding="utf-8") as file:
            for line in file:
                url = json.loads(line)["url"]
                if url in seen:
                    continue
                if self.limit is not None and emitted >= self.limit:
                    self.logger.info("Sample mode: stopping after %d new pages", self.limit)
                    break
                emitted += 1
                yield scrapy.Request(url, callback=self.parse, errback=self.on_error)

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

    def on_error(self, failure):
        """Log a failed request and move on — one bad page must not kill the crawl.

        The systemic-failure guard lives here: CLOSESPIDER_ERRORCOUNT only
        counts callback exceptions (verified in the Scrapy source), which our
        tolerant parsing never raises — so the errback counts failures itself
        and closes the spider past the threshold.
        """
        self.failures += 1
        self.logger.error(
            "Request failed (%d/%d), skipping: %s — %s",
            self.failures,
            self.max_failures,
            failure.request.url,
            failure.value,
        )
        if self.failures >= self.max_failures:
            raise CloseSpider("too_many_failed_requests")

    def closed(self, reason):
        """Log the crawl summary: how it ended and how many requests failed."""
        self.logger.info("Crawl finished (%s): %d failed requests", reason, self.failures)
