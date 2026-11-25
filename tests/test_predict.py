from unittest.mock import MagicMock

import pytest

from main import app
from repositories.moderation import ModerationRepository
from routers.predict import get_moderation_service
from services.moderation import ModerationService

FIELDS = [
    "seller_id", "is_verified_seller", "item_id",
    "name", "description", "category", "images_qty",
]


def test_predict_rejects_extra_field(client, payload):
    payload["images_count"] = 2

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    error = response.json()["detail"][0]
    assert error["type"] == "extra_forbidden"
    assert error["loc"] == ["body", "images_count"]


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


# Положительные и отрицательные результаты
@pytest.mark.parametrize(
    "is_verified_seller, images_qty, answer",
    [
        # Подтвержденный продавец - всегда без нарушений
        (True, 0, True),
        (True, 10, True),
        # Неподтвержденный - без нарушений только с фото
        (False, 1, True),
        (False, 10, True),
        # Неподтвержденный без фото - нарушение
        (False, 0, False),
    ],
)
def test_predict(client, payload, is_verified_seller, images_qty, answer):
    payload["is_verified_seller"] = is_verified_seller
    payload["images_qty"] = images_qty

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json() is answer


# Валидация - отсутствует обязательное поле
@pytest.mark.parametrize("field", FIELDS)
def test_missing_field(client, payload, field):
    del payload[field]

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    error = response.json()["detail"][0]
    assert error["type"] == "missing"
    assert error["loc"] == ["body", field]


# Валидация - неверный тип или значение
@pytest.mark.parametrize(
    "field, value, error_type",
    [
        # Неверные типы
        ("seller_id", "1", "int_type"),
        ("item_id", 1.5, "int_type"),
        ("category", "auto", "int_type"),
        ("images_qty", True, "int_type"),
        ("is_verified_seller", "true", "bool_type"),
        ("is_verified_seller", 1, "bool_type"),
        ("name", 123, "string_type"),
        ("description", ["text"], "string_type"),
        # null вместо значения
        ("seller_id", None, "int_type"),
        ("name", None, "string_type"),
        # Граничные значения
        ("seller_id", 0, "greater_than"),
        ("item_id", -1, "greater_than"),
        ("category", -1, "greater_than_equal"),
        ("images_qty", -1, "greater_than_equal"),
        ("name", "", "string_too_short"),
        ("description", "   ", "string_too_short"),
    ],
)
def test_invalid_field(client, payload, field, value, error_type):
    payload[field] = value

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    error = response.json()["detail"][0]
    assert error["type"] == error_type
    assert error["loc"] == ["body", field]


# Валидация - тело запроса целиком некорректно
@pytest.mark.parametrize(
    "request_kwargs",
    [
        {"json": {}},
        {"json": None},
        {"json": [1, 2, 3]},
        {"content": "not a json", "headers": {"Content-Type": "application/json"}},
    ],
)
def test_invalid_body(client, request_kwargs):
    response = client.post("/predict", **request_kwargs)

    assert response.status_code == 400


# Ошибка на уровне бизнес-логики
@pytest.mark.parametrize("exception", [RuntimeError("boom"), ValueError("bad"), KeyError("x")])
def test_service_error(client, payload, exception):
    service = MagicMock(spec=ModerationService)
    service.predict.side_effect = exception
    app.dependency_overrides[get_moderation_service] = lambda: service

    response = client.post("/predict", json=payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "Prediction failed"}
    service.predict.assert_called_once()


# Ошибка на уровне репозитория тоже превращается в 500
def test_repository_error(client, payload):
    repository = MagicMock(spec=ModerationRepository)
    repository.save_result.side_effect = ConnectionError("db is down")
    app.dependency_overrides[get_moderation_service] = lambda: ModerationService(repository)

    response = client.post("/predict", json=payload)

    assert response.status_code == 500


# Сервис сохраняет результат в репозиторий
@pytest.mark.parametrize("is_verified_seller, images_qty, answer", [(True, 0, True), (False, 0, False)])
def test_result_saved(client, payload, is_verified_seller, images_qty, answer):
    repository = ModerationRepository()
    app.dependency_overrides[get_moderation_service] = lambda: ModerationService(repository)
    payload["is_verified_seller"] = is_verified_seller
    payload["images_qty"] = images_qty

    client.post("/predict", json=payload)

    assert repository.get_result(payload["item_id"]) is answer
