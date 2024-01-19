from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "worker",
    broker="amqp://guest@bemore-queue//",
    backend="db+"
    + f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@bemore-db/{settings.POSTGRES_DB}",
)
