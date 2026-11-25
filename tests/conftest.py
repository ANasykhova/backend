import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from db.pool import DEFAULT_DATABASE_URL
from main import app
from repositories.advertisements import AdvertisementsRepository
from repositories.users import UsersRepository


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def payload():
    return {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 42,
        "name": "Велосипед",
        "description": "Горный, почти новый",
        "category": 3,
        "images_qty": 2,
    }


@pytest_asyncio.fixture
async def database_client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.getenv("TEST_DATABASE_URL", DEFAULT_DATABASE_URL))
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as test_client:
            yield test_client


@pytest_asyncio.fixture
async def connection(database_client):
    async with app.state.database_pool.acquire() as conn:
        yield conn


@pytest.fixture
def seller_data():
    return {"first_name": "Анна", "last_name": "Иванова", "violations_qty": 2}


@pytest_asyncio.fixture
async def stored_advertisement(request, connection, payload, seller_data):
    is_verified, images_qty = getattr(request, "param", (True, 0))
    users = UsersRepository(connection)
    advertisements = AdvertisementsRepository(connection)
    async with connection.transaction():
        seller_id = await users.create(**seller_data, is_verified=is_verified)
        item_id = await advertisements.create(
            seller_id=seller_id,
            name=payload["name"],
            description=payload["description"],
            category=payload["category"],
            images_qty=images_qty,
        )

    payload.update(
        seller_id=seller_id,
        item_id=item_id,
        is_verified_seller=is_verified,
        images_qty=images_qty,
    )
    try:
        yield payload
    finally:
        async with connection.transaction():
            await connection.execute("DELETE FROM advertisements WHERE id = $1", item_id)
            await connection.execute("DELETE FROM users WHERE id = $1", seller_id)
