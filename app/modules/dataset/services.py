import base64
import hashlib
import logging
import os
import shutil
import uuid
from typing import Optional

import requests
from flask import request

from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DataSet, DSMetaData, DSViewRecord
from app.modules.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.modules.featuremodel.repositories import FeatureModelRepository, FMMetaDataRepository
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class DataSetService(BaseService):
    def __init__(self):
        super().__init__(DataSetRepository())
        self.feature_model_repository = FeatureModelRepository()
        self.author_repository = AuthorRepository()
        self.dsmetadata_repository = DSMetaDataRepository()
        self.fmmetadata_repository = FMMetaDataRepository()
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.hubfiledownloadrecord_repository = HubfileDownloadRecordRepository()
        self.hubfilerepository = HubfileRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()
        self.hubfileviewrecord_repository = HubfileViewRecordRepository()

    def move_feature_models(self, dataset: DataSet):
        current_user = AuthenticationService().get_authenticated_user()
        source_dir = current_user.temp_folder()

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(
            working_dir,
            "uploads",
            f"user_{
                current_user.id}",
            f"dataset_{
                dataset.id}",
        )

        os.makedirs(dest_dir, exist_ok=True)

        for feature_model in dataset.feature_models:
            uvl_filename = feature_model.fm_meta_data.uvl_filename
            shutil.move(os.path.join(source_dir, uvl_filename), dest_dir)

    def get_synchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_synchronized(current_user_id)

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_unsynchronized(current_user_id)

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        return self.repository.get_unsynchronized_dataset(current_user_id, dataset_id)

    def latest_synchronized(self):
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        return self.repository.count_synchronized_datasets()

    def count_feature_models(self):
        return self.feature_model_service.count_feature_models()

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        return self.dsmetadata_repository.count()

    def total_dataset_downloads(self) -> int:
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.dsviewrecord_repostory.total_dataset_views()

    def trending_datasets_last_week(self, limit: int = 3):
        """
        WI101: Retorna los datasets más descargados en la semana anterior.

        LÓGICA DE NEGOCIO:
        ------------------
        "Semana anterior" se define como la semana calendario previa a la semana
        actual, de lunes 00:00 UTC a lunes 00:00 UTC (exclusive).

        Ejemplo:
        - Si hoy es miércoles 8 de noviembre de 2025:
          - Semana actual: lunes 4 nov - domingo 10 nov
          - Semana anterior: lunes 28 oct - domingo 3 nov
          - El método retorna datasets descargados entre 28 oct y 4 nov

        RETORNO:
        --------
        Cada item es un diccionario con:
        - id: ID del dataset
        - title: Título del dataset
        - main_author: Nombre del primer autor (o None si no hay)
        - downloads: Número de descargas en la semana anterior
        - url: URL del dataset en uvlhub (DOI)

        ORDEN:
        ------
        Los datasets se retornan ordenados por número de descargas descendente.
        Si hay empates, el orden puede variar entre ejecuciones.

        Args:
            limit: Número máximo de datasets a retornar (por defecto 3 para el widget)

        Returns:
            Lista de diccionarios con la información de cada dataset
        """
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        # start of current week (Monday 00:00 UTC)
        start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(
            days=now.weekday()
        )
        last_week_start = start_of_week - timedelta(days=7)
        last_week_end = start_of_week

        # Obtener los dataset_id más descargados en el período
        top = self.dsdownloadrecord_repository.top_downloaded_in_period(last_week_start, limit, until=last_week_end)
        results = []
        for item in top:
            # item is (dataset_id, count)
            dataset_id, count = item
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                continue
            # pick the first author if available
            main_author = None
            try:
                if dataset.ds_meta_data.authors and len(dataset.ds_meta_data.authors) > 0:
                    main_author = dataset.ds_meta_data.authors[0].name
            except Exception:
                main_author = None

            results.append(
                {
                    "id": dataset.id,
                    "title": dataset.ds_meta_data.title,
                    "main_author": main_author,
                    "downloads": int(count),
                    "url": dataset.get_uvlhub_doi(),
                }
            )

        return results

    def trending_datasets_this_week(self, limit: int = 3):
        """
        WI101: Retorna los datasets más descargados en la semana actual.

        LÓGICA DE NEGOCIO:
        ------------------
        "Semana actual" se define desde el lunes de esta semana a las 00:00 UTC
        hasta el momento actual.

        DIFERENCIA CON trending_datasets_last_week():
        ----------------------------------------------
        - trending_datasets_last_week(): Semana completa anterior (7 días completos)
        - trending_datasets_this_week(): Semana actual en progreso (puede ser 1-7 días)

        NOTA:
        -----
        Esta función se creó para posibles extensiones futuras del widget.
        Actualmente el widget usa solo trending_datasets_last_week().

        Args:
            limit: Número máximo de datasets a retornar

        Returns:
            Lista de diccionarios con la información de cada dataset (mismo formato que last_week)
        """
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        # Monday is weekday 0. Compute start of week (Monday 00:00:00)
        start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)
        # subtract number of days since monday
        start_of_week = start_of_week - timedelta(days=now.weekday())

        top = self.dsdownloadrecord_repository.top_downloaded_in_period(start_of_week, limit)
        results = []
        for item in top:
            dataset_id, count = item
            dataset = self.repository.get_by_id(dataset_id)
            if not dataset:
                continue
            main_author = None
            try:
                if dataset.ds_meta_data.authors and len(dataset.ds_meta_data.authors) > 0:
                    main_author = dataset.ds_meta_data.authors[0].name
            except Exception:
                main_author = None

            results.append(
                {
                    "id": dataset.id,
                    "title": dataset.ds_meta_data.title,
                    "main_author": main_author,
                    "downloads": int(count),
                    "url": dataset.get_uvlhub_doi(),
                }
            )

        return results

    def create_from_form(self, form, current_user) -> DataSet:
        main_author = {
            "name": f"{
                current_user.profile.surname}, {
                current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }
        try:
            logger.info(f"Creating dsmetadata...: {form.get_dsmetadata()}")
            dsmetadata = self.dsmetadata_repository.create(**form.get_dsmetadata())
            for author_data in [main_author] + form.get_authors():
                author = self.author_repository.create(commit=False, ds_meta_data_id=dsmetadata.id, **author_data)
                dsmetadata.authors.append(author)

            dataset = self.create(commit=False, user_id=current_user.id, ds_meta_data_id=dsmetadata.id)

            for feature_model in form.feature_models:
                uvl_filename = feature_model.uvl_filename.data
                fmmetadata = self.fmmetadata_repository.create(commit=False, **feature_model.get_fmmetadata())
                for author_data in feature_model.get_authors():
                    author = self.author_repository.create(commit=False, fm_meta_data_id=fmmetadata.id, **author_data)
                    fmmetadata.authors.append(author)

                fm = self.feature_model_repository.create(
                    commit=False, data_set_id=dataset.id, fm_meta_data_id=fmmetadata.id
                )

                # associated files in feature model
                file_path = os.path.join(current_user.temp_folder(), uvl_filename)
                checksum, size = calculate_checksum_and_size(file_path)

                file = self.hubfilerepository.create(
                    commit=False, name=uvl_filename, checksum=checksum, size=size, feature_model_id=fm.id
                )
                fm.files.append(file)
            self.repository.session.commit()
        except Exception as exc:
            logger.info(f"Exception creating dataset from form...: {exc}")
            self.repository.session.rollback()
            raise exc
        return dataset

    def update_dsmetadata(self, id, **kwargs):
        return self.dsmetadata_repository.update(id, **kwargs)

    def get_uvlhub_doi(self, dataset: DataSet) -> str:
        domain = os.getenv("DOMAIN", "localhost")
        return f"http://{domain}/doi/{dataset.ds_meta_data.dataset_doi}"


