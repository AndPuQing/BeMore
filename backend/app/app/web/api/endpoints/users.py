from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlmodel import select

from app.core.config import settings
from app.crud.crud_user import user as crud
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

router = APIRouter()


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[UserOut],
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
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> UserOut:
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
            email_to=user_in.email,
            username=user_in.email,
            password=user_in.password,
        )
    return user


@router.put("/me", response_model=UserOut)
def update_user_me(
    *, session: SessionDep, body: UserUpdateMe, current_user: CurrentUser
) -> UserOut:
    """
    Update own user.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = UserUpdate(**current_user_data)
    if body.password is not None:
        user_in.password = body.password
    if body is not None:
        user_in.full_name = body.full_name
    if body is not None:
        user_in.email = body.email
    user = crud.update(db=session, session_obj=current_user, obj_in=user_in)
    return user


@router.get("/me", response_model=UserOut)
def read_user_me(session: SessionDep, current_user: CurrentUser) -> UserOut:
    """
    Get current user.
    """
    return current_user


@router.post("/open", response_model=UserOut)
def create_user_open(session: SessionDep, user_in: UserCreateOpen) -> UserOut:
    """
    Create new user without the need to be logged in.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = crud.get_by_email(db=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create(db=session, obj_in=user_create)
    return user


@router.get("/{user_id}", response_model=UserOut)
def read_user_by_id(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> UserOut:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            # TODO: Review status code
            status_code=400,
            detail="The user doesn't have enough privileges",
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
) -> UserOut:
    """
    Update a user.
    """

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = crud.update(db=session, db_obj=user, obj_in=user_in)
    return user
