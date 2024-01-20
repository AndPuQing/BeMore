from app.core.celery_app import celery_app
from app.core.config import settings
from app.source import Nips

celery_app.register_task(Nips())


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx : min(ndx + n, l)]


@celery_app.task(acks_late=True)
def test_celery_worker(word: str) -> None:
    urls = Nips.get_urls()
    for url in batch(urls, settings.REQUESTS_BATCH_SIZE):
        celery_app.send_task("Nips", kwargs={"urls": url})
