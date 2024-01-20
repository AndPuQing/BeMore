from app.core.celery_app import celery_app
from app.source.NIPS import Nips


@celery_app.task(acks_late=True)
def test_celery_worker(word: str) -> None:
    print(f"word: {word}")
    Nips("https://nips.cc/Conferences/2023/Schedule?type=Poster").run()
    print("done")
