from sqlmodel import Session

from bemore.db.engine import engine
from bemore.db.init_db import init_db


def init() -> None:
    with Session(engine) as session:
        init_db(session)


def main() -> None:
    init()


if __name__ == "__main__":
    main()
