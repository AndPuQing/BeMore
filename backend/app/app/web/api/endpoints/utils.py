from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pydantic.networks import EmailStr

from app.models import FeedBack, Message
from app.utils import send_test_email
from app.web.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.worker import (
    paper_crawler,
    send_recommendation_email,
    train_doc2vec,
    train_recommender,
)

router = APIRouter()


class TaskOut(BaseModel):
    task_id: str
    status: str | None = None
    result: str | None = None


@router.post(
    "/test-email",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    send_test_email(email_to=email_to)
    return Message(message="Test email sent")


@router.get("/health_check", status_code=200)
def health_check() -> Message:
    """
    Check health.
    """
    return Message(message="OK")


@router.post(
    "/test-celery",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_celery() -> TaskOut:
    """
    Test celery.
    """
    task = paper_crawler.delay()
    return _to_task_out(task)


@router.get(
    "/test-doc2vec",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_doc2vec() -> TaskOut:
    """
    Test doc2vec.
    """
    task = train_doc2vec.delay()
    return _to_task_out(task)


@router.get(
    "/test-recommender",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_recommender() -> TaskOut:
    """
    Test recommender.
    """
    task = train_recommender.delay()
    return _to_task_out(task)


@router.get(
    "/test-send-recommender-email",
    response_model=TaskOut,
    dependencies=[Depends(get_current_active_superuser)],
)
def test_send_recommender_email(current_user: CurrentUser) -> TaskOut:
    """
    Test send recommender email.
    """
    user_id = current_user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="User id is None")
    task = send_recommendation_email.s([user_id]).delay()
    return _to_task_out(task)


def _to_task_out(r: AsyncResult) -> TaskOut:
    return TaskOut(
        task_id=r.task_id,  # type: ignore
        status=r.status,
    )


@router.get("/feedback/{user_id}/{item_id}", status_code=200)
def add_feedback(
    session: SessionDep, user_id: int, item_id: int, like: bool = True
) -> Any:
    """
    Create an item.
    """
    if like:
        session.add(
            FeedBack(
                user_id=user_id,
                item_id=item_id,
                feedback_type=5,
            ),
        )
        session.commit()
    # # back to the previous page
    return HTMLResponse(
        """
        <html>
        <body>
            <script>
                window.onload = function() {
                    window.close();
                };
            </script>
        </body>
        </html>
        """
    )
