import re

import unidecode
from sqlalchemy import any_, or_

from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

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

        # Check if using advanced search
        using_advanced_search = any(
            [
                filter_title,
                filter_author,
                filter_tags,
                filter_publication_type != "any",
                filter_date_from,
                filter_date_to,
            ]
        )

        # Start building the query
        datasets = (
            self.model.query.join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .join(DataSet.feature_models)
            .join(FeatureModel.fm_meta_data)
            .filter(DSMetaData.dataset_doi.isnot(None))
        )

        if using_advanced_search:
            # Advanced search: use individual field filters
            if filter_title:
                datasets = datasets.filter(DSMetaData.title.ilike(f"%{filter_title}%"))

            if filter_author:
                datasets = datasets.filter(Author.name.ilike(f"%{filter_author}%"))

            if filter_tags:
                datasets = datasets.filter(DSMetaData.tags.ilike(f"%{filter_tags}%"))

            if filter_publication_type != "any":
                matching_type = None
                for member in PublicationType:
                    if member.value.lower() == filter_publication_type:
                        matching_type = member
                        break
                if matching_type is not None:
                    datasets = datasets.filter(DSMetaData.publication_type == matching_type.name)

            if filter_date_from:
                from datetime import datetime

                date_from = datetime.strptime(filter_date_from, "%Y-%m-%d")
                datasets = datasets.filter(self.model.created_at >= date_from)

            if filter_date_to:
                from datetime import datetime

                date_to = datetime.strptime(filter_date_to, "%Y-%m-%d")
                datasets = datasets.filter(self.model.created_at <= date_to)
        else:
            # Regular search: use general query across multiple fields
            if query:
                normalized_query = unidecode.unidecode(query).lower()
                cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

                filters = []
                for word in cleaned_query.split():
                    filters.append(DSMetaData.title.ilike(f"%{word}%"))
                    filters.append(DSMetaData.description.ilike(f"%{word}%"))
                    filters.append(Author.name.ilike(f"%{word}%"))
                    filters.append(Author.affiliation.ilike(f"%{word}%"))
                    filters.append(Author.orcid.ilike(f"%{word}%"))
                    filters.append(FMMetaData.uvl_filename.ilike(f"%{word}%"))
                    filters.append(FMMetaData.title.ilike(f"%{word}%"))
                    filters.append(FMMetaData.description.ilike(f"%{word}%"))
                    filters.append(FMMetaData.publication_doi.ilike(f"%{word}%"))
                    filters.append(FMMetaData.tags.ilike(f"%{word}%"))
                    filters.append(DSMetaData.tags.ilike(f"%{word}%"))

                datasets = datasets.filter(or_(*filters))

            # Apply publication_type filter for regular search if not using advanced
            if publication_type != "any":
                matching_type = None
                for member in PublicationType:
                    if member.value.lower() == publication_type:
                        matching_type = member
                        break

                if matching_type is not None:
                    datasets = datasets.filter(DSMetaData.publication_type == matching_type.name)

        if tags:
            datasets = datasets.filter(DSMetaData.tags.ilike(any_(f"%{tag}%" for tag in tags)))

        # Order by created_at
        if sorting == "oldest":
            datasets = datasets.order_by(self.model.created_at.asc())
        else:
            datasets = datasets.order_by(self.model.created_at.desc())

        return datasets.all()
