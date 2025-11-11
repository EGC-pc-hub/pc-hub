from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token


class DatasetBehavior(TaskSet):
    def on_start(self):
        self.dataset()

    @task
    def dataset(self):
        response = self.client.get("/dataset/upload")
        get_csrf_token(response)


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()


class GithubBackupBehavior(TaskSet):
    def on_start(self):
        # Intentar acceder al status inicial de GitHub (no autenticado)
        self.client.get("/github/status")

    @task
    def github_oauth_flow_and_backup(self):
        # Flujo básico: status -> login page ->
        # callback simulado -> backup UI -> backup API

        # 1) Comprobar estado OAuth
        self.client.get("/github/status")

        # 2) Solicitar login de GitHub (normalmente devuelve HTML con form y state)
        login_resp = self.client.get("/github/login?next=/datasets")
        try:
            get_csrf_token(login_resp)
        except Exception:
            pass

        # 3) Acceder a la UI de backup (sin token debería redirigir a /github/login)

        # Este endpoint requiere dataset_id válido; usamos un id genérico 1
        resp = self.client.get("/dataset/1/backup/github-ui")
        # Sólo verificamos que responde; la semántica exacta depende de datos/estado
        assert resp.status_code in (200, 302, 401, 403)

        # 4) Acceder al endpoint de autorización de backup (sin login puede redirigir)
        authz_resp = self.client.get("/dataset/1/backup/authorised-user")
        assert authz_resp.status_code in (200, 302, 401, 403)

        # 5) Intentar el backup API (sin token probablemente 401)
        backup_api = self.client.post("/dataset/1/backup/github")
        assert backup_api.status_code in (200, 302, 401, 403)


class GithubBackupUser(HttpUser):
    tasks = [GithubBackupBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
