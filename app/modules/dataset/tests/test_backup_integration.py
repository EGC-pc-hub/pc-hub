from unittest.mock import patch

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType


def do_login(client, email, password):
    return client.post("/login", data=dict(email=email, password=password), follow_redirects=True)


def create_dataset_for_user(user_id, title="Dataset Title"):
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


@pytest.mark.usefixtures("test_client")
class TestBackupIntegration:

    def test_backup_authorised_user_ok(self, test_client):
        # El propietario del dataset está autorizado para hacer backup

        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        ds = create_dataset_for_user(user.id, title="Mi DS")

        # Autenticar al usuario de pruebas
        do_login(test_client, "test@example.com", "test1234")
        # Consultar endpoint de autorización de backup
        resp = test_client.get(f"/dataset/{ds.id}/backup/authorised-user")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["can_backup"] is True

    def test_backup_authorised_user_forbidden(self, test_client):
        # Un usuario no propietario no está autorizado (403)

        # Crear propietario distinto
        other = User(email="other@example.com", password="x")
        db.session.add(other)
        db.session.commit()

        ds = create_dataset_for_user(other.id, title="Privado")

        do_login(test_client, "test@example.com", "test1234")
        resp = test_client.get(f"/dataset/{ds.id}/backup/authorised-user")
        assert resp.status_code == 403
        data = resp.get_json()
        assert "Not authorized" in data.get("error", "")

    def test_backup_github_requires_token(self, test_client):
        # Para POST /backup/github se requiere github_token en sesión (401 si falta)
        user = User.query.filter_by(email="test@example.com").first()
        ds = create_dataset_for_user(user.id, title="DS sin token")

        do_login(test_client, "test@example.com", "test1234")
        # No establecer github_token en la sesión
        resp = test_client.post(f"/dataset/{ds.id}/backup/github")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data.get("error") == "Not authenticated with GitHub"

    def test_backup_github_success_with_mocks(self, test_client):
        # Backup GitHub exitoso mockeando la creación de repo y la subida de contenido
        user = User.query.filter_by(email="test@example.com").first()
        ds = create_dataset_for_user(user.id, title="Backup Title")

        do_login(test_client, "test@example.com", "test1234")
        # Insertar token de GitHub en la sesión del cliente
        with test_client.session_transaction() as sess:
            sess["github_token"] = "fake-token"

        # Mockear creación de repo y subida de ficheros
        from app.modules.dataset import services as ds_services

        with patch.object(
            ds_services.GitHubRepoService,
            "create_repo",
            return_value={
                "full_name": "me/backup-title",
                "html_url": "https://github.com/me/backup-title",
                "default_branch": "main",
            },
        ):
            with patch.object(ds_services.GitHubContentService, "upload_dataset", return_value={"uploaded": 3}):
                # llamar al endpoint de backup
                resp = test_client.post(f"/dataset/{ds.id}/backup/github")
                assert resp.status_code == 200
                # Acomprobar estructura de respuesta
                data = resp.get_json()
                assert data["message"] == "Backup completed"
                assert data["repo"].startswith("me/")
                assert data["uploaded"] == 3
