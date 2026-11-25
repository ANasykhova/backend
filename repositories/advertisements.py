from asyncpg import Connection

from models.advertisement import AdvertisementRequest


class AdvertisementsRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def create(
        self,
        *,
        seller_id: int,
        name: str,
        description: str,
        category: int,
        images_qty: int,
    ) -> int:
        return await self._connection.fetchval(
            """
            INSERT INTO advertisements (seller_id, name, description, category, images_qty)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            seller_id,
            name,
            description,
            category,
            images_qty,
        )

    async def get_for_prediction(self, item_id: int) -> AdvertisementRequest | None:
        row = await self._connection.fetchrow(
            """
            SELECT a.id AS item_id, a.seller_id, u.is_verified AS is_verified_seller,
                   a.name, a.description, a.category, a.images_qty
            FROM advertisements AS a
            JOIN users AS u ON u.id = a.seller_id
            WHERE a.id = $1
            """,
            item_id,
        )
        return AdvertisementRequest.model_validate(dict(row)) if row is not None else None
