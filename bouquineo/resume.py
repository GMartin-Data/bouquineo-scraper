"""Resume layer: the output JSONL re-read as crawl state.

Design option A: no checkpoint file, no DB — whatever reached disk IS what
was collected. The books spider resumes by diffing its input URLs against
this set at startup.
"""

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
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            urls.add(json.loads(line)["url"])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue  # truncated or malformed line: redoing one request is cheap
    return urls
