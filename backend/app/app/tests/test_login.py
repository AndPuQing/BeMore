import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status


@pytest.mark.anyio
async def test_login(client: AsyncClient, fastapi_app: FastAPI) -> None:
    """
    Checks the health endpoint.

    :param client: client for the app.
    :param fastapi_app: current FastAPI application.
    """
    response = await client.post(
        "/api/login/access-token",
        data={"username": "admin@localhost.com", "password": "admin"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.anyio
async def test_token(client: AsyncClient, fastapi_app: FastAPI) -> None:
    """
    Checks the health endpoint.

    :param client: client for the app.
    :param fastapi_app: current FastAPI application.
    """

    response = await client.post(
        "/api/login/access-token",
        data={"username": "admin@localhost.com", "password": "admin"},
    )

    token = response.json()["access_token"]

    response = await client.post(
        "/api/login/test-token",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "admin@localhost.com"
