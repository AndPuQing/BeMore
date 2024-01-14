from typing import List

from fastapi import APIRouter

from bemore.web.api.users.schema import User, UserResponse

router = APIRouter()


@router.post("/", response_model=UserResponse)
async def creat_user(name: str, email: str, topics: List[str] | None) -> UserResponse:
    """
    Creates user.

    :param name: user name.
    :param email: user email.
    :param topics: user topics.
    :returns: created user.
    """
    user = User(name=name, email=email, topics=topics)
    return UserResponse(ID=user.ID)


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str) -> User:
    """
    Gets user.

    :param user_id: user ID.
    :returns: user.
    """
    return User(ID=user_id)


@router.delete("/{user_id}", response_model=None)
async def delete_user(user_id: str) -> None:
    """
    Deletes user.

    :param user_id: user ID.
    """


@router.patch("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    name: str,
    email: str,
    topics: List[str] | None,
) -> User:
    """
    Updates user.

    :param user_id: user ID.
    :param name: user name.
    :param email: user email.
    :param topics: user topics.
    :returns: updated user.
    """


@router.get("s", response_model=List[User])
async def get_users(n: int, cursor: str) -> List[User]:
    """
    Gets users.

    :returns: users.
    """
