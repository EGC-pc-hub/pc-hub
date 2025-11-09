import json
import os
import tempfile
import types
from unittest.mock import patch

import pytest

from app.modules.dataset.services import (
    GitHubAPIError,
    GitHubContentService,
    GitHubRepoService,
    repo_name_formatting,
)


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text or json.dumps(self._json)

    def json(self):
        return self._json


@pytest.mark.usefixtures("test_client")
class TestBackupUnitGithub:
    # Tests unitarios de funciones y servicios GitHub del módulo dataset

    # ---------------------- repo_name_formatting ----------------------
    def test_repo_name_formatting_basic(self):
        # Normaliza correctamente espacios y mayúsculas a kebab-case sencillo
        assert repo_name_formatting("My DataSet Title") == "my-dataset-title"

    def test_repo_name_formatting_strips_and_filters(self):
        # Elimina símbolos no permitidos y recorta espacios antes de normalizar
        assert repo_name_formatting("  **Mi Repo?!  ") == "mi-repo"

    def test_repo_name_formatting_empty_returns_dataset(self):
        # Si la entrada queda vacía tras limpiar, devuelve el fallback 'dataset'
        assert repo_name_formatting("    !!!   ") == "dataset"

    # ---------------------- GitHubRepoService.create_repo ----------------------
    def test_github_repo_service_create_repo_success(self):
        # Crea un repositorio con éxito mockeando la llamada POST a GitHub

        with patch("app.modules.dataset.services.requests.post") as mock_post:

            def _resp(*args, **kwargs):
                mock_post.payload = kwargs.get("json")  # Capturar body
                return DummyResponse(
                    status_code=201, json_data={"full_name": "user/repo", "html_url": "https://github.com/user/repo"}
                )

            mock_post.side_effect = _resp
            svc = GitHubRepoService(token="abc123")
            data = svc.create_repo("repo-name", private=True, description="Desc")
            assert data["full_name"] == "user/repo"
            assert mock_post.payload["name"] == "repo-name"
            assert mock_post.payload["private"] is True

    def test_github_repo_service_create_repo_repo_exists_error(self):
        # Si GitHub devuelve 422 por repo existente, se lanza GitHubAPIError con reason 'repo_exists'
        payload = {
            "message": "Validation Failed",
            "errors": [
                {
                    "resource": "Repository",
                    "field": "name",
                    "code": "custom",
                    "message": "name already exists on this account",
                }
            ],
            "documentation_url": "https://docs.github.com/rest/reference/repos",
        }
        with patch(
            "app.modules.dataset.services.requests.post", return_value=DummyResponse(status_code=422, json_data=payload)
        ):
            svc = GitHubRepoService(token="abc123")
            with pytest.raises(GitHubAPIError) as exc:
                svc.create_repo("existing")
            assert exc.value.status == 422
            assert exc.value.reason == "repo_exists"
            assert "already exists" in exc.value.message

    def test_github_repo_service_create_repo_generic_error(self):
        # Errores 5xx se traducen a GitHubAPIError con el mensaje de la API
        with patch(
            "app.modules.dataset.services.requests.post",
            return_value=DummyResponse(status_code=500, json_data={"message": "Server error"}),
        ):
            svc = GitHubRepoService(token="abc123")
            with pytest.raises(GitHubAPIError) as exc:
                svc.create_repo("bad")
            assert exc.value.status == 500
            assert str(exc.value) in ("Server error", exc.value.message)

    # ---------------------- GitHubContentService._put_file ----------------------
    def test_github_content_service_put_file_uploaded(self):
        # Sube fichero nuevo cuando no existe (GET 404 -> PUT 201)
        with patch(
            "app.modules.dataset.services.requests.get", return_value=DummyResponse(status_code=404, json_data={})
        ):
            with patch(
                "app.modules.dataset.services.requests.put", return_value=DummyResponse(status_code=201, json_data={})
            ):
                svc = GitHubContentService(token="tok", repo_full_name="user/repo")
                action = svc._put_file("file.txt", b"hello", message="msg")
                assert action == "uploaded"

    def test_github_content_service_put_file_updated(self):
        # Actualiza fichero existente (GET 200 con sha -> PUT 200)
        with patch(
            "app.modules.dataset.services.requests.get",
            return_value=DummyResponse(status_code=200, json_data={"sha": "abc"}),
        ):
            with patch(
                "app.modules.dataset.services.requests.put", return_value=DummyResponse(status_code=200, json_data={})
            ):
                svc = GitHubContentService(token="tok", repo_full_name="user/repo")
                action = svc._put_file("file.txt", b"hello", message="msg")
                assert action == "updated"

    def test_github_content_service_put_file_error(self):
        # Errores en PUT deben provocar excepción (por ejemplo 400)
        with patch(
            "app.modules.dataset.services.requests.get", return_value=DummyResponse(status_code=404, json_data={})
        ):
            with patch(
                "app.modules.dataset.services.requests.put",
                return_value=DummyResponse(status_code=400, json_data={"error": "bad"}),
            ):
                svc = GitHubContentService(token="tok", repo_full_name="user/repo")
                with pytest.raises(RuntimeError):
                    svc._put_file("file.txt", b"hello", message="msg")

    # ---------------------- GitHubContentService.upload_dataset ----------------------
    def test_github_content_service_upload_dataset_folder_not_found(self):
        # Si no existe la carpeta de uploads esperada, se lanza RuntimeError

        svc = GitHubContentService(token="tok", repo_full_name="user/repo")
        DummyDataset = types.SimpleNamespace(id=999, user_id=1)
        with pytest.raises(RuntimeError):
            svc.upload_dataset(DummyDataset)

    def test_github_content_service_upload_dataset_success(self, tmp_path):
        # Sube todos los ficheros existentes en la estructura de uploads

        working_dir = tmp_path
        os.environ["WORKING_DIR"] = str(working_dir)
        user_id = 42
        dataset_id = 7
        base_dir = working_dir / "uploads" / f"user_{user_id}" / f"dataset_{dataset_id}"
        base_dir.mkdir(parents=True)
        (base_dir / "a.txt").write_text("A")
        subdir = base_dir / "sub"
        subdir.mkdir()
        (subdir / "b.txt").write_text("B")

        uploaded_paths = []

        with patch(
            "app.modules.dataset.services.requests.get", return_value=DummyResponse(status_code=404, json_data={})
        ):
            with patch(
                "app.modules.dataset.services.requests.put",
                side_effect=lambda *args, **kwargs: uploaded_paths.append(args[0])
                or DummyResponse(status_code=201, json_data={}),
            ):
                svc = GitHubContentService(token="tok", repo_full_name="user/repo")
                DummyDataset = types.SimpleNamespace(id=dataset_id, user_id=user_id)
                result = svc.upload_dataset(DummyDataset)
                assert result["uploaded"] == 2  # a.txt y sub/b.txt
                assert len(uploaded_paths) == 2
