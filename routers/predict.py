import logging
from typing import Annotated

from asyncpg import Pool
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BeforeValidator

from db.pool import get_database_pool
from models.advertisement import AdvertisementRequest
from repositories.advertisements import AdvertisementsRepository
from repositories.moderation import moderation_repository
from services.moderation import ModerationService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_moderation_service() -> ModerationService:
    return ModerationService(moderation_repository)


def validate_item_id(value: object) -> int:
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return int(value)
    raise ValueError("item_id must be a positive integer")


def run_prediction(ad: AdvertisementRequest, service: ModerationService) -> bool:
    try:
        return service.predict(ad)
    except Exception as exc:
        logger.exception("Prediction failed for item_id=%s", ad.item_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed",
        ) from exc


@router.post(
    "/predict",
    response_model=bool,
    responses={
        400: {"description": "Невалидные входные данные"},
        500: {"description": "Ошибка при выполнении предсказания"},
    },
)
async def predict(
    ad: AdvertisementRequest,
    service: ModerationService = Depends(get_moderation_service),
) -> bool:
    return run_prediction(ad, service)


@router.post(
    "/simple_predict",
    response_model=bool,
    responses={
        400: {"description": "Невалидный идентификатор объявления"},
        404: {"description": "Объявление не найдено"},
        500: {"description": "Ошибка при выполнении предсказания"},
    },
)
async def simple_predict(
    item_id: Annotated[
        int, Query(gt=0, le=2_147_483_647), BeforeValidator(validate_item_id)
    ],
    pool: Annotated[Pool, Depends(get_database_pool)],
    service: Annotated[ModerationService, Depends(get_moderation_service)],
) -> bool:
    try:
        async with pool.acquire(timeout=5) as connection:
            ad = await AdvertisementsRepository(connection).get_for_prediction(item_id)
    except Exception as exc:
        logger.exception("Could not load advertisement for item_id=%s", item_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed",
        ) from exc

    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advertisement not found",
        )

    return run_prediction(ad, service)
