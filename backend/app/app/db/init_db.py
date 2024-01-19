from sqlmodel import Session, select

from app.core.config import settings
from app.crud.crud_user import user as crud
from app.models import User, UserCreate  # noqa: F401

# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER),
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create(db=session, obj_in=user_in)