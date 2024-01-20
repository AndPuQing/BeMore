from scrapy.http import HtmlResponse

from app.source.base import PaperRequestsTask


class Nips(PaperRequestsTask):
    def __init__(self):
        url: str = "https://nips.cc/Conferences/2023/Schedule?type=Poster"
        super().__init__(url)

    @staticmethod
    def get_urls(response: HtmlResponse) -> list[str]:
        poster_ids = response.css(".maincard::attr(id)").getall()
        urls = [
            f"https://nips.cc/Conferences/2023/Schedule?showEvent={poster_id.replace('maincard_', '')}"
            for poster_id in poster_ids
        ]
        return urls

    @staticmethod
    def parse(response: HtmlResponse):
        return {
            "type": response.css("div.maincardType::text").get(),
            "title": response.css("div.maincardBody::text").get(),
            "authors": response.css("div.maincardFooter::text").get(),
            "url": openreview_url(
                response.css("div.maincard span a::attr(href)").getall(),
            ),
            "abstract": response.css("div.abstractContainer::text").get(),
        }


def openreview_url(urls):
    for url in urls[::-1]:
        if "openreview" in url:
            return url
    return urls[0]  # if no openreview url, return the first url
