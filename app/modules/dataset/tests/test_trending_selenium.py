"""
Test de Selenium para validar el widget de "Trending Datasets (last week)"

HOJA DE RUTA - IMPLEMENTACIÓN FEATURE WI101: Trending Datasets
================================================================

CONTEXTO:
---------
Este test forma parte de la implementación de la funcionalidad de datasets trending
(datasets más descargados en la última semana) para la plataforma uvlhub.io.

CAMBIOS IMPLEMENTADOS EN ESTA RAMA (feature-wi101-trending-datasets):
---------------------------------------------------------------------

1. BACKEND - Servicio de trending datasets:
   - Creación de lógica para calcular datasets más descargados en la última semana
   - Consulta a la base de datos filtrando registros de descarga (DSDownloadRecord)
   - Ordenamiento por número de descargas descendente
   - Limitación a top 3 datasets

2. FRONTEND - Widget de visualización:
   - Creación de componente HTML para mostrar trending datasets
   - Diseño responsive con información de autor y número de descargas
   - Integración en la página principal (index)
   - Manejo de estado vacío (cuando no hay datos de trending)

3. TESTING - Validación con Selenium:
   - Test end-to-end que verifica toda la funcionalidad
   - Preparación de datos de prueba en base de datos
   - Verificación de correcta visualización en interfaz
   - Validación de orden correcto por número de descargas

ADAPTACIONES PARA WSL:
----------------------
Dado que el desarrollo se realiza en entorno WSL (Windows Subsystem for Linux),
se implementaron las siguientes adaptaciones:

- Instalación de Firefox en WSL (apt install firefox)
- Instalación de dependencias gráficas necesarias (libasound2t64, libgtk-3-0t64, etc.)
- Configuración de Firefox en modo headless (sin interfaz gráfica)
- Creación de directorio temporal compatible con la estructura esperada por common.py
- Uso de webdriver-manager para gestión automática de geckodriver

RESULTADO DEL TEST:
-------------------
El test valida exitosamente que:
✓ Los datasets con más descargas en la última semana aparecen en el widget
✓ El orden es correcto (descendente por número de descargas)
✓ Los números de descargas mostrados son precisos
✓ El widget se renderiza correctamente en la página principal

La captura de pantalla generada (/tmp/trending_test.png) muestra:
- Widget "Trending datasets (last week)" visible en la sidebar
- DS One con 5 downloads (creadas en el test)
- DS Two con 3 downloads (creadas en el test)
- DS Three con 2 downloads (creadas en el test)
- Información de autores correctamente mostrada
"""

import time
import uuid
from datetime import datetime, timedelta, timezone

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from app import app, db
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSDownloadRecord, DSMetaData, PublicationType
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver


def initialize_driver_wsl():
    """
    Inicializa el driver de Firefox configurado para WSL.

    CONFIGURACIÓN PARA WSL:
    - Modo headless: Firefox se ejecuta sin interfaz gráfica (necesario en WSL sin X11)
    - TMPDIR: Se crea el directorio ~/snap/firefox/common/tmp que espera common.py
    - GeckoDriver: Se descarga automáticamente mediante webdriver-manager

    Esta función fue creada específicamente para este test debido a las limitaciones
    de WSL con aplicaciones gráficas. En un entorno nativo de Linux/Ubuntu, se usaría
    directamente la función initialize_driver() de core.selenium.common.

    Returns:
        WebDriver: Instancia de Firefox WebDriver configurada para WSL
    """
    import os

    options = webdriver.FirefoxOptions()
    # Modo headless: confiable y rápido en WSL
    options.add_argument("--headless")

    # Configurar TMPDIR para WSL (sin snap, que no existe en WSL)
    os.environ.setdefault("TMPDIR", "/tmp")

    # Crear directorio temporal que espera common.py (aunque no usemos snap)
    snap_tmp = os.path.expanduser("~/snap/firefox/common/tmp")
    os.makedirs(snap_tmp, exist_ok=True)
    os.environ["TMPDIR"] = snap_tmp

    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def create_dataset_with_author(title, user_id, author_name):
    dsmeta = DSMetaData(title=title, description="desc", publication_type=PublicationType.NONE)
    author = Author(name=author_name)
    dsmeta.authors.append(author)
    dataset = DataSet(user_id=user_id, ds_meta_data=dsmeta)
    db.session.add(dsmeta)
    db.session.add(dataset)
    db.session.flush()
    return dataset


def create_download(dataset_id, days_ago=0):
    download = DSDownloadRecord(
        dataset_id=dataset_id,
        download_date=datetime.now(timezone.utc) - timedelta(days=days_ago),
        download_cookie=str(uuid.uuid4()),
    )
    db.session.add(download)


