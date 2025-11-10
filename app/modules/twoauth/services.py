import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app, session
from flask_mail import Message

from app import db, mail
from app.modules.twoauth.models import TwoFactorToken
from app.modules.twoauth.repositories import TwoFactorTokenRepository


class TwoAuthService:
    def __init__(self):
        self.repo = TwoFactorTokenRepository()

    def _generate_code(self) -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    def _send_email(self, to_email: str, subject: str, body: str, sender_cfg: str | None, from_name: str):
        msg = Message(subject=subject, recipients=[to_email], sender=sender_cfg)
        msg.body = body
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Error enviando email (SMTP): {e}")

    def create_and_send_code(self, user):
        # Invalidate previous unused tokens for the user to prevent reuse
        last = self.repo.latest_active_for_user(user.id)
        if last is not None:
            last.used = True
            db.session.add(last)

        code = self._generate_code()
        ttl = int(current_app.config.get("TWOAUTH_TTL_MINUTES", 10))
        token = TwoFactorToken(user_id=user.id, code=code, ttl_minutes=ttl)
        db.session.add(token)
        db.session.commit()

        subject = current_app.config.get("TWOAUTH_EMAIL_SUBJECT", "Tu código de verificación (PC Hub)")
        sender_cfg = current_app.config.get("MAIL_DEFAULT_SENDER")
        from_name = current_app.config.get("MAIL_FROM_NAME") or "PC Hub"
        body = (
            f"Hola,\n\nTu código de verificación es: {code}\n\n"
            f"Este código caduca en {ttl} minutos. Si no has solicitado este código, ignora este mensaje.\n\n"
            f"PC Hub"
        )

        self._send_email(user.email, subject, body, sender_cfg, from_name)
        return token

    def create_and_send_signup_code(self, email: str):
        code = self._generate_code()
        ttl = int(current_app.config.get("TWOAUTH_TTL_MINUTES", 10))
        # Persist in session
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl)
        session["pending_signup_2fa"] = {
            "email": email,
            "expires_at": expires_at.isoformat(),
        }
        session["pending_signup_2fa_code"] = code
        session["pending_signup_2fa_last_sent"] = datetime.now(timezone.utc).isoformat()

        # Build email
        subject = current_app.config.get("TWOAUTH_EMAIL_SUBJECT", "Tu código de verificación (PC Hub)")
        sender_cfg = current_app.config.get("MAIL_DEFAULT_SENDER")
        from_name = current_app.config.get("MAIL_FROM_NAME") or "PC Hub"
        body = (
            f"Hola,\n\nTu código de verificación es: {code}\n\n"
            f"Este código caduca en {ttl} minutos. Si no has solicitado este código, ignora este mensaje.\n\n"
            f"PC Hub"
        )
        # Send
        self._send_email(email, subject, body, sender_cfg, from_name)
        return {"expires_at": expires_at}

    def can_resend_signup(self):
        cooldown = int(current_app.config.get("TWOAUTH_RESEND_COOLDOWN_SEC", 30))
        last_sent = session.get("pending_signup_2fa_last_sent")
        if not last_sent:
            return True
        try:
            last_dt = datetime.fromisoformat(last_sent)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except Exception:
            return True
        return (datetime.now(timezone.utc) - last_dt) > timedelta(seconds=cooldown)

    def verify_code(self, user, code: str):
        token = self.repo.latest_active_for_user(user.id)
        if not token:
            return False
        if token.used:
            return False
        expires = token.expires_at
        if expires is None:
            return False
        if expires.tzinfo is None:
            from datetime import datetime as _dt

            if _dt.utcnow() > expires:
                return False
        else:
            if datetime.now(timezone.utc) > expires:
                return False
        if token.code != code:
            return False
        token.used = True
        db.session.add(token)
        db.session.commit()
        return True

    def can_resend(self, user):
        cooldown = int(current_app.config.get("TWOAUTH_RESEND_COOLDOWN_SEC", 30))
        last = self.repo.latest_active_for_user(user.id)
        if not last:
            return True
        now_utc = datetime.now(timezone.utc)
        created = last.created_at
        if created is None:
            return True
        if created.tzinfo is None:
            created_utc = created.replace(tzinfo=timezone.utc)
        else:
            created_utc = created.astimezone(timezone.utc)
        return (now_utc - created_utc) > timedelta(seconds=cooldown)