class AuthorService(BaseService):
    def __init__(self):
        super().__init__(AuthorRepository())


class DSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(DSDownloadRecordRepository())


class DSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(DSViewRecordRepository())

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:

        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


class DOIMappingService(BaseService):
    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        doi_mapping = self.repository.get_new_doi(old_doi)
        if doi_mapping:
            return doi_mapping.dataset_doi_new
        else:
            return None


class SizeService:

    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"
        else:
            return f"{round(size / (1024 ** 3), 2)} GB"


def repo_name_formatting(name: str) -> str:
    formated_name = name.strip().lower()
    formated_name = formated_name.replace(" ", "-")

    # Para quitar caracteres raros
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_."
    formated_name = "".join(ch for ch in formated_name if ch in allowed)
    # Para evitar puntos/guiones/barras bajos al principio o final
    formated_name = formated_name.strip("-._")

    return formated_name or "dataset"


class GitHubRepoService:

    # Servicio para crear repositorios en GitHub usando la API REST y un token OAuth de usuario.

    def __init__(self, token: str):
        if not token:
            raise RuntimeError("GitHub OAuth token is required.")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_repo(self, name: str, private: bool = True, description: Optional[str] = None) -> dict:
        payload = {
            "name": name,
            "private": private,
            "auto_init": False,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False,
            "description": description or "Backup created by PC-Hub",
        }
        # Crear el repositorio en la cuenta del usuario autenticado
        url = "https://api.github.com/user/repos"

        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
        if resp.status_code not in (201,):
            # Manejar errores de la API de GitHub
            try:
                data = resp.json()
            except Exception:
                data = None

            message = None
            reason = None
            docs = None
            if data:
                message = data.get("message")
                docs = data.get("documentation_url")
                # Detectar errores específicos
                # Error 422: nombre de repositorio ya existe
                if resp.status_code == 422 and isinstance(data.get("errors"), list):
                    for err in data.get("errors", []):
                        if (
                            err.get("resource") == "Repository"
                            and err.get("field") == "name"
                            and "already exists" in (err.get("message") or "")
                        ):
                            reason = "repo_exists"
                            message = (
                                "A repository with this name already exists in your account. "
                                "Please change the dataset title or remove/rename the existing repository on GitHub."
                            )
                            break

            if not message:
                message = f"GitHub error ({resp.status_code})."

            raise GitHubAPIError(status=resp.status_code, message=message, reason=reason, docs_url=docs, raw=data)
        return resp.json()


