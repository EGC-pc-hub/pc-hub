"""
WI101: Tests unitarios para la funcionalidad de Trending Datasets

COBERTURA DE TESTS:
-------------------
Este archivo contiene tests pytest que validan la lógica de negocio
del servicio trending_datasets_last_week() y el endpoint de API asociado.

TESTS INCLUIDOS:
----------------
1. test_trending_datasets_last_week: Test principal que verifica orden y contenido
2. test_trending_last_week_no_downloads: Caso edge cuando no hay descargas
3. test_trending_last_week_ties: Manejo de empates en número de descargas
4. test_api_trending_returns_json: Validación del endpoint API REST

DIFERENCIA CON test_trending_selenium.py:
------------------------------------------
- test_trending_last_week.py: Tests unitarios de lógica de negocio (ESTE ARCHIVO)
- test_trending_selenium.py: Test end-to-end con navegador (interfaz gráfica)

FIXTURES UTILIZADAS:
--------------------
- clean_database: Limpia la base de datos antes de cada test
- test_app: Proporciona contexto de aplicación Flask
- test_client: Cliente HTTP para probar endpoints
"""

import uuid
from datetime import datetime, timedelta, timezone

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSDownloadRecord, DSMetaData, PublicationType
from app.modules.dataset.services import DataSetService


def create_dataset_with_author(title, user_id, author_name):
    """
    Función auxiliar para crear datasets en los tests.

    Simplifica la creación de datasets de prueba con metadata y autor.
    Reutilizada en múltiples tests para mantener consistencia.
    """
    dsmeta = DSMetaData(title=title, description="desc", publication_type=PublicationType.NONE)
    author = Author(name=author_name)
    dsmeta.authors.append(author)
    dataset = DataSet(user_id=user_id, ds_meta_data=dsmeta)
    db.session.add(dsmeta)
    db.session.add(dataset)
    db.session.flush()
    return dataset


def create_download(dataset_id, days_ago=0):
    """
    Función auxiliar para crear registros de descarga en los tests.

    Permite simular descargas en fechas específicas del pasado.
    Útil para testear la lógica de filtrado por rango de fechas.
    """
    download = DSDownloadRecord(
        dataset_id=dataset_id,
        download_date=datetime.now(timezone.utc) - timedelta(days=days_ago),
        download_cookie=str(uuid.uuid4()),
    )
    db.session.add(download)


