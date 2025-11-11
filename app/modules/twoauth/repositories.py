from app.modules.twoauth.models import TwoFactorToken
from core.repositories.BaseRepository import BaseRepository


class TwoFactorTokenRepository(BaseRepository):
    def __init__(self):
        super().__init__(TwoFactorToken)

    def latest_active_for_user(self, user_id: int):
        return (
            self.session.query(TwoFactorToken)
            .filter(TwoFactorToken.user_id == user_id, TwoFactorToken.used.is_(False))
            .order_by(TwoFactorToken.created_at.desc())
            .first()
        )
