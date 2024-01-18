from sqlmodel import SQLModel, Session

from app.db.engine import engine
from app.db.init_db import init_db


def init() -> None:
    with Session(engine) as session:
        SQLModel.metadata.create_all(engine)
        init_db(session)


def main() -> None:
    init()


if __name__ == "__main__":
    main()
