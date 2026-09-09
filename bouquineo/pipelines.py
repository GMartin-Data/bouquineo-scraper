"""Item pipelines: what happens to every item a spider yields.

Single pipeline here: append-as-you-go JSONL writing. Writing line by line
(not at the end) is what makes the output file usable as resume state —
whatever is on disk when a crawl dies is exactly what was collected.
"""

import json
from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.crawler import Crawler


class JsonlWritePipeline:
    """Write each item as one JSON line to data/<spider.name>.jsonl.

    File mode comes from the spider's `output_mode` attribute:
    - "a" (default): append — required for the resumable `books` crawl;
    - "w": rewrite from scratch — for the cheap, rerun-anytime `listing` crawl.
    """

    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler):
        # Modern Scrapy (2.13+) no longer passes `spider` to pipeline methods:
        # the crawler instance, saved here, gives access to it instead.
        pipeline = cls()
        pipeline.crawler = crawler
        return pipeline

    def open_spider(self):
        spider = self.crawler.spider
        assert spider is not None  # a pipeline only opens for a live spider
        path = Path("data") / f"{spider.name}.jsonl"
        path.parent.mkdir(exist_ok=True)
        self.file = path.open(getattr(spider, "output_mode", "a"), encoding="utf-8")

    def close_spider(self):
        self.file.close()

    def process_item(self, item):
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False)
        self.file.write(line + "\n")
        self.file.flush()  # each line hits disk immediately: crash-safe state
        return item
