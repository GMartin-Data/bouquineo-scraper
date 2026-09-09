"""Item schemas: the explicit contract of what each spider collects.

Declaring fields (rather than yielding bare dicts) makes typos fail loudly
at yield time instead of silently producing misnamed JSONL keys.
"""

import scrapy


class BookItem(scrapy.Item):
    """One book as seen on its product page (spider `books`, phase D2).

    The three price fields are collected despite their observed redundancy
    (excl == incl, tax == 0 everywhere): landing-zone fidelity — the
    conclusion belongs to the observation note, not to the collector.
    """

    upc = scrapy.Field()             # the real key (ON CONFLICT target in DB)
    title = scrapy.Field()
    category = scrapy.Field()        # breadcrumb, 3rd item
    price_excl_tax = scrapy.Field()  # float, decoded from '£51.77'
    price_incl_tax = scrapy.Field()  # float
    tax = scrapy.Field()             # float
    stock = scrapy.Field()           # int, from '(N available)'; None if absent
    rating = scrapy.Field()          # int 1-5, from the star-rating CSS class
    num_reviews = scrapy.Field()     # int, from the bare digit in the table
    description = scrapy.Field()     # missing on some pages -> None
    url = scrapy.Field()             # resume key during the crawl


class BookListItem(scrapy.Item):
    """One book as seen on a list page (spider `listing`, phase D1)."""

    title = scrapy.Field()   # from a/@title (anchor text truncates long titles)
    price = scrapy.Field()   # float, decoded from '£51.77'
    rating = scrapy.Field()  # int 1-5, decoded from the star-rating CSS class
    url = scrapy.Field()     # absolute product-page URL: the fuel for phase D2
