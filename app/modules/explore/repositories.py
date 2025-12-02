import re
from datetime import datetime
from typing import List, Optional

import unidecode
from sqlalchemy import any_, asc, desc, func, or_

from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from core.repositories.BaseRepository import BaseRepository

class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter(self, query="", sorting="newest", publication_type="any", tags=[], **kwargs):
        # Normalize and remove unwanted characters
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

        datasets = (
            self.model.query.join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .join(DataSet.feature_models)
            .join(FeatureModel.fm_meta_data)
            .filter(or_(*filters))
            .filter(DSMetaData.dataset_doi.isnot(None))  # Exclude datasets with empty dataset_doi
        )

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

    # NUEVOS MÉTODOS PARA BÚSQUEDA AVANZADA
    def advanced_filter(
        self,
        query: str = "",
        authors: str = "",
        tags: str = "",
        publication_types: List[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "created_at_desc",
        **kwargs,
    ):
        """
        Búsqueda avanzada con múltiples filtros
        """
        # Base query
        datasets = self.model.query.join(DataSet.ds_meta_data).filter(DSMetaData.dataset_doi.isnot(None))

        has_author_join = False

        # Filtro por texto general
        if query:
            normalized_query = unidecode.unidecode(query).lower()
            cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

            text_filters = []
            for word in cleaned_query.split():
                text_filters.extend([DSMetaData.title.ilike(f"%{word}%"), DSMetaData.description.ilike(f"%{word}%")])

            if text_filters:
                datasets = datasets.filter(or_(*text_filters))

        # Filtro por autores
        if authors and authors.strip():
            authors_list = [author.strip() for author in authors.split(",") if author.strip()]

            # Crear subquery para datasets que tienen los autores buscados
            author_subquery = (
                self.model.query.join(DataSet.ds_meta_data)
                .join(DSMetaData.authors)
                .filter(DSMetaData.dataset_doi.isnot(None))
            )

            # Aplicar filtros de autores
            author_filters = []
            for author in authors_list:
                author_filters.extend([Author.name.ilike(f"%{author}%"), Author.orcid.ilike(f"%{author}%")])

            if author_filters:
                author_subquery = author_subquery.filter(or_(*author_filters))
                # Obtener IDs de datasets que coinciden
                matching_dataset_ids = [ds.id for ds in author_subquery.all()]

                # Filtrar la consulta principal por estos IDs
                if matching_dataset_ids:
                    datasets = datasets.filter(DataSet.id.in_(matching_dataset_ids))
                    has_author_join = True
                else:
                    # Si no hay coincidencias, devolver consulta vacía
                    datasets = datasets.filter(DataSet.id == -1)  # Impossible condition

        # Filtro por tags
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]
            tag_filters = []

            for tag in tags_list:
                tag_filters.append(DSMetaData.tags.ilike(f"%{tag}%"))

            if tag_filters:
                datasets = datasets.filter(or_(*tag_filters))

        # Filtro por tipos de publicación
        if publication_types:
            pub_type_enums = []
            for pt in publication_types:
                for member in PublicationType:
                    if member.value == pt:
                        pub_type_enums.append(member)
                        break

            if pub_type_enums:
                datasets = datasets.filter(DSMetaData.publication_type.in_(pub_type_enums))

        # Filtro por fechas
        if date_from:
            datasets = datasets.filter(DataSet.created_at >= date_from)

        if date_to:
            datasets = datasets.filter(DataSet.created_at <= date_to)

        # Ordenamiento
        if sort_by == "created_at_desc":
            datasets = datasets.order_by(desc(DataSet.created_at))
        elif sort_by == "created_at_asc":
            datasets = datasets.order_by(asc(DataSet.created_at))
        elif sort_by == "download_count_desc":
            datasets = datasets.order_by(desc(DataSet.download_count))
        elif sort_by == "title_asc":
            datasets = datasets.order_by(asc(DSMetaData.title))
        elif sort_by == "title_desc":
            datasets = datasets.order_by(desc(DSMetaData.title))
        else:
            datasets = datasets.order_by(desc(DataSet.created_at))

        # Execute query and get results
        result = datasets.distinct().all()

        return result

    def get_available_tags(self) -> List[str]:
        """
        Obtiene todos los tags únicos disponibles en los datasets
        """
        tags_query = (
            self.model.query.join(DataSet.ds_meta_data)
            .with_entities(DSMetaData.tags)
            .filter(DSMetaData.tags.isnot(None))
            .filter(DSMetaData.dataset_doi.isnot(None))
            .all()
        )

        all_tags = set()
        for tag_row in tags_query:
            if tag_row[0]:
                tags = [tag.strip() for tag in tag_row[0].split(",")]
                all_tags.update(tags)

        return sorted(list(all_tags))

    def get_author_suggestions(self, term: str, limit: int = 10) -> List[Author]:
        """
        Obtiene sugerencias de autores basadas en el término de búsqueda
        """
        return (
            Author.query.join(Author.ds_meta_data)
            .join(DSMetaData.data_set)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .filter(or_(Author.name.ilike(f"%{term}%"), Author.orcid.ilike(f"%{term}%")))
            .distinct()
            .limit(limit)
            .all()
        )

    def get_publication_type_stats(self) -> dict:
        """
        Obtiene estadísticas de tipos de publicación
        """
        stats = (
            self.model.query.join(DataSet.ds_meta_data)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .with_entities(DSMetaData.publication_type, func.count(DataSet.id))
            .group_by(DSMetaData.publication_type)
            .all()
        )

        return {pub_type.value: count for pub_type, count in stats}
