from flask import current_app, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService
from app.modules.twoauth.services import TwoAuthService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()
twoauth_service = TwoAuthService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        if current_app.config.get("ENABLE_2FA", False):
            session["pending_signup"] = {
                "email": form.email.data,
                "password": form.password.data,
                "name": form.name.data,
                "surname": form.surname.data,
            }
            twoauth_service.create_and_send_signup_code(form.email.data)
            return redirect(url_for("twoauth.verify"))
        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")
        login_user(user, remember=True)
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        if current_app.config.get("ENABLE_2FA", False):
            user = authentication_service.authenticate(form.email.data, form.password.data)
            if user is not None:
                session["2fa_user_id"] = user.id
                twoauth_service.create_and_send_code(user)
                return redirect(url_for("twoauth.verify"))
            else:
                return render_template("auth/login_form.html", form=form, error="Invalid credentials")
        else:
            if authentication_service.login(form.email.data, form.password.data):
                return redirect(url_for("public.index"))
            return render_template("auth/login_form.html", form=form, error="Invalid credentials")

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))