def test_trending_selenium():
    """Seed DB with downloads in last week and assert the trending widget on the public index."""

    # Seed the DB so the public index shows trending datasets
    with app.app_context():
        # Clean up ALL download records first to avoid interference from previous tests/data
        # This ensures only our test data affects the trending calculation
        DSDownloadRecord.query.delete()
        db.session.commit()

        # Get or create user
        user = User.query.filter_by(email="selenium_trending@example.com").first()
        if user is None:
            user = User(email="selenium_trending@example.com", password="pass")
            db.session.add(user)
            db.session.commit()
        else:
            # Clean up existing datasets for this user
            existing_datasets = DataSet.query.filter_by(user_id=user.id).all()

            # Delete datasets and their metadata
            for ds in existing_datasets:
                metadata_id = ds.ds_meta_data_id
                db.session.delete(ds)
                if metadata_id:
                    metadata = DSMetaData.query.get(metadata_id)
                    if metadata:
                        db.session.delete(metadata)

            db.session.commit()

        # create datasets
        ds1 = create_dataset_with_author("DS One", user.id, "Author One")
        ds2 = create_dataset_with_author("DS Two", user.id, "Author Two")
        ds3 = create_dataset_with_author("DS Three", user.id, "Author Three")
        ds4 = create_dataset_with_author("DS Old", user.id, "Author Old")

        db.session.commit()

        # compute last week start (same logic as the service)
        now = datetime.now(timezone.utc)
        start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(
            days=now.weekday()
        )
        last_week_start = start_of_week - timedelta(days=7)

        # place records on last_week_start + 1, +2, +3 days
        for _ in range(5):
            db.session.add(
                DSDownloadRecord(
                    dataset_id=ds1.id,
                    download_date=last_week_start + timedelta(days=1),
                    download_cookie=str(uuid.uuid4()),
                )
            )
        for _ in range(3):
            db.session.add(
                DSDownloadRecord(
                    dataset_id=ds2.id,
                    download_date=last_week_start + timedelta(days=2),
                    download_cookie=str(uuid.uuid4()),
                )
            )
        for _ in range(2):
            db.session.add(
                DSDownloadRecord(
                    dataset_id=ds3.id,
                    download_date=last_week_start + timedelta(days=3),
                    download_cookie=str(uuid.uuid4()),
                )
            )
        # ds4 older than last week
        for _ in range(10):
            db.session.add(
                DSDownloadRecord(
                    dataset_id=ds4.id,
                    download_date=last_week_start - timedelta(days=10),
                    download_cookie=str(uuid.uuid4()),
                )
            )

        db.session.commit()

        # Store dataset IDs before leaving the app context
        ds1_id = ds1.id
        ds2_id = ds2.id
        ds3_id = ds3.id

    # Now open the public index page and verify the trending widget
    driver = initialize_driver_wsl()

    try:
        host = get_host_for_selenium_testing()

        # Open the index page
        driver.get(f"{host}/")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(3)

        # Tomar captura de pantalla para ver qué muestra la página
        driver.save_screenshot("/tmp/trending_test.png")
        print("\n📸 Captura guardada en: /tmp/trending_test.png")

        try:
            # list items under #trending-list
            items = driver.find_elements(By.CSS_SELECTOR, "#trending-list li")

            if not items:
                # If the container is present but empty the page shows an #trending-empty element
                empty = driver.find_element(By.ID, "trending-empty")
                raise AssertionError(f"Expected trending items but found empty message: '{empty.text}'")

            # Expect top 3 items in order: ds1 (5), ds2 (3), ds3 (2)
            expected = [str(ds1_id), str(ds2_id), str(ds3_id)]
            if len(items) < 3:
                raise AssertionError(f"Expected at least 3 trending items, found {len(items)}")

            # check the first three items
            expected_counts = [5, 3, 2]
            for idx in range(3):
                li = items[idx]
                dsid = li.get_attribute("data-dsid")
                if dsid != expected[idx]:
                    raise AssertionError(f"Expected dataset id {expected[idx]} at position {idx}, found {dsid}")

                # downloads count
                downloads_el = li.find_element(By.CLASS_NAME, "trending-downloads")
                downloads_text = downloads_el.text.strip()
                # Convert to int
                try:
                    downloads_num = int(downloads_text)
                except ValueError:
                    raise AssertionError(f"Downloads number is not an integer: '{downloads_text}'")

                if downloads_num != expected_counts[idx]:
                    raise AssertionError(
                        f"Expected {expected_counts[idx]} downloads for ds {expected[idx]}, found {downloads_num}"
                    )

        except NoSuchElementException as exc:
            raise AssertionError(f"Test failed, missing element: {exc}")

    finally:

        # Close the browser
        close_driver(driver)


# Allow running the test directly (the rosemary selenium command expects a module that runs when executed)
if __name__ == "__main__":
    test_trending_selenium()
