from typing import Any

from app.core.config import settings
from app.models import (
    User,
    UserCreate,
    UserCreateOpen,
    UserOut,
    UserUpdate,
    UserUpdateMe,
)
from app.utils import send_new_account_email
from app.web.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from starlette import status

router = APIRouter()


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[UserOut],
    status_code=status.HTTP_200_OK,
)
def read_users(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve users.
    """
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return users


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = User.first_by_field(session, "email", user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = User.create(session, user_in)
    if settings.EMAILS_ENABLED and user_in.email:
        send_new_account_email(
            email_to=user_in.email,
            username=user_in.email,
            password=user_in.password,
        )
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to create user.",
        )
    return user


@router.put("/me", response_model=UserOut)
def update_user_me(
    *, session: SessionDep, body: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    current_user.update(session, body)
    return current_user


@router.get("/me", response_model=UserOut)
def read_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.post("/open", response_model=UserOut)
def create_user_open(session: SessionDep, user_in: UserCreateOpen) -> Any:
    """
    Create new user without the need to be logged in.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = User.first_by_field(session, "email", user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user = User.create(session, user_in)
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to create user.",
        )
    return user


@router.get("/{user_id}", response_model=UserOut)
def read_user_by_id(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get a specific user by id.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            # TODO: Review status code
            status_code=400,
            detail="The user doesn't have enough privileges",
        )
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    return user


@router.put(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserOut,
)
def update_user(
    *,
    session: SessionDep,
    user_id: int,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user.update(session, user_in)
    return user
