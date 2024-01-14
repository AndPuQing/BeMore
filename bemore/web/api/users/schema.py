import uuid
from typing import List
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    """
    User model.

    This model is used to represent user.
    """

    ID: UUID = uuid.uuid4()
    name: str
    email: str
    is_active: bool = True
    is_superuser: bool = False
    topics: List[str] | None = None


class UserResponse(BaseModel):
    """
    User response model.

    This model is used to represent user response.
    """

    ID: UUID
