from models.advertisement import AdvertisementRequest
from repositories.moderation import ModerationRepository


class ModerationService:
    def __init__(self, repository: ModerationRepository) -> None:
        self._repository = repository

    def predict(self, ad: AdvertisementRequest) -> bool:
        """True - нарушений нет, False - есть нарушения

        Подтвержденный продавец публикует без нарушений,
        неподтвержденный - только при наличии изображений
        """
        is_approved = ad.is_verified_seller or ad.images_qty > 0
        self._repository.save_result(ad.item_id, is_approved)
        return is_approved
