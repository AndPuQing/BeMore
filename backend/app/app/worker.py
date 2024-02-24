import inspect
import logging
from datetime import datetime, timedelta
from typing import Union

from celery import Task
from sqlmodel import Session, select

from app import source
from app.core.celery_app import celery_app
from app.core.config import settings
from app.models import CrawledItem
from app.source.base import PaperRequestsTask


@celery_app.on_after_configure.connect  # type: ignore
def setup_periodic_tasks(sender, **kwargs):
    # sender.add_periodic_task(
    #     crontab(minute="10"),
    #     paper_crawler.s(),
    #     name="crawl papers",
    # )
    pass


members = inspect.getmembers(source, inspect.isclass)
for name, _class in members:
    # auto register task
    celery_app.register_task(_class)


def batch(iterable: Union[set[str], list[str]], n: int = 1):
    """
    Batch generator.

    :param iterable: iterable object.
    :param n: batch size.
    """
    iterable = list(iterable)
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx : min(ndx + n, length)]


class DatabaseTask(Task):
    @property
    def db(self) -> Session:
        """
        Lazy loading of database connection.
        """
        from app.db.engine import engine

        return Session(engine)


@celery_app.task(
    acks_late=True,
    base=DatabaseTask,
    bind=True,
    ignore_result=True,
)
def paper_crawler(self: DatabaseTask) -> None:
    """
    Celery task to crawl papers from arxiv.
    """
    for name, _class in members:
        if issubclass(_class, PaperRequestsTask):
            urls = _class.get_urls()
            # duplicate urls
            urls = list(set(urls))
            # duplicate usls from db
            with self.db as db:
                crawled_urls = db.exec(
                    select(CrawledItem).where(
                        (CrawledItem.last_crawled - datetime.now())
                        <= timedelta(days=7)
                    )
                )
                crawled_urls = [item.raw_url for item in crawled_urls]
            urls = list(set(urls) - set(crawled_urls))
            if len(urls) > settings.REQUESTS_BATCH_SIZE:
                for batch_urls in batch(urls, settings.REQUESTS_BATCH_SIZE):
                    logging.info(
                        f"Start crawling {name} with {len(batch_urls)} urls"
                    )
                    celery_app.send_task(name, args=[batch_urls])
            else:
                logging.info(f"Start crawling {name} with {len(urls)} urls")
                celery_app.send_task(name, args=[urls])
        else:
            logging.info(f"Start crawling {name}")
            celery_app.send_task(name)
