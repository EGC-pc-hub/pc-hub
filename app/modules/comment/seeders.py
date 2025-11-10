from core.seeders.BaseSeeder import BaseSeeder
from datetime import datetime
import pytz

from app.modules.comment.models import Comment


class CommentSeeder(BaseSeeder):

    def run(self):
       
        tz = pytz.timezone("Europe/Madrid")

        # Parent/top-level comment
        comment_a = Comment(
            user_id=1,
            dataset_id=4,
            content="prueba 1",
            created_at=tz.localize(datetime(2025, 10, 12, 9, 0)),
            visible=True,
        )

        # Reply to the parent comment
        comment_b = Comment(
            user_id=2,
            dataset_id=4,
            content="prueba 2",
            created_at=tz.localize(datetime(2025, 10, 12, 9, 30)),
            visible=True,
            parent=comment_a,
        )

        # Another top-level comment, hidden
        comment_c = Comment(
            user_id=1,
            dataset_id=4,
            content="prueba 3",
            created_at=tz.localize(datetime(2025, 10, 12, 9, 45)),
            visible=False,
        )

        data = [comment_a, comment_b, comment_c]

        self.seed(data)
