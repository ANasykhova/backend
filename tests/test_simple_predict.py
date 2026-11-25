from unittest.mock import AsyncMock

import pytest
from asyncpg import ForeignKeyViolationError

from repositories.advertisements import AdvertisementsRepository


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stored_advertisement, expected",
    [((True, 0), True), ((False, 1), True), ((False, 0), False)],
    indirect=["stored_advertisement"],
)
async def test_simple_predict(database_client, stored_advertisement, expected):
    response = await database_client.post(
        "/simple_predict", params={"item_id": stored_advertisement["item_id"]}
    )

    assert response.status_code == 200
    assert response.json() is expected


@pytest.mark.asyncio
async def test_advertisement_not_found(database_client, connection, stored_advertisement):
    item_id = stored_advertisement["item_id"]
    await connection.execute("DELETE FROM advertisements WHERE id = $1", item_id)

    response = await database_client.post("/simple_predict", params={"item_id": item_id})

    assert response.status_code == 404
    assert response.json() == {"detail": "Advertisement not found"}


@pytest.mark.parametrize(
    "item_id",
    [None, "", " ", "abc", "true", "0", "-1", "1.0", "1.5", "2147483648"],
)
def test_invalid_item_id(client, item_id):
    params = {} if item_id is None else {"item_id": item_id}
    response = client.post("/simple_predict", params=params)

    assert response.status_code == 400
    assert response.json()["detail"][0]["loc"] == ["query", "item_id"]


@pytest.mark.asyncio
async def test_database_error(database_client, stored_advertisement, monkeypatch):
    load_advertisement = AsyncMock(side_effect=ConnectionError("db is down"))
    monkeypatch.setattr(
        AdvertisementsRepository, "get_for_prediction", load_advertisement
    )
    item_id = stored_advertisement["item_id"]

    response = await database_client.post("/simple_predict", params={"item_id": item_id})

    assert response.status_code == 500
    assert response.json() == {"detail": "Prediction failed"}
    load_advertisement.assert_awaited_once_with(item_id)


@pytest.mark.asyncio
async def test_repositories_create_user_and_advertisement(
    connection, seller_data, stored_advertisement
):
    seller_id = stored_advertisement["seller_id"]
    item_id = stored_advertisement["item_id"]
    assert seller_id > 0
    assert item_id > 0

    seller = await connection.fetchrow(
        "SELECT first_name, last_name, is_verified, violations_qty FROM users WHERE id = $1",
        seller_id,
    )
    assert dict(seller) == {
        **seller_data,
        "is_verified": stored_advertisement["is_verified_seller"],
    }

    advertisement = await AdvertisementsRepository(connection).get_for_prediction(item_id)
    assert advertisement.model_dump() == stored_advertisement

    with pytest.raises(ForeignKeyViolationError):
        await connection.execute("DELETE FROM users WHERE id = $1", seller_id)
