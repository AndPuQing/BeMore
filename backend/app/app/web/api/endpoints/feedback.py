from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.models import FeedBack, FeedBackType, Message
from app.web.api.deps import SessionDep, get_current_active_superuser

router = APIRouter()


@router.get(
    "/",
    response_model=list[FeedBack],
    dependencies=[Depends(get_current_active_superuser)],
)
def read_feedbacks(
    session: SessionDep,
    cursor: int = 1,
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


@router.post(
    "/",
    response_model=Message,
    dependencies=[Depends(get_current_active_superuser)],
)
def create_feedback(
    session: SessionDep,
    feedbacks: list[FeedBack],
) -> Any:
    """
    Create an item.
    """
    num = 0
    for feedback in feedbacks:
        temp = FeedBack.create(session, feedback)
        if temp is not None:
            num += 1
    return Message(message=f"success {num} items")


@router.get(
    "/{feedback_type}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[FeedBack],
)
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
    "/{feedback_type}/{item_id}",
    response_model=list[FeedBack],
    dependencies=[Depends(get_current_active_superuser)],
)
def read_feedbacks_by_item_feedback(
    session: SessionDep,
    feedback_type: FeedBackType,
    item_id: int,
    cursor: int = 1,
    num: int = 100,
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
        .where(FeedBack.item_id == item_id)
        .offset(skip)
        .limit(num)
    ).all()
    return feedbacks


@router.get(
    "/{feedback_type}/{user_id}",
    response_model=list[FeedBack],
    dependencies=[Depends(get_current_active_superuser)],
)
def read_feedbacks_by_user_feedback(
    session: SessionDep,
    feedback_type: FeedBackType,
    user_id: int,
    cursor: int = 1,
    num: int = 100,
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
        .where(FeedBack.user_id == user_id)
        .offset(skip)
        .limit(num)
    ).all()
    return feedbacks


@router.get(
    "/{user_id}/{item_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[FeedBack],
)
def read_feedbacks_by_user_item_all(
    session: SessionDep,
    user_id: int,
    item_id: int,
) -> Any:
    """
    Retrieve items.
    """
    feedbacks = session.exec(
        select(FeedBack)
        .where(FeedBack.user_id == user_id)
        .where(FeedBack.item_id == item_id)
    ).all()
    return feedbacks


@router.get(
    "/{item_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[FeedBack],
)
def read_feedbacks_by_item(
    session: SessionDep,
    item_id: int,
    cursor: int = 1,
    num: int = 100,
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
        .where(FeedBack.item_id == item_id)
        .offset(skip)
        .limit(num)
    ).all()
    return feedbacks


@router.get(
    "/{user_id}",
    response_model=list[FeedBack],
    dependencies=[Depends(get_current_active_superuser)],
)
def read_feedbacks_by_user(
    session: SessionDep,
    user_id: int,
    cursor: int = 1,
    num: int = 100,
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
        .where(FeedBack.user_id == user_id)
        .offset(skip)
        .limit(num)
    ).all()
    return feedbacks


@router.get(
    "/{feedback_type}/{user_id}/{item_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[FeedBack],
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
