from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pydantic.networks import EmailStr

from app.models import Message
from app.utils import send_test_email
from app.web.api.deps import get_current_active_superuser
from app.worker import test_celery_worker

router = APIRouter()


class TaskOut(BaseModel):
    task_id: str
    status: str | None = None
    result: str | None = None


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    send_test_email(email_to=email_to)
    return Message(message="Test email sent")


@router.post(
    "/texst-celery/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_celery(word: str) -> TaskOut:
    """
    Test celery.
    """
    task = test_celery_worker.delay(word)
    return _to_task_out(task)


def _to_task_out(r: AsyncResult) -> TaskOut:
    return TaskOut(
        task_id=r.task_id,  # type: ignore
        status=r.status,
    )
