from scrapy.http import HtmlResponse

from app.source.base import PaperRequestsTask, PaperType, openreview_url


class NIPS(PaperRequestsTask):
    url: str = "https://nips.cc/Conferences/2023/Schedule?type=Poster"
    name: str = "NIPS"

    @classmethod
    def parse_urls(cls, response: HtmlResponse) -> list[str]:
        poster_ids = response.css(".maincard::attr(id)").getall()
        urls = [
            f"{cls.url}showEvent={poster_id.replace('maincard_', '')}"
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
    def post_parse(item: PaperType) -> PaperType:
        if item["authors"] is not None:
            item["authors"] = item["authors"].split(" · ")  # type: ignore
        if item["authors"] is not None:
            for i, author in enumerate(item["authors"]):
                item["authors"][i] = author.strip()
        return item
