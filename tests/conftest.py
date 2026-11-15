import pytest
from fastapi.testclient import TestClient

from main import app


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
