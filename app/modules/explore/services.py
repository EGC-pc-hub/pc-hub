from app.modules.explore.repositories import ExploreRepository
from core.services.BaseService import BaseService

class ExploreService(BaseService):
    def __init__(self):
        super().__init__(ExploreRepository())

    def filter(self, query="", sorting="newest", publication_type="any", tags=[], **kwargs):
        return self.repository.filter(query, sorting, publication_type, tags, **kwargs)

    def advanced_search(self, **search_params):
        """
        Servicio para búsqueda avanzada
        """
        return self.repository.advanced_filter(**search_params)

    def get_available_tags(self):
        """
        Obtiene todos los tags disponibles
        """
        return self.repository.get_available_tags()

    def get_author_suggestions(self, term):
        """
        Obtiene sugerencias de autores
        """
        return self.repository.get_author_suggestions(term)

    def get_publication_type_stats(self):
        """
        Obtiene estadísticas de tipos de publicación
        """
        return self.repository.get_publication_type_stats()
