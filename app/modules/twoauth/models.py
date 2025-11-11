from datetime import datetime, timedelta, timezone

from app import db


class TwoFactorToken(db.Model):
    __tablename__ = "two_factor_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, user_id: int, code: str, ttl_minutes: int = 10):
        self.user_id = user_id
        self.code = code
        now = datetime.now(timezone.utc)
        self.created_at = now
        self.expires_at = now + timedelta(minutes=ttl_minutes)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def mark_used(self):
        self.used = True
        db.session.add(self)
        db.session.commit()
