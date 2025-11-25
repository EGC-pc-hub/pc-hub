from app.modules.comment.repositories import CommentRepository
from core.services.BaseService import BaseService


class CommentService(BaseService):
    def __init__(self):
        super().__init__(CommentRepository())

    def get_comments_by_dataset(self, dataset_id):
        return self.repository.get_comments_by_dataset(dataset_id)

    def get_comments_by_parent(self, parent_id):
        return self.repository.get_comments_by_parent(parent_id)

    def count_comments_by_dataset(self, dataset_id):
        return self.repository.count_comments_by_dataset(dataset_id)

    def update_children_visibility(self, parent_id, visible: bool) -> int:
        return self.repository.update_children_visibility(parent_id, visible)
