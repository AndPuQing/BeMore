from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.models import FeedBack, FeedBackType, Message
from app.web.api.deps import SessionDep

router = APIRouter()


@router.get("/", response_model=list[FeedBack])
def read_feedbacks(
    session: SessionDep,
    cursor: int = 0,
    num: int = 10,
) -> Any:
    """
    Retrieve items.
    """
    if cursor < 1:
        raise HTTPException(
            status_code=400,
            detail="Page number must be greater than or equal to 1.",
        )
    if num < 1:
        raise HTTPException(
            status_code=400, detail="Limit must be greater than or equal to 1."
        )
    skip = (cursor - 1) * num
    feedbacks = session.exec(select(FeedBack).offset(skip).limit(num)).all()
    return feedbacks


@router.post("/", response_model=Message)
def create_feedback(
    session: SessionDep,
    feedbacks: list[FeedBack],
) -> Any:
    """
    Create an item.
    """
    for feedback in feedbacks:
        FeedBack.create(session, feedback)
    return Message(message="success")


@router.get("/{feedback_type}", response_model=list[FeedBack])
def read_feedbacks_by_type(
    session: SessionDep,
    feedback_type: FeedBackType,
    cursor: int = 0,
    num: int = 10,
) -> Any:
    """
    Retrieve items.
    """
    if cursor < 1:
        raise HTTPException(
            status_code=400,
            detail="Page number must be greater than or equal to 1.",
        )
    if num < 1:
        raise HTTPException(
            status_code=400, detail="Limit must be greater than or equal to 1."
        )
    skip = (cursor - 1) * num
    feedbacks = session.exec(
        select(FeedBack)
        .where(FeedBack.feedback_type == feedback_type)
        .offset(skip)
        .limit(num)
    ).all()
    return feedbacks


@router.get(
    "/{feedback_type}/{user_id}/{item_id}", response_model=list[FeedBack]
)
def read_feedbacks_by_user_item(
    session: SessionDep,
    feedback_type: FeedBackType,
    user_id: int,
    item_id: int,
) -> Any:
    """
    Retrieve items.
    """
    feedbacks = session.exec(
        select(FeedBack)
        .where(FeedBack.feedback_type == feedback_type)
        .where(FeedBack.user_id == user_id)
        .where(FeedBack.item_id == item_id)
    ).all()
    return feedbacks


@router.delete("/{feedback_type}/{user_id}/{item_id}")
def delete_feedback(
    session: SessionDep,
    feedback_type: FeedBackType,
    user_id: int,
    item_id: int,
) -> Any:
    """
    Delete an item.
    """
    feedbacks = session.exec(
        select(FeedBack)
        .where(FeedBack.feedback_type == feedback_type)
        .where(FeedBack.user_id == user_id)
        .where(FeedBack.item_id == item_id)
    ).all()
    for feedback in feedbacks:
        feedback.delete(session)
    return Message(message="success")
