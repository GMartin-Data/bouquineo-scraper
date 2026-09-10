"""Project-wide crawl configuration.

Only deliberate choices live here; everything else keeps Scrapy's defaults.
Each politeness setting answers an explicit requirement of the brief.
"""

BOT_NAME = "bouquineo"

SPIDER_MODULES = ["bouquineo.spiders"]
NEWSPIDER_MODULE = "bouquineo.spiders"

# --- Politeness (brief: explicit UA, justified delay) ---------------------

# Nominative User-Agent: identifies who crawls and why, with a contact.
USER_AGENT = (
    "bouquineo-training-scraper "
    "(Gregory Martin; gregory.martin.data@gmail.com; 2-day training brief)"
)

# robots.txt returns 404 on this site (= no restrictions), but obeying is
# the correct default posture and costs nothing.
ROBOTSTXT_OBEY = True

# 0.5s between requests, one request at a time: the full 1,000-page crawl
# takes ~10 min — fast enough to finish well within a day, slow enough to
# stay a negligible load for the server. Scrapy randomizes the actual delay
# (0.5x-1.5x) to avoid a robotic request pattern.
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# --- Robustness (brief: how many failures before giving up?) --------------

# NB: this only counts CALLBACK exceptions (spider_error signal) — failed
# requests never reach it. The "10 failures ≈ 1% → give up" guard therefore
# lives in the books spider's errback (max_failures + CloseSpider); this
# setting stays as a safety net against genuine code bugs in callbacks.
CLOSESPIDER_ERRORCOUNT = 10

# --- Output ---------------------------------------------------------------

ITEM_PIPELINES = {
    "bouquineo.pipelines.JsonlWritePipeline": 300,
}

# INFO keeps logs demo-readable; DEBUG remains one -s LOG_LEVEL=DEBUG away.
LOG_LEVEL = "INFO"

FEED_EXPORT_ENCODING = "utf-8"
