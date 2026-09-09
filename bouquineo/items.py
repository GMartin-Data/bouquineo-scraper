"""Item schemas: the explicit contract of what each spider collects.

Declaring fields (rather than yielding bare dicts) makes typos fail loudly
at yield time instead of silently producing misnamed JSONL keys.
"""

import scrapy


class BookListItem(scrapy.Item):
    """One book as seen on a list page (spider `listing`, phase D1)."""

    title = scrapy.Field()   # from a/@title (anchor text truncates long titles)
    price = scrapy.Field()   # float, decoded from '£51.77'
    rating = scrapy.Field()  # int 1-5, decoded from the star-rating CSS class
    url = scrapy.Field()     # absolute product-page URL: the fuel for phase D2
