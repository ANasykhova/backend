import logging

from fastapi import APIRouter, Depends, HTTPException, status

from models.advertisement import AdvertisementRequest
from repositories.moderation import moderation_repository
from services.moderation import ModerationService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_moderation_service() -> ModerationService:
    return ModerationService(moderation_repository)


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
    try:
        return service.predict(ad)
    except Exception:
        logger.exception("Prediction failed for item_id=%s", ad.item_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed",
        )
