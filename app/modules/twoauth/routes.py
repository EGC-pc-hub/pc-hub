from datetime import datetime as _dt
from datetime import timezone as _tz

from flask import redirect, render_template, request, session, url_for
from flask_login import current_user

from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService
from app.modules.twoauth import twoauth_bp
from app.modules.twoauth.forms import TwoAuthVerifyForm
from app.modules.twoauth.services import TwoAuthService

service = TwoAuthService()
user_repo = UserRepository()
profile_service = UserProfileService()
auth_service = AuthenticationService()


@twoauth_bp.route("/2auth", methods=["GET", "POST"])
@twoauth_bp.route("/2auth/verify", methods=["GET", "POST"], endpoint="verify")
def verify():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    user_id = session.get("2fa_user_id")
    pending_signup = session.get("pending_signup")
    user = None

    if user_id:
        user = user_repo.get_by_id(user_id)
        if not user:
            session.pop("2fa_user_id", None)
            return redirect(url_for("auth.login"))
    elif not pending_signup:
        return redirect(url_for("auth.login"))

    form = TwoAuthVerifyForm()
    if request.method == "POST" and form.validate_on_submit():
        code = form.code.data
        from flask_login import login_user

        if user is not None:
            if service.verify_code(user, code):
                login_user(user, remember=True)
                session.pop("2fa_user_id", None)
                return redirect(url_for("public.index"))
            else:
                return render_template("twoauth/verify_form.html", form=form, error="Código inválido o caducado")
        else:
            meta = session.get("pending_signup_2fa")
            code_stored = session.get("pending_signup_2fa_code")
            if not meta or not code_stored:
                return redirect(url_for("auth.login"))
            try:
                exp = _dt.fromisoformat(meta.get("expires_at"))
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=_tz.utc)
            except Exception:
                exp = None
            if not exp or _dt.now(_tz.utc) > exp:
                return render_template("twoauth/verify_form.html", form=form, error="Código inválido o caducado")
            if code != code_stored:
                return render_template("twoauth/verify_form.html", form=form, error="Código inválido o caducado")

            pdata = session.get("pending_signup")
            if not pdata:
                return redirect(url_for("auth.login"))
            try:
                user = auth_service.create_with_profile(**pdata)
            except Exception as exc:
                return render_template("twoauth/verify_form.html", form=form, error=f"Error creando cuenta: {exc}")

            login_user(user, remember=True)
            session.pop("pending_signup", None)
            session.pop("pending_signup_2fa", None)
            session.pop("pending_signup_2fa_code", None)
            session.pop("pending_signup_2fa_last_sent", None)
            return redirect(url_for("public.index"))

    return render_template("twoauth/verify_form.html", form=form)


@twoauth_bp.route("/2auth/resend", methods=["GET"])
def resend():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    user_id = session.get("2fa_user_id")
    if user_id:
        user = user_repo.get_by_id(user_id)
        if not user:
            session.pop("2fa_user_id", None)
            return redirect(url_for("auth.login"))
        if not service.can_resend(user):
            return redirect(url_for("twoauth.verify"))
        service.create_and_send_code(user)
        return redirect(url_for("twoauth.verify"))

    pending = session.get("pending_signup")
    if not pending:
        return redirect(url_for("auth.login"))
    if not service.can_resend_signup():
        return redirect(url_for("twoauth.verify"))
    service.create_and_send_signup_code(pending.get("email"))
    return redirect(url_for("twoauth.verify"))
