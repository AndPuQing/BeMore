import pytest
from httpx import AsyncClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.web.api.deps import get_db
from app.web.application import get_app


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@bemore-db/{settings.POSTGRES_DB}",
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
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


# @pytest.fixture()
# def fastapi_app() -> FastAPI:
#     """
#     Fixture for creating FastAPI app.

#     :return: fastapi app with mocked dependencies.
#     """
#     application = get_app()
#     return application  # noqa: WPS331


# @pytest.fixture(name="client")
# async def client_fixture(
#     fastapi_app: FastAPI,
# ) -> AsyncGenerator[AsyncClient, None]:
#     """
#     Fixture that creates client for requesting server.

#     :param fastapi_app: the application.
#     :yield: client for the app.
#     """
#     async with AsyncClient(
#         app=fastapi_app, base_url="http://localhost:8000"
#     ) as ac:
#         yield ac
