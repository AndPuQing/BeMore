import logging
from abc import abstractmethod

import requests
from scrapy.http import HtmlResponse

from app.core.celery_app import celery_app
from app.core.config import settings


class PaperRequests:
    def __init__(self, url):
        self.url = url

    @abstractmethod
    def get_urls(self, response: HtmlResponse) -> list:
        raise NotImplementedError

    @abstractmethod
    @celery_app.task(acks_late=True)
    def parse(self, response: HtmlResponse) -> None:
        raise NotImplementedError

    @staticmethod
    def request(url: str) -> HtmlResponse | None:
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(e)
            return
        return HtmlResponse(url=url, body=response.content, encoding="utf-8")

    @staticmethod
    def batch_urls(urls: list, batch_size: int = settings.REQUESTS_BATCH_SIZE):
        for i in range(0, len(urls), batch_size):
            yield urls[i : i + batch_size]

    def run(self):
        self.response = self.request(self.url)
        if self.response is None:
            return
        urls = self.get_urls(self.response)
        logging.info(f"From {self.url} found {len(urls)} urls")
        for batch in self.batch_urls(urls):
            self.parse.delay(batch)
