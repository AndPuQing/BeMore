
import xml.dom.minidom

from scrapy.http import HtmlResponse

from app.source.base import PaperRequestsTask, PaperType


class AAAI(PaperRequestsTask):
    url: str = (
        "https://dblp.uni-trier.de/search/publ/api?q=toc%3Adb/conf/aaai/aaai2023.bht%3A&h=1000&format=xml"
    )
    name: str = "AAAI"

    @staticmethod
    def parse_urls(response: HtmlResponse) -> list[str]:
        _xml = response.text
        domTree = xml.dom.minidom.parseString(_xml)
        collection = domTree.documentElement

        hits = collection.getElementsByTagName("hit")
        urls = []
        for hit in hits:
            url = hit.getElementsByTagName("ee")[0]
            urls.append(url.childNodes[0].data)
        return urls

    @staticmethod
    def parse(response: HtmlResponse):
        item = {
            "title": response.css("h1.page_title::text").get().strip(),  # type: ignore
            "abstract": response.css("section.abstract::text").getall()[1].strip(),  # type: ignore
            "url": response.css("a.pdf::attr(href)").get(),
            "keywords": response.css("section.keywords span.value::text")
            .get()
            .replace("\t", "")  # type: ignore
            .replace("\n", "")
            .split(", "),
            "authors": response.css("span.name::text").getall(),
        }

        return item

    @staticmethod
    def post_parse(item: PaperType) -> PaperType:
        if item["authors"] is not None:
            for i, author in enumerate(item["authors"]):
                item["authors"][i] = author.strip()
        return item