class GitHubAPIError(Exception):

    def __init__(
        self,
        status: int,
        message: str,
        reason: Optional[str] = None,
        docs_url: Optional[str] = None,
        raw: Optional[dict] = None,
    ):
        super().__init__(message)
        self.status = status
        self.message = message
        self.reason = reason
        self.docs_url = docs_url
        self.raw = raw or {}


class GitHubContentService:
    # Servicio para subir archivos a un repositorio GitHub usando la API REST y un token OAuth de usuario.

    def __init__(self, token: str, repo_full_name: str, branch: str = "main"):
        if not token:
            raise RuntimeError("GitHub OAuth token is required.")
        if not repo_full_name:
            raise RuntimeError("Repository full name required (owner/repo).")
        self.token = token
        self.repo = repo_full_name
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{self.repo}/contents"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get_file_sha(self, path: str) -> Optional[str]:
        url = f"{self.base_url}/{path}"
        params = {"ref": self.branch}
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("sha")
        return None

    def _put_file(self, path: str, content_bytes: bytes, message: str) -> str:
        sha = self._get_file_sha(path)
        body = {
            "message": message,
            "content": base64.b64encode(content_bytes).decode("utf-8"),
            "branch": self.branch,
        }
        if sha:
            body["sha"] = sha

        url = f"{self.base_url}/{path}"
        resp = requests.put(url, headers=self.headers, json=body, timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"GitHub upload error {resp.status_code}: {resp.text}")
        return "updated" if sha else "uploaded"

    def upload_dataset(self, dataset: DataSet, prefix: str = "") -> dict:
        working_dir = os.getenv("WORKING_DIR", "")
        source_dir = os.path.join(
            working_dir,
            "uploads",
            f"user_{dataset.user_id}",
            f"dataset_{dataset.id}",
        )
        if not os.path.isdir(source_dir):
            raise RuntimeError(f"Dataset folder not found: {source_dir}")

        uploaded_count = 0

        for root, _, files in os.walk(source_dir):
            for filename in files:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, source_dir).replace("\\", "/")
                repo_path = f"{prefix}/{rel_path}" if prefix else rel_path
                with open(full_path, "rb") as fh:
                    content = fh.read()
                action = self._put_file(
                    repo_path,
                    content,
                    message=f"Backup dataset {dataset.id}: add {rel_path}",
                )
                if action == "uploaded":
                    uploaded_count += 1

        return {"uploaded": uploaded_count}
