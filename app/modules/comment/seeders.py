from datetime import datetime

import pytz

from app import db
from app.modules.comment.models import Comment
from core.seeders.BaseSeeder import BaseSeeder


class CommentSeeder(BaseSeeder):

    def run(self):

        tz = pytz.timezone("Europe/Madrid")

        # Parent/top-level comment (as dict for comparison/creation)
        comment_a = {
            "user_id": 1,
            "dataset_id": 4,
            "content": "prueba 1",
            "created_at": tz.localize(datetime(2025, 10, 12, 9, 0)),
            "visible": True,
        }

        # Reply to the parent comment
        comment_b = {
            "user_id": 2,
            "dataset_id": 4,
            "content": "prueba 2",
            "created_at": tz.localize(datetime(2025, 10, 12, 9, 30)),
            "visible": True,
            "parent_content": "prueba 1",  # helper to find parent
        }

        # Another top-level comment, hidden
        comment_c = {
            "user_id": 1,
            "dataset_id": 4,
            "content": "prueba 3",
            "created_at": tz.localize(datetime(2025, 10, 12, 9, 45)),
            "visible": False,
        }

        to_seed = []

        # create or reuse parent comment_a
        existing_a = Comment.query.filter_by(
            user_id=comment_a["user_id"],
            dataset_id=comment_a["dataset_id"],
            content=comment_a["content"],
            created_at=comment_a["created_at"],
            visible=comment_a["visible"],
        ).first()
        if not existing_a:
            # will be created
            comment_a_obj = Comment(**comment_a)
            to_seed.append(comment_a_obj)
        else:
            # reuse existing for replies resolution
            comment_a_obj = existing_a

        # comment_b: find parent (by content + dataset) and check existence
        parent = Comment.query.filter_by(
            dataset_id=comment_b["dataset_id"], content=comment_b["parent_content"]
        ).first()
        existing_b = Comment.query.filter_by(
            user_id=comment_b["user_id"],
            dataset_id=comment_b["dataset_id"],
            content=comment_b["content"],
            created_at=comment_b["created_at"],
            visible=comment_b["visible"],
        ).first()
        if not existing_b:
            # if parent object exists in DB use it, otherwise will link after seeding
            parent_id = parent.id if parent else None
            cb = Comment(
                user_id=comment_b["user_id"],
                dataset_id=comment_b["dataset_id"],
                content=comment_b["content"],
                created_at=comment_b["created_at"],
                visible=comment_b["visible"],
            )
            if parent_id:
                cb.parent_id = parent_id
            else:
                # mark to link after seeding when parent is created
                cb._link_parent_content = comment_b["parent_content"]
            to_seed.append(cb)

        # comment_c
        existing_c = Comment.query.filter_by(
            user_id=comment_c["user_id"],
            dataset_id=comment_c["dataset_id"],
            content=comment_c["content"],
            created_at=comment_c["created_at"],
            visible=comment_c["visible"],
        ).first()
        if not existing_c:
            to_seed.append(Comment(**comment_c))

        created = []
        if to_seed:
            created = self.seed(to_seed)

        # Fix parent links for newly created replies if parent was created in this run
        for obj in created:
            if hasattr(obj, "_link_parent_content"):
                parent_obj = Comment.query.filter_by(
                    dataset_id=obj.dataset_id, content=getattr(obj, "_link_parent_content")
                ).first()
                if parent_obj:
                    obj.parent_id = parent_obj.id
                    db.session.add(obj)
                    db.session.commit()
