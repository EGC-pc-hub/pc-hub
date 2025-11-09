import json
import os
from unittest.mock import patch

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType


def create_dataset_for_user(user_id, title="DS UI Backup"):
    meta = DSMetaData(
        title=title,
        description="desc",
        publication_type=PublicationType.OTHER,
        publication_doi=None,
        dataset_doi=None,
        tags="",
    )
    db.session.add(meta)
    db.session.flush()
    ds = DataSet(user_id=user_id, ds_meta_data_id=meta.id)
    db.session.add(ds)
    db.session.commit()
    return ds


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


@pytest.mark.usefixtures("test_client")
class TestBackupGithubUI:
    # Pruebas del endpoint GET /dataset/<id>/backup/github-ui
    # (Caso en el que se abre el popup)

    def _inject_token(self, client, value="token-123"):
        with client.session_transaction() as sess:
            sess["github_token"] = value

    def test_requires_login_redirect(self, test_client):
        # Si el usuario no está autenticado se redirige a /login

        user = User.query.filter_by(email="test@example.com").first()
        ds = create_dataset_for_user(user.id)
        resp = test_client.get(f"/dataset/{ds.id}/backup/github-ui")
        assert resp.status_code in (302, 401)  # normalmente 302 a /login
        # Confirmar que apunta a login
        location = resp.headers.get("Location", "")
        assert "/login" in location

    def test_without_github_token_redirects_to_github_login(self, test_client):
        # Sin github_token en sesión se redirige al flujo OAuth (/github/login)

        user = User.query.filter_by(email="test@example.com").first()
        login(test_client, "test@example.com", "test1234")
        ds = create_dataset_for_user(user.id)

        resp = test_client.get(f"/dataset/{ds.id}/backup/github-ui")
        # Debe redirigir a auth.github_login con parámetro next
        assert resp.status_code == 302
        location = resp.headers.get("Location", "")
        assert "/github/login" in location
        assert "next=" in location

    def test_with_token_no_return_url_html_message(self, test_client):
        # Con token y sin parámetro return, muestra mensaje HTML de backup completado

        user = User.query.filter_by(email="test@example.com").first()
        login(test_client, "test@example.com", "test1234")
        ds = create_dataset_for_user(user.id)
        self._inject_token(test_client)

        # Mock servicios GitHub
        from app.modules.dataset import services as ds_services

        with patch.object(
            ds_services.GitHubRepoService,
            "create_repo",
            return_value={
                "full_name": "me/ds-ui-backup",
                "html_url": "https://github.com/me/ds-ui-backup",
                "default_branch": "main",
            },
        ):
            with patch.object(ds_services.GitHubContentService, "upload_dataset", return_value={"uploaded": 1}):
                resp = test_client.get(f"/dataset/{ds.id}/backup/github-ui")
                assert resp.status_code == 200
                body = resp.get_data(as_text=True)
                assert "Backup completed" in body
                assert "https://github.com/me/ds-ui-backup" in body

    def test_with_token_popup_flow(self, test_client):
        # Flujo popup (param popup=1): devuelve script postMessage y cierra ventana

        user = User.query.filter_by(email="test@example.com").first()
        login(test_client, "test@example.com", "test1234")
        ds = create_dataset_for_user(user.id)
        self._inject_token(test_client)

        from app.modules.dataset import services as ds_services

        with patch.object(
            ds_services.GitHubRepoService,
            "create_repo",
            return_value={
                "full_name": "me/ds-popup",
                "html_url": "https://github.com/me/ds-popup",
                "default_branch": "main",
            },
        ):
            with patch.object(ds_services.GitHubContentService, "upload_dataset", return_value={"uploaded": 2}):
                resp = test_client.get(f"/dataset/{ds.id}/backup/github-ui?return=/datasets&popup=1")
                assert resp.status_code == 200
                body = resp.get_data(as_text=True)
                assert "postMessage" in body
                assert "Backup completed" in body
                assert "window.close" in body

    def test_with_token_return_url_redirect(self, test_client):
        # Con token y parámetro return, redirige con query params de resultado

        user = User.query.filter_by(email="test@example.com").first()
        login(test_client, "test@example.com", "test1234")
        ds = create_dataset_for_user(user.id)
        self._inject_token(test_client)

        from app.modules.dataset import services as ds_services

        with patch.object(
            ds_services.GitHubRepoService,
            "create_repo",
            return_value={
                "full_name": "me/ds-redirect",
                "html_url": "https://github.com/me/ds-redirect",
                "default_branch": "main",
            },
        ):
            with patch.object(ds_services.GitHubContentService, "upload_dataset", return_value={"uploaded": 5}):
                resp = test_client.get(f"/dataset/{ds.id}/backup/github-ui?return=/dashboard")
                assert resp.status_code == 302
                location = resp.headers.get("Location", "")
                assert "/dashboard" in location
                assert "backup=done" in location
                assert "uploaded=5" in location
                assert ("repo=me/ds-redirect" in location) or ("repo=me%2Fds-redirect" in location)
