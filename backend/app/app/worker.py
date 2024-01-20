import logging

from app.core.celery_app import celery_app


def run_paper_requests_task(source: str):
    pass


@celery_app.task(acks_late=True)
def test_celery_worker(word: str) -> None:
    logging.info("Celery worker is working")
    logging.info(f"DONE: {word}")
