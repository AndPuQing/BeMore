from typing import Any

from app.source.base import RSSTask


class PMLR(RSSTask):
    url: str = "http://proceedings.mlr.press//v221/assets/rss/feed.xml"
    name: str = "PMLR"

    @staticmethod
    def parse(entry: dict) -> dict[str, Any]:
        return {
            "title": entry["title"],
            "url": entry["link"],
            "abstract": entry["description"],
        }
