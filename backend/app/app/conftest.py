import pytest
from httpx import AsyncClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.db.init_db import init_db
from app.web.api.deps import get_db
from app.web.application import get_app


@pytest.fixture(scope="session")
def engine_fixture():
    engine = create_engine(
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@bemore-db/test",
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        init_db(session)
    yield engine


@pytest.fixture(name="session")
def session_fixture(engine_fixture):
    with Session(engine_fixture) as session:
        yield session


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Backend for anyio pytest plugin.

    :return: backend name.
    """
    return "asyncio"


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app = get_app()
    app.dependency_overrides[get_db] = get_session_override

    client = AsyncClient(app=app, base_url="http://localhost:8000")
    yield client
    app.dependency_overrides.clear()
