import os
import secrets
from urllib.parse import urlencode

import requests
from flask import current_app, jsonify, redirect, render_template, request, session, url_for
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


@auth_bp.route("/github/status", methods=["GET"])
def github_status():
    connected = bool(session.get("github_token"))
    return jsonify({"connected": connected}), 200


@auth_bp.route("/github/login", methods=["GET"])
def github_login():
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        return "GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.", 500

    state = secrets.token_urlsafe(16)
    session["github_oauth_state"] = state
    next_param = request.args.get("next")
    if next_param:
        session["github_oauth_next"] = next_param

    redirect_uri = url_for("auth.github_callback", _external=True)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        # Solo pedimos acceso a repos para poder crear repos privados en la cuenta del usuario
        "scope": "repo",
        "state": state,
    }
    url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    # Usamos una pequeña página HTML para realizar la redirección en el cliente (en lugar de
    # devolver un redirect/302 desde el servidor).
    # Motivos:
    # - Evitar problemas con proxies inversos o balanceadores que a veces alteran o ignoran la
    #   cabecera Location de respuestas 302.
    # - Asegurar la redirección incluso si el proxy reescribe dominios/rutas o hay mezcla de
    #   HTTP/HTTPS.
    # - Mantener un comportamiento consistente en navegadores y evitar sorpresas con CORS al
    #   seguir la redirección.
    # Detalles de implementación:
    # - Incluimos un meta refresh y window.location.replace hacia la URL de autorización de GitHub.
    # - Si JavaScript está deshabilitado, el enlace en el cuerpo permite continuar manualmente.
    # - No se exponen secretos: el parámetro state y el next se guardan en sesión; aquí solo
    #   generamos la URL pública de GitHub.
    # - Esta ruta devuelve HTML intencionadamente en lugar de usar redirect() para mayor
    #   compatibilidad con entornos con proxy.
    html = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"utf-8\">
        <meta http-equiv=\"refresh\" content=\"0;url={url}\">
        <title>Redirecting to GitHub…</title>
    </head>
    <body>
        <p>Redirecting to GitHub… If you are not redirected automatically, <a href=\"{url}\">click here</a>.</p>
        <script>window.location.replace({url!r});</script>
    </body>
    </html>
    """
    return html


@auth_bp.route("/github/callback", methods=["GET"])
def github_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    expected_state = session.get("github_oauth_state")
    if not code or not state or state != expected_state:
        return "Invalid OAuth state.", 400

    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    token_url = "https://github.com/login/oauth/access_token"

    headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": url_for("auth.github_callback", _external=True),
        "state": state,
    }
    try:
        resp = requests.post(token_url, headers=headers, data=data, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        access_token = payload.get("access_token")
        if not access_token:
            return f"GitHub OAuth error: {payload}", 400
        session["github_token"] = access_token
        # Limpieza de estado OAuth en sesión para evitar fugas
        session.pop("github_oauth_state", None)
        next_url = session.pop("github_oauth_next", url_for("public.index"))
        return redirect(next_url)
    except Exception as exc:
        return f"OAuth exchange failed: {exc}", 400
