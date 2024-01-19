import time

from app.core.celery_app import celery_app


@celery_app.task(acks_late=True)
def test_celery_worker(word: str) -> None:
    print(f"word: {word}")
    time.sleep(5)
    print("done")
