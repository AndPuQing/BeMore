import logging
from abc import abstractmethod

import requests
from celery import Task
from scrapy.http import HtmlResponse


class PaperRequestsTask(Task):
    def __init__(self, url):
        self.url = url

    @abstractmethod
    @staticmethod
    def get_urls(response: HtmlResponse) -> list[str]:
        # you should return list of absolute urls
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def parse(response: HtmlResponse) -> dict[str, str]:
        # you should return dict with fields:
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

    def run(self, urls: list[str]):
        results = []
        for url in urls:
            response = PaperRequestsTask.request(url)
            if response is None:
                continue
            results.append(self.parse(response))
        return results
