import pytest
from unittest.mock import MagicMock

from flask import session

from app import db
from app.modules.auth.models import User
from app.modules.twoauth.models import TwoFactorToken
from app.modules.twoauth.services import TwoAuthService
from datetime import timedelta, timezone, datetime


@pytest.fixture()
def mock_send(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("app.modules.twoauth.services.mail.send", mock)
    return mock


@pytest.fixture(scope="module")
def test_client(test_client):
    with test_client.application.app_context():
        user = User(email="twoauth@example.com", password="test1234")
        db.session.add(user)
        db.session.commit()

        TwoFactorToken.query.delete()
        db.session.commit()

    yield test_client


def test_verify_form_shown_when_user_pending_2fa(test_client):
    with test_client.session_transaction() as sess:
        user = User.query.filter_by(email="twoauth@example.com").first()
        sess["2fa_user_id"] = user.id
    resp = test_client.get("/2auth")
    assert resp.status_code == 200
    assert b"Verificar" in resp.data, "No se ha podidio verificar"


def test_create_and_send_code_generates_token_and_sends_email(mock_send, test_client):
    with test_client.application.app_context():
        user = User.query.filter_by(email="twoauth@example.com").first()
        svc = TwoAuthService()

        token = svc.create_and_send_code(user)

        assert token.id
        assert token.user_id == user.id, "El token no pertenece al usuario"
        assert len(token.code) == 6 and token.code.isdigit(), "El formato del token no es correcto"
        assert token.used is False, "El token ya ha sido usado"

        assert mock_send.called


def test_verify_code_succesful(test_client):
    with test_client.application.app_context():
        user = User.query.filter_by(email="twoauth@example.com").first()
        svc = TwoAuthService()
        token = svc.create_and_send_code(user)

        assert svc.verify_code(user, token.code) is True
        assert TwoFactorToken.query.get(token.id).used is True


def test_verify_code_wrong_code_fails(test_client):
    with test_client.application.app_context():
        user = User.query.filter_by(email="twoauth@example.com").first()
        svc = TwoAuthService()
        svc.create_and_send_code(user)
        assert svc.verify_code(user, "000000") is False, "Se ha aceptado un código incorrecto"


def test_can_resend_cooldown(test_client, monkeypatch):

    with test_client.application.app_context():
        user = User.query.filter_by(email="twoauth@example.com").first()
        svc = TwoAuthService()
        token = svc.create_and_send_code(user)

        assert svc.can_resend(user) is False

        def fake_now(tz=timezone.utc):
            return token.created_at.replace(tzinfo=timezone.utc) + timedelta(seconds=61)

        monkeypatch.setattr(
            "app.modules.twoauth.services.datetime",
            type("_dt", (), {"now": staticmethod(fake_now), "timezone": timezone, "timedelta": timedelta}),
        )
        assert svc.can_resend(user) is True


def test_signup_code_stored_in_session_and_email_sent(mock_send, test_client):
    svc = TwoAuthService()
    with test_client.application.test_request_context("/"):
        svc.create_and_send_signup_code("newuser@example.com")
        assert mock_send.called
        assert session.get("pending_signup_2fa")
        assert session.get("pending_signup_2fa_code")
        assert session.get("pending_signup_2fa_last_sent")


def test_resend_signup_cooldown(monkeypatch, test_client):
    svc = TwoAuthService()

    with test_client.application.test_request_context("/"):
        session["pending_signup_2fa_last_sent"] = datetime.now(timezone.utc).isoformat()
        assert svc.can_resend_signup() is False

    def fake_now(tz=timezone.utc):
        return datetime.now(timezone.utc) + timedelta(seconds=61)

    monkeypatch.setattr(
        "app.modules.twoauth.services.datetime",
        type("_dt", (), {"now": staticmethod(fake_now), "timezone": timezone, "timedelta": timedelta}),
    )
    with test_client.application.test_request_context("/"):
        session["pending_signup_2fa_last_sent"] = datetime.now(timezone.utc).isoformat()
        assert svc.can_resend_signup() is True
