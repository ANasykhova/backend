class ModerationRepository:
    """Хранилище результатов модерации"""

    def __init__(self) -> None:
        self._results: dict[int, bool] = {}

    def save_result(self, item_id: int, is_approved: bool) -> None:
        self._results[item_id] = is_approved

    def get_result(self, item_id: int) -> bool | None:
        return self._results.get(item_id)


moderation_repository = ModerationRepository()
