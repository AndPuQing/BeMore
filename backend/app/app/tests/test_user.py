import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status


@pytest.mark.anyio
async def test_create_user(client: AsyncClient, fastapi_app: FastAPI) -> None:
    """
    Checks the health endpoint.

    :param client: client for the app.
    :param fastapi_app: current FastAPI application.
    """
    response = await client.get(
        "/api/users/", headers={"skip": "0", "limit": "10"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
