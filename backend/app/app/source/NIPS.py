from scrapy.http import HtmlResponse

from app.source.base import PaperRequests


class Nips(PaperRequests):
    @staticmethod
    def get_urls(response: HtmlResponse):
        return response.css("div::attr(onclick)").getall()

    @staticmethod
    def parse(response: HtmlResponse):
        yield {
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