def test_trending_datasets_last_week(clean_database, test_app):
    """
    WI101: Test principal que valida el cálculo de trending datasets.

    OBJETIVO:
    ---------
    Verificar que trending_datasets_last_week() retorna los datasets
    correctos en el orden correcto basándose en las descargas de la
    semana anterior.

    ESCENARIO DE PRUEBA:
    --------------------
    - 4 datasets creados: DS One, DS Two, DS Three, DS Old
    - DS One: 5 descargas en la semana anterior ← PRIMERO
    - DS Two: 3 descargas en la semana anterior ← SEGUNDO
    - DS Three: 2 descargas en la semana anterior ← TERCERO
    - DS Old: 10 descargas ANTES de la semana anterior ← NO aparece

    VALIDACIONES:
    -------------
    ✓ Se retornan exactamente 3 datasets
    ✓ El orden es: DS One, DS Two, DS Three
    ✓ Los números de descargas son: 5, 3, 2
    ✓ DS Old no aparece (tiene más descargas pero fuera del rango)

    LÓGICA CRÍTICA TESTEADA:
    ------------------------
    - Filtrado por rango de fechas (última semana calendario)
    - Ordenamiento descendente por número de descargas
    - Exclusión de descargas fuera del rango temporal
    """
    # create a user
    user = User(email="u@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    # create datasets
    ds1 = create_dataset_with_author("DS One", user.id, "Author One")
    ds2 = create_dataset_with_author("DS Two", user.id, "Author Two")
    ds3 = create_dataset_with_author("DS Three", user.id, "Author Three")
    ds4 = create_dataset_with_author("DS Old", user.id, "Author Old")

    db.session.commit()

    # create downloads inside the previous calendar week
    from datetime import datetime, timedelta, timezone

    # Calcular inicio de la semana anterior (lunes 00:00 UTC)
    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(
        days=now.weekday()
    )
    last_week_start = start_of_week - timedelta(days=7)

    # place records on last_week_start + 1, +2, +3 days
    # DS One: 5 descargas (más popular de la semana pasada)
    for _ in range(5):
        rec = DSDownloadRecord(
            dataset_id=ds1.id,
            download_date=last_week_start + timedelta(days=1),
            download_cookie=str(uuid.uuid4()),
        )
        db.session.add(rec)

    # DS Two: 3 descargas (segunda más popular)
    for _ in range(3):
        rec = DSDownloadRecord(
            dataset_id=ds2.id,
            download_date=last_week_start + timedelta(days=2),
            download_cookie=str(uuid.uuid4()),
        )
        db.session.add(rec)

    # DS Three: 2 descargas (tercera más popular)
    for _ in range(2):
        rec = DSDownloadRecord(
            dataset_id=ds3.id,
            download_date=last_week_start + timedelta(days=3),
            download_cookie=str(uuid.uuid4()),
        )
        db.session.add(rec)

    # ds4 older than last week - NO debe aparecer en trending
    for _ in range(10):
        rec = DSDownloadRecord(
            dataset_id=ds4.id,
            download_date=last_week_start - timedelta(days=10),
            download_cookie=str(uuid.uuid4()),
        )
        db.session.add(rec)

    db.session.commit()

    # Ejecutar el servicio de trending
    service = DataSetService()
    trending = service.trending_datasets_last_week(limit=3)

    # expect ds1, ds2, ds3 in that order
    assert len(trending) == 3
    assert trending[0]["id"] == ds1.id
    assert trending[0]["downloads"] == 5
    assert trending[1]["id"] == ds2.id
    assert trending[1]["downloads"] == 3
    assert trending[2]["id"] == ds3.id
    assert trending[2]["downloads"] == 2


def test_trending_last_week_no_downloads(clean_database, test_app):
    """
    WI101: Test de caso edge - sin descargas en la semana anterior.

    OBJETIVO:
    ---------
    Verificar que el servicio maneja correctamente el caso cuando no hay
    descargas en el período de la semana anterior.

    ESCENARIO:
    ----------
    - Datasets existen en la base de datos
    - NO hay registros de descargas en ningún período

    COMPORTAMIENTO ESPERADO:
    ------------------------
    El servicio debe retornar una lista vacía [], no None ni error.

    IMPLICACIÓN EN EL WIDGET:
    -------------------------
    El template detectará la lista vacía y mostrará el mensaje:
    "No trending datasets for last week."
    """
    user = User(email="no@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    # create datasets but no downloads
    create_dataset_with_author("A", user.id, "Author A")
    create_dataset_with_author("B", user.id, "Author B")
    db.session.commit()

    service = DataSetService()
    trending = service.trending_datasets_last_week(limit=3)
    assert trending == []


def test_trending_last_week_ties(clean_database, test_app):
    """
    WI101: Test de caso edge - empates en número de descargas.

    OBJETIVO:
    ---------
    Verificar el comportamiento cuando múltiples datasets tienen el mismo
    número de descargas.

    ESCENARIO:
    ----------
    - Tie1 y Tie2: ambos con 3 descargas en la semana anterior

    COMPORTAMIENTO ESPERADO:
    ------------------------
    - Ambos datasets deben aparecer en el resultado
    - Ambos deben mostrar downloads=3
    - El orden entre ellos puede variar (no determinista sin ORDER BY secundario)

    VALIDACIÓN:
    -----------
    ✓ Longitud de la lista = 2
    ✓ Los IDs incluyen tanto Tie1 como Tie2
    ✓ Ambos tienen downloads = 3

    NOTA TÉCNICA:
    -------------
    SQLAlchemy no garantiza un orden específico entre registros con el mismo
    COUNT sin una cláusula ORDER BY adicional (por ejemplo, por ID o título).
    """
    user = User(email="tie@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    ds1 = create_dataset_with_author("Tie1", user.id, "T1")
    ds2 = create_dataset_with_author("Tie2", user.id, "T2")
    db.session.commit()

    # place 3 downloads for each in last week
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(
        days=now.weekday()
    )
    last_week_start = start_of_week - timedelta(days=7)

    # Crear 3 descargas para cada dataset en la semana anterior
    for _ in range(3):
        db.session.add(
            DSDownloadRecord(
                dataset_id=ds1.id, download_date=last_week_start + timedelta(days=1), download_cookie=str(uuid.uuid4())
            )
        )
        db.session.add(
            DSDownloadRecord(
                dataset_id=ds2.id, download_date=last_week_start + timedelta(days=1), download_cookie=str(uuid.uuid4())
            )
        )

    db.session.commit()

    service = DataSetService()
    trending = service.trending_datasets_last_week(limit=3)

    # Validar que ambos datasets aparecen con el conteo correcto
    assert len(trending) == 2
    ids = {t["id"] for t in trending}
    assert ids == {ds1.id, ds2.id}
    for t in trending:
        assert t["downloads"] == 3


def test_api_trending_returns_json(test_client, clean_database, test_app):
    """
    WI101: Test del endpoint API /dataset/api/trending

    OBJETIVO:
    ---------
    Verificar que el endpoint REST retorna datos JSON consistentes con
    el servicio trending_datasets_last_week().

    ENDPOINT TESTEADO:
    ------------------
    GET /dataset/api/trending

    ESCENARIO:
    ----------
    - 1 dataset (API1) creado
    - 1 descarga en la semana anterior

    VALIDACIONES:
    -------------
    ✓ Status code = 200 OK
    ✓ Response es JSON válido
    ✓ Response es una lista (array)
    ✓ Contiene al menos 1 elemento
    ✓ El primer elemento tiene el ID correcto
    ✓ El contador de descargas es correcto (1)

    ESTRUCTURA JSON ESPERADA:
    -------------------------
    [
        {
            "id": <dataset_id>,
            "title": "API1",
            "main_author": "A1",
            "downloads": 1,
            "url": "http://..."
        }
    ]

    USO DEL ENDPOINT:
    -----------------
    Este endpoint permite integraciones externas o actualizaciones
    dinámicas del widget sin recargar la página completa.
    """
    user = User(email="api@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    ds1 = create_dataset_with_author("API1", user.id, "A1")
    db.session.commit()

    # add one download in last week
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(
        days=now.weekday()
    )
    last_week_start = start_of_week - timedelta(days=7)
    db.session.add(
        DSDownloadRecord(
            dataset_id=ds1.id, download_date=last_week_start + timedelta(days=1), download_cookie=str(uuid.uuid4())
        )
    )
    db.session.commit()

    # Llamar al endpoint API
    resp = test_client.get("/dataset/api/trending")

    # Validar respuesta
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == ds1.id
    assert data[0]["downloads"] == 1


def test_trending_limit_parameter(clean_database, test_app):
    """
    WI101: Test del parámetro limit en trending_datasets_last_week.

    OBJETIVO:
    ---------
    Verificar que el parámetro limit controla correctamente el número
    de resultados retornados, evitando saturar interfaces cuando hay
    muchos datasets populares.

    ESCENARIO:
    ----------
    - 5 datasets creados, cada uno con descargas decrecientes
    - DS1: 5 descargas (1º)
    - DS2: 4 descargas (2º)
    - DS3: 3 descargas (3º)
    - DS4: 2 descargas (4º)
    - DS5: 1 descarga (5º)

    VALIDACIONES CON DIFERENTES LIMITS:
    ------------------------------------
    ✓ limit=2 → retorna 2 datasets (DS1, DS2)
    ✓ limit=3 → retorna 3 datasets (DS1, DS2, DS3)
    ✓ limit=10 → retorna 5 datasets (todos)
    ✓ limit=0 → sin limitación (retorna todos)

    IMPLICACIÓN EN WIDGETS:
    ----------------------
    Los widgets de trending en el dashboard pueden controlar cuántos
    items mostrar sin preocuparse de rendimiento, independientemente
    de cuántos datasets populares existan.
    """
    user = User(email="limit@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    # Crear 5 datasets con descargas decrecientes
    datasets = []
    for i in range(1, 6):
        ds = create_dataset_with_author(f"DS{i}", user.id, f"Author{i}")
        datasets.append(ds)
    db.session.commit()

    # Calcular rango de la semana anterior
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(
        days=now.weekday()
    )
    last_week_start = start_of_week - timedelta(days=7)

    # Crear descargas: DS1=5, DS2=4, DS3=3, DS4=2, DS5=1
    for ds_idx, ds in enumerate(datasets):
        num_downloads = 5 - ds_idx
        for _ in range(num_downloads):
            db.session.add(
                DSDownloadRecord(
                    dataset_id=ds.id,
                    download_date=last_week_start + timedelta(days=1),
                    download_cookie=str(uuid.uuid4()),
                )
            )
    db.session.commit()

    service = DataSetService()

    # Validar limit=2
    trending = service.trending_datasets_last_week(limit=2)
    assert len(trending) == 2
    assert trending[0]["id"] == datasets[0].id
    assert trending[1]["id"] == datasets[1].id

    # Validar limit=3
    trending = service.trending_datasets_last_week(limit=3)
    assert len(trending) == 3
    assert trending[0]["downloads"] == 5
    assert trending[1]["downloads"] == 4
    assert trending[2]["downloads"] == 3

    # Validar limit=10 (más que existentes)
    trending = service.trending_datasets_last_week(limit=10)
    assert len(trending) == 5

    # Validar limit=None (sin límite)
    trending = service.trending_datasets_last_week(limit=None)
    assert len(trending) == 5


def test_trending_dataset_author_info(clean_database, test_app):
    """
    WI101: Test de integridad de datos de autores en trending.

    OBJETIVO:
    ---------
    Verificar que los datos del autor (nombre) se recuperan correctamente
    en los datasets de trending, y que la estructura de datos es completa
    para su visualización en el widget.

    ESCENARIO:
    ----------
    - Dataset "My Dataset" con autor "John Smith"
    - 2 descargas en la semana anterior

    VALIDACIONES:
    ---------
    ✓ El dataset aparece en trending
    ✓ El campo "title" es correcto
    ✓ El campo "main_author" es correcto
    ✓ El campo "downloads" es exacto
    ✓ El campo "url" está presente y no está vacío

    DATOS DEVUELTOS (estructura):
    ----------------------------
    {
        "id": 1,
        "title": "My Dataset",
        "main_author": "John Smith",
        "downloads": 2,
        "url": "http://localhost/doi/..."
    }

    LÓGICA CRÍTICA:
    ---------------
    - Relación dataset → metadata → author funciona correctamente
    - El método get_uvlhub_doi() genera URLs válidas
    - Los datos no son nulos ni incompletos
    """
    user = User(email="author@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    # Crear dataset con autor específico
    ds = create_dataset_with_author("My Dataset", user.id, "John Smith")
    db.session.commit()

    # Crear 2 descargas en la semana anterior
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(
        days=now.weekday()
    )
    last_week_start = start_of_week - timedelta(days=7)

    for _ in range(2):
        db.session.add(
            DSDownloadRecord(
                dataset_id=ds.id,
                download_date=last_week_start + timedelta(days=1),
                download_cookie=str(uuid.uuid4()),
            )
        )
    db.session.commit()

    service = DataSetService()
    trending = service.trending_datasets_last_week(limit=10)

    # Validar que el dataset está en trending con datos correctos
    assert len(trending) == 1
    trending_item = trending[0]

    assert trending_item["id"] == ds.id
    assert trending_item["title"] == "My Dataset"
    assert trending_item["main_author"] == "John Smith"
    assert trending_item["downloads"] == 2
    assert trending_item["url"] is not None
    assert isinstance(trending_item["url"], str)
    assert len(trending_item["url"]) > 0


def test_trending_cross_user_datasets(clean_database, test_app):
    """
    WI101: Test de trending con múltiples usuarios.

    OBJETIVO:
    ---------
    Verificar que el ranking de trending es global (agrupa datos de todos
    los usuarios) y no está segmentado por usuario individual.

    ESCENARIO:
    ----------
    - Usuario A crea Dataset A (3 descargas)
    - Usuario B crea Dataset B (5 descargas)
    - Usuario C crea Dataset C (4 descargas)

    COMPORTAMIENTO ESPERADO:
    ------------------------
    El ranking global debe ser: B (5), C (4), A (3)
    NO debe haber datasets filtrados por usuario.

    IMPLICACIÓN EN EL WIDGET:
    -------------------------
    El widget de trending muestra los mejores datasets de toda la plataforma,
    independientemente de quién sea el propietario, para maximizar discoverability.

    VALIDACIONES:
    ✓ Dataset B aparece primero (5 descargas)
    ✓ Dataset C aparece segundo (4 descargas)
    ✓ Dataset A aparece tercero (3 descargas)
    ✓ Se respeta el orden global sin segmentación por usuario
    """
    # Crear 3 usuarios distintos
    user_a = User(email="user_a@example.com", password="pass")
    user_b = User(email="user_b@example.com", password="pass")
    user_c = User(email="user_c@example.com", password="pass")
    db.session.add_all([user_a, user_b, user_c])
    db.session.commit()

    # Crear datasets de cada usuario
    ds_a = create_dataset_with_author("Dataset A", user_a.id, "Author A")
    ds_b = create_dataset_with_author("Dataset B", user_b.id, "Author B")
    ds_c = create_dataset_with_author("Dataset C", user_c.id, "Author C")
    db.session.commit()

    # Calcular rango de la semana anterior
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(
        days=now.weekday()
    )
    last_week_start = start_of_week - timedelta(days=7)

    # Crear descargas: A=3, B=5 (ganador), C=4
    for _ in range(3):
        db.session.add(
            DSDownloadRecord(
                dataset_id=ds_a.id,
                download_date=last_week_start + timedelta(days=1),
                download_cookie=str(uuid.uuid4()),
            )
        )

    for _ in range(5):
        db.session.add(
            DSDownloadRecord(
                dataset_id=ds_b.id,
                download_date=last_week_start + timedelta(days=2),
                download_cookie=str(uuid.uuid4()),
            )
        )

    for _ in range(4):
        db.session.add(
            DSDownloadRecord(
                dataset_id=ds_c.id,
                download_date=last_week_start + timedelta(days=3),
                download_cookie=str(uuid.uuid4()),
            )
        )

    db.session.commit()

    service = DataSetService()
    trending = service.trending_datasets_last_week(limit=10)

    # Validar el orden global: B (5) > C (4) > A (3)
    assert len(trending) == 3
    assert trending[0]["id"] == ds_b.id
    assert trending[0]["downloads"] == 5
    assert trending[1]["id"] == ds_c.id
    assert trending[1]["downloads"] == 4
    assert trending[2]["id"] == ds_a.id
    assert trending[2]["downloads"] == 3
