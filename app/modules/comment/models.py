from datetime import datetime

import pytz

from app import db


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # many-to-one: do NOT cascade from Comment -> User (would delete/update users)
    user = db.relationship("User", lazy=True)

    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"), nullable=False)

    # many-to-one: dataset owns comments via backref on DataSet; avoid cascade here
    dataset = db.relationship("DataSet", backref="comments", lazy=True)

    parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)
    # parent/children relationship: avoid cascading destructive ops from child -> parent
    # parent/children relationship: replies are owned by the parent comment
    # deleting a parent should delete its replies as well (delete-orphan)
    parent = db.relationship(
        "Comment",
        remote_side=[id],
        backref=db.backref("replies", cascade="all, delete-orphan"),
        lazy=True,
    )
    content = db.Column(db.String(256), nullable=False)

    # Visibility flag: dataset owners can hide/unhide comments
    visible = db.Column(db.Boolean, nullable=False, default=True)

    content = db.Column(db.String(256), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.timezone("Europe/Madrid")))

    def __repr__(self):
        return (
            f"Comment<{self.id}, User={self.user.profile.name}, "
            f"Dataset={self.dataset.name}>, CreatedAt={self.created_at}>"
        )
