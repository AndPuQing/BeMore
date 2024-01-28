from typing import Any

from app.source.base import PaperRequestsTask, openreview_url
from scrapy.http import HtmlResponse


class NIPS(PaperRequestsTask):
    url: str = "https://nips.cc/Conferences/2023/Schedule?type=Poster"
    name: str = "NIPS"

    @staticmethod
    def parse_urls(response: HtmlResponse) -> list[str]:
        poster_ids = response.css(".maincard::attr(id)").getall()
        urls = [
            f"https://nips.cc/Conferences/2023/Schedule?showEvent={poster_id.replace('maincard_', '')}"
            for poster_id in poster_ids
        ]
        return urls

    @staticmethod
    def parse(response: HtmlResponse):
        item = {
            "title": response.css("div.maincardBody::text").get(),
            "authors": response.css("div.maincardFooter::text").get(),
            "url": openreview_url(
                response.css("div.maincard span a::attr(href)").getall(),
            ),
            "abstract": response.css("div.abstractContainer p::text").get(),
        }
        if item["abstract"] is None:
            item["abstract"] = response.css("div.abstractContainer::text").get()

        return item

    @staticmethod
    def post_parse(item: dict[str, Any]) -> dict[str, Any]:
        if item["authors"] is not None:
            item["authors"] = item["authors"].split(" · ")
        if item["authors"] is not None:
            for i, author in enumerate(item["authors"]):
                item["authors"][i] = author.strip()
        return item
