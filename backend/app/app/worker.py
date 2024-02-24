import inspect
from typing import Union

from celery import Task
from celery.schedules import crontab
from sqlmodel import Session

from app import source
from app.core.celery_app import celery_app


@celery_app.on_after_configure.connect  # type: ignore
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('hello') every 30 seconds.
    # It uses the same signature of previous task, an explicit name is
    # defined to avoid this task replacing the previous one defined.
    sender.add_periodic_task(30.0, test.s('hello'), name='add every 30')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        test.s('Happy Mondays!'),
    )


@celery_app.task
def test(arg):
    print(arg)


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
def test_celery_worker(self: DatabaseTask, word: str) -> None:
    celery_app.send_task("Arxiv")
