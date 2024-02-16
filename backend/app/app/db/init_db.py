import logging

from sqlmodel import Session, SQLModel, select

from app.core.config import settings
from app.db.engine import engine
from app.models import User, UserCreate  # noqa: F401


def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER),
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = User.create(session, user_in)
        logging.debug(f"Superuser {settings.FIRST_SUPERUSER} created")


async def init():
    with Session(engine) as session:
        SQLModel.metadata.create_all(engine)
        init_db(session)
