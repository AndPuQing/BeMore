import logging
from typing import Union

from celery import Task
from sqlmodel import Session, select

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models import CrawledItem
from app.source import Nips

celery_app.register_task(Nips())


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
def test_celery_worker(self: DatabaseTask, word: str) -> None:
    urls = set(Nips.get_urls())

    # remove duplicates from db
    with self.db as db:
        items = set(db.exec(select(CrawledItem.raw_url)).all())
    dup_urls = urls - items

    # Calculate cache hit rate
    cache_hit_rate = (len(urls) - len(dup_urls)) / len(urls) if urls else 0

    # Log cache hit rate
    logging.info(f"Cache hit rate: {cache_hit_rate * 100:.2f}%")

    for url in batch(urls, settings.REQUESTS_BATCH_SIZE):
        celery_app.send_task("Nips", kwargs={"urls": url})
