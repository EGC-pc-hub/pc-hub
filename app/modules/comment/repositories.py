from app.modules.comment.models import Comment
from core.repositories.BaseRepository import BaseRepository


class CommentRepository(BaseRepository):
    def __init__(self):
        super().__init__(Comment)

    def get_comments_by_dataset(self, dataset_id):
        return Comment.query.filter_by(dataset_id=dataset_id).all()

    def get_comments_by_parent(self, parent_id):
        return Comment.query.filter_by(parent_id=parent_id).all()

    def count_comments_by_dataset(self, dataset_id):
        return Comment.query.filter_by(dataset_id=dataset_id).count()

    def update_children_visibility(self, parent_id, visible: bool) -> int:
        """Set the visible flag for all direct replies of parent_id.

        Returns the number of rows updated.
        """

        to_process = [parent_id]
        total_updated = 0
        while to_process:
            children = self.session.query(Comment).filter(Comment.parent_id.in_(to_process)).all()
            if not children:
                break
            ids = [c.id for c in children]
            updated = (
                self.session.query(Comment)
                .filter(Comment.id.in_(ids))
                .update({"visible": visible}, synchronize_session=False)
            )
            total_updated += updated
            to_process = ids

        self.session.commit()
        return total_updated
