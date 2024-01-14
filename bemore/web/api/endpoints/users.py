from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from bemore.web.api.deps import get_current_active_superuser, SessionDep
from bemore.models import User, UserOut

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
