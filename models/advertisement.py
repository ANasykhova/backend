from pydantic import BaseModel, ConfigDict, Field


class AdvertisementRequest(BaseModel):
    # strict - без неявных приведений типов ("1" -> 1, "true" -> True)
    model_config = ConfigDict(strict=True, str_strip_whitespace=True)

    seller_id: int = Field(gt=0, description="ID продавца")
    is_verified_seller: bool = Field(description="Подтвержден ли продавец")
    item_id: int = Field(gt=0, description="ID объявления")
    name: str = Field(min_length=1, max_length=255, description="Название")
    description: str = Field(min_length=1, max_length=5000, description="Описание")
    category: int = Field(ge=0, description="ID категории")
    images_qty: int = Field(ge=0, description="Количество изображений")
