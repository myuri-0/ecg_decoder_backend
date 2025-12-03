import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from main import app


@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    return app


@pytest.fixture
async def async_client(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac
