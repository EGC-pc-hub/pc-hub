from app.modules.comment.models import Comment
from core.repositories.BaseRepository import BaseRepository


class CommentRepository(BaseRepository):
    def __init__(self):
        super().__init__(Comment)
