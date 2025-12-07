from app.modules.explore.repositories import ExploreRepository
from core.services.BaseService import BaseService


class ExploreService(BaseService):
    def __init__(self):
        super().__init__(ExploreRepository())

    def filter(
        self,
        query="",
        sorting="newest",
        publication_type="any",
        tags=[],
        filter_title="",
        filter_author="",
        filter_tags="",
        filter_publication_type="any",
        filter_date_from="",
        filter_date_to="",
        **kwargs,
    ):
        return self.repository.filter(
            query,
            sorting,
            publication_type,
            tags,
            filter_title,
            filter_author,
            filter_tags,
            filter_publication_type,
            filter_date_from,
            filter_date_to,
            **kwargs,
        )
