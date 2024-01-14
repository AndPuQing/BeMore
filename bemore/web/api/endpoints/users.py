from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from bemore.crud.crud_user import user as crud
from bemore.web.api.deps import get_current_active_superuser, SessionDep
from bemore.models import User, UserCreate, UserOut
from bemore.core.config import settings
from bemore.utils import (
    send_new_account_email,
)

router = APIRouter()


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=List[UserOut],
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return users


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserOut
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = crud.get_by_email(db=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    user = crud.create(db=session, user_create=user_in)
    if settings.EMAILS_ENABLED and user_in.email:
        send_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
    return user
