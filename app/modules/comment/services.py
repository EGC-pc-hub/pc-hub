from app.modules.comment.repositories import CommentRepository
from core.services.BaseService import BaseService


class CommentService(BaseService):
    def __init__(self):
        super().__init__(CommentRepository())
