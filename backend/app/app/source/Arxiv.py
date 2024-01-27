import logging
import re
from typing import Any

from scrapy.http import HtmlResponse

from app.source.base import PaperRequestsTask, RSSTask


class Arxiv(RSSTask):
    url: str = "http://export.arxiv.org/rss/cs"
    name: str = "Arxiv"
    _cache_category_map: dict[str, str] = {}

    @staticmethod
    def parse(entry: dict) -> dict[str, Any]:
        return {
            "title": entry["title"],
            "authors": entry["author"],
            "url": entry["link"],
            "abstract": entry["summary"],
        }

    @property
    def category_map(self):
        if not self._cache_category_map:
            response = PaperRequestsTask._request(
                "https://arxiv.org/category_taxonomy",
            )
            if response is None:
                return {}
            response = HtmlResponse(
                url="",
                body=response.text,
                encoding="utf-8",
            )
            category = response.css("h4::text").getall()
            full_name = response.css("span::text").getall()
            for i, c in enumerate(category):
                self._cache_category_map[c] = (
                    full_name[i].replace("(", "").replace(")", "")
                )

        return self._cache_category_map

    def post_parse(self, entry: dict[str, Any]) -> dict[str, Any]:
        entry["title"] = entry["title"].split("(", 1)[0]
        entry["authors"] = (
            HtmlResponse(url="", body=entry["authors"], encoding="utf-8")
            .css("a::text")
            .getall()
        )
        entry["abstract"] = (
            HtmlResponse(url="", body=entry["abstract"], encoding="utf-8")
            .css("p::text")
            .get()
        )
        category = re.findall(r"\[(.*?)\]", entry["title"])[0]
        if category in Arxiv.category_map:
            entry["category"] = self.category_map[category]
        else:
            logging.warning(f"Unknown category: {category}")
            entry["category"] = None
        return entry
