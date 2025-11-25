from app import db


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f"Comment<{self.id}>"
