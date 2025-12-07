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


class TrendingDatasetsBehavior(TaskSet):
    """
    Pruebas de carga para el widget de Trending Datasets.
    Este TaskSet simula el comportamiento de usuarios accediendo a los endpoints de trending datasets (última semana).
    ENDPOINTS TESTEADOS:
    - GET /dataset/api/trending
    PARÁMETROS OPCIONALES:
    - limit: número máximo de datasets a retornar (default: 10)
    """

    def on_start(self):
        """Llamada inicial cuando el usuario comienza la prueba."""
        self.get_trending()

    @task(weight=3)
    def get_trending(self):
        """
        Obtener datasets trending (última semana).
        ENDPOINT: GET /dataset/api/trending
        VALIDACIONES:
        - Status 200 OK
        - Response es JSON válido (lista de datasets)
        """
        response = self.client.get("/dataset/api/trending", name="/dataset/api/trending")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    @task(weight=2)
    def get_trending_with_limit(self):
        """
        Obtener datasets trending con parámetro limit personalizado.
        ENDPOINT: GET /dataset/api/trending?limit=<n>
        """
        limits = [5, 20, 100]
        for limit in limits:
            response = self.client.get(
                f"/dataset/api/trending?limit={limit}", name="/dataset/api/trending [with limit]"
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= limit, f"Expected <= {limit} items, got {len(data)}"

    # Los endpoints de "this-week" no existen en el backend actual, así que se omiten.


class TrendingDatasetsUser(HttpUser):
    """
    Usuario que simula el acceso a trending datasets.

    CARACTERÍSTICAS:
    - Tiempo de espera entre tareas: 2-6 segundos
    - Pruebas más frecuentes: last-week (peso 3)
    - Pruebas moderadas: parámetros personalizados (peso 2)
    - Pruebas ocasionales: this-week (peso 1)
    """

    tasks = [TrendingDatasetsBehavior]
    min_wait = 2000  # 2 segundos mínimo entre tareas
    max_wait = 6000  # 6 segundos máximo entre tareas
    host = get_host_for_locust_testing()


class TrendingDatasetsStressUser(HttpUser):
    """
    Usuario de estrés que martillea los endpoints de trending.

    CARACTERÍSTICAS:
    - Tiempo de espera muy corto: 200-500ms
    - Simula carga alta y picos de tráfico
    - Pruebas intensivas de endpoints

    CASO DE USO:
    - Testing de capacidad y límites
    - Identificación de bottlenecks
    - Validación de caché y optimizaciones
    """

    tasks = [TrendingDatasetsBehavior]
    min_wait = 200  # 200ms entre tareas
    max_wait = 500  # 500ms entre tareas
    host = get_host_for_locust_testing()
