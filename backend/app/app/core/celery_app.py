from celery import Celery

celery_app = Celery("worker", broker="amqp://guest@bemore-queue//")

celery_app.conf.task_routes = {"app.worker.test_celery": "main-queue"}
