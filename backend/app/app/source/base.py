import logging

import requests
from celery import Task
from scrapy.http import HtmlResponse
from sqlmodel import Session

from app.models import CrawledItem, Item


class PaperRequestsTask(Task):
    url: str
    ignore_result: bool = True

    @property
    def db(self):
        """
        Lazy loading of database connection.
        """
        from app.db.engine import engine

        return Session(engine)

    @staticmethod
    def parse_urls(response: HtmlResponse) -> list[str]:
        # you should return list of absolute urls
        raise NotImplementedError

    @classmethod
    def get_urls(cls) -> list[str]:
        response = cls._request(cls.url)
        if response is None:
            return []
        return cls.parse_urls(response)

    @staticmethod
    def parse(response: HtmlResponse) -> dict[str, str]:
        # you should return dict with fields:
        # title, abstract, url
        raise NotImplementedError

    @staticmethod
    def _request(
        url: str,
    ) -> HtmlResponse | None:  # On the Take class have same method(request)
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(e)
            return
        return HtmlResponse(url=url, body=response.content, encoding="utf-8")

    def save(self, data: list[dict[str, str]]) -> None:
        with self.db as db:
            objs = [
                CrawledItem(
                    raw_url=item["url"],
                )
                for item in data
            ]
            db.add_all(objs)
            db.commit()

            objs = [
                Item(
                    title=item["title"],
                    abstract=item["abstract"],
                    raw_url=item["url"],
                )
                for item in data
            ]
            db.add_all(objs)
            db.commit()

    def run(self, urls: list[str]):
        results = []
        for url in urls:
            response = PaperRequestsTask._request(url)
            if response is None:
                continue
            results.append(self.parse(response))
        self.save(results)
