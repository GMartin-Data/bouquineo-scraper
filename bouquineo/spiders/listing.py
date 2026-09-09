"""Spider `listing` (phase D1): crawl the 50 list pages.

Collects title, price, rating and product-page URL for the 1,000 books.
The URLs are the input of the `books` spider (phase D2).

Run: uv run scrapy crawl listing   → data/listing.jsonl
"""

from typing import ClassVar

import scrapy

from bouquineo.items import BookListItem
from bouquineo.parsing import parse_price, parse_rating


class ListingSpider(scrapy.Spider):
    name = "listing"
    allowed_domains: ClassVar[list[str]] = ["books.toscrape.com"]
    start_url = "https://books.toscrape.com/"

    # 50 requests ≈ 30s: rerunning from scratch is cheaper than resume logic,
    # so the output file is rewritten on each run (idempotent by design).
    output_mode = "w"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_crawled = 0

    async def start(self):
        """Emit the first request (modern Scrapy 2.13+ entry point)."""
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):
        """Extract the 20 books of one list page, then follow the next link.

        Scrapy contracts (live checks against the real site: scrapy check):
        @url https://books.toscrape.com/
        @returns items 20 20
        @returns requests 1 1
        @scrapes title price rating url
        """
        self.pages_crawled += 1

        for book in response.css("article.product_pod"):
            # Anchor TEXT truncates long titles ("A Light in the ...");
            # the full title only lives in the title attribute.
            yield BookListItem(
                title=book.css("h3 a::attr(title)").get(),
                price=parse_price(book.css("p.price_color::text").get()),
                rating=parse_rating(book.css("p.star-rating::attr(class)").get()),
                url=response.urljoin(book.css("h3 a::attr(href)").get()),
            )

        # Hrefs are relative to the CURRENT page (no catalogue/ prefix past
        # page 1): response.follow resolves them like a browser would.
        next_link = response.css("li.next a::attr(href)").get()
        if next_link is not None:
            yield response.follow(next_link, callback=self.parse)

    def closed(self, reason):
        """Log the crawl summary the brief asks for (pages walked)."""
        self.logger.info("Crawl finished (%s): %d list pages crawled", reason, self.pages_crawled)
