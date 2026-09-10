"""Resume layer: the output JSONL re-read as crawl state.

Design option A: no checkpoint file, no DB — whatever reached disk IS what
was collected. The books spider resumes by diffing its input URLs against
this set at startup.
"""

from __future__ import annotations

import json
from pathlib import Path


def seen_urls(path: Path) -> set[str]:
    """Return the product URLs already collected in a JSONL output file.

    Never raises: this runs precisely after a crash, so it must survive
    whatever state the crash left on disk. A missing file means a fresh
    start; an unparseable or url-less line counts as "not collected" (that
    page will simply be crawled again).
    """
    if not path.exists():
        return set()
    urls: set[str] = set()
    # Iterate the open file, NOT read_text().splitlines(): splitlines() also
    # breaks on Unicode separators (U+2028/U+2029) that legally appear RAW
    # inside JSON strings — which would shred valid lines and cause endless
    # re-crawls of the same books. File iteration splits on \n only.
    with path.open(encoding="utf-8") as file:
        for line in file:
            try:
                urls.add(json.loads(line)["url"])
            except (json.JSONDecodeError, KeyError, TypeError):
                continue  # truncated or malformed line: redoing one request is cheap
    return urls
