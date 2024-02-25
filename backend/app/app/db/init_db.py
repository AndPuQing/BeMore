import csv
import logging
import random

from sqlmodel import Session, SQLModel, select

from app.core.config import settings
from app.db.engine import engine
from app.models import (
    FeedBack,
    Item,
    User,
    UserCreate,
)


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

        # cold start for the recommender
        users = [f"{i}@bemore.com" for i in range(1, 11)]
        for email in users:
            user_in = UserCreate(
                email=email,
                password="123456",
                is_active=False,
            )
            user = User.create(session, user_in)
            logging.debug(f"User {user.email} created")  # type: ignore

        with open("/app/app/db/item.csv", "r") as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if i == 0:
                    continue
                item_in = Item(
                    title=row[0],
                    abstract=row[1],
                    url=row[4],
                    from_source=row[5],
                )
                item = Item.create(session, item_in)

        for user_id in range(1, 11):
            for i in range(1, 20):
                feedback = FeedBack(
                    user_id=user_id,
                    item_id=random.randint(1, 100),
                    feedback_type=1.0,
                )
                session.add(feedback)
        session.commit()


async def init():
    with Session(engine) as session:
        SQLModel.metadata.create_all(engine)
        init_db(session)
