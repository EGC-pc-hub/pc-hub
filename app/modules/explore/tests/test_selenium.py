"""
Test de Selenium para validar la funcionalidad de Advanced Search en el módulo Explore

Este test valida la funcionalidad de búsqueda avanzada implementada que permite
buscar datasets usando filtros individuales por autor, título, tags, fecha y tipo de publicación.
"""

import os
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

from app import app, db
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData, FMMetrics
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver


def initialize_driver_wsl():
    """Inicializa el driver de Firefox configurado para WSL."""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")

    os.environ.setdefault("TMPDIR", "/tmp")
    snap_tmp = os.path.expanduser("~/snap/firefox/common/tmp")
    os.makedirs(snap_tmp, exist_ok=True)
    os.environ["TMPDIR"] = snap_tmp

    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def create_test_dataset(user_id, title, description, pub_type, tags, author_name, days_ago=0):
    """Helper para crear un dataset de prueba"""
    ds_metrics = DSMetrics(number_of_models="5", number_of_features="20")
    db.session.add(ds_metrics)
    db.session.flush()

    ds_meta = DSMetaData(
        title=title,
        description=description,
        publication_type=pub_type,
        publication_doi=f"10.1234/{title.lower().replace(' ', '-')}",
        dataset_doi=f"10.1234/dataset-{title.lower().replace(' ', '-')}",
        tags=tags,
        ds_metrics_id=ds_metrics.id,
    )
    db.session.add(ds_meta)
    db.session.flush()

    author = Author(name=author_name, affiliation="Test University", ds_meta_data_id=ds_meta.id)
    db.session.add(author)

    dataset = DataSet(user_id=user_id, ds_meta_data_id=ds_meta.id, created_at=datetime.now() - timedelta(days=days_ago))
    db.session.add(dataset)
    db.session.flush()

    # Add feature model
    fm_metrics = FMMetrics(solver="PySAT", not_solver=None)
    db.session.add(fm_metrics)
    db.session.flush()

    fm_meta = FMMetaData(
        uvl_filename=f"{title.lower()}.uvl",
        title=f"{title} Model",
        description=f"Model for {title}",
        publication_type=pub_type,
        publication_doi=f"10.1234/{title.lower().replace(' ', '-')}",
        tags=tags,
        fm_metrics_id=fm_metrics.id,
    )
    db.session.add(fm_meta)
    db.session.flush()

    fm = FeatureModel(data_set_id=dataset.id, fm_meta_data_id=fm_meta.id)
    db.session.add(fm)

    return dataset


def test_advanced_search_selenium():
    """
    Test completo de la funcionalidad de búsqueda avanzada.
    Valida todos los filtros en una sola ejecución.
    """

    # Preparar datos de prueba
    with app.app_context():
        # No limpiamos todo, solo nos aseguramos de que el usuario de prueba existe
        # Los datos de prueba se identificarán por nombres específicos

        # Obtener o crear usuario
        user = User.query.filter_by(email="selenium_explore@example.com").first()
        if user is None:
            user = User(email="selenium_explore@example.com", password="pass")
            db.session.add(user)
            db.session.commit()

        # Crear datasets de prueba con diferentes características
        ds1 = create_test_dataset(  # noqa: F841
            user.id,
            "Machine Learning Framework",
            "ML framework for data science",
            PublicationType.SOFTWARE,
            "machine learning, AI, python",
            "John Smith",
            days_ago=5,
        )

        ds2 = create_test_dataset(  # noqa: F841
            user.id,
            "IoT Sensor Network",
            "Hardware specifications for IoT",
            PublicationType.HARDWARE,
            "IoT, sensors, hardware",
            "Jane Doe",
            days_ago=30,
        )

        ds3 = create_test_dataset(  # noqa: F841
            user.id,
            "Web Development Framework",
            "Modern web framework",
            PublicationType.SOFTWARE,
            "web, javascript, framework",
            "John Smith",
            days_ago=10,
        )

        db.session.commit()

    # Inicializar driver
    driver = initialize_driver_wsl()

    try:
        host = get_host_for_selenium_testing()

        print("\n🧪 TEST 1: Verificar que el botón de búsqueda avanzada existe y funciona")
        driver.get(f"{host}/explore")
        wait_for_page_to_load(driver)
        time.sleep(2)

        # Captura inicial
        driver.save_screenshot("/tmp/explore_test_initial.png")
        print("📸 Captura inicial guardada: /tmp/explore_test_initial.png")

        # Encontrar y verificar botón de búsqueda avanzada
        advanced_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "toggle-advanced-search"))
        )
        assert advanced_button is not None, "Botón de búsqueda avanzada no encontrado"
        print("✅ Botón de búsqueda avanzada encontrado")

        # Verificar panel inicialmente oculto
        advanced_panel = driver.find_element(By.ID, "advanced-search-panel")
        assert advanced_panel.value_of_css_property("display") == "none", "Panel debería estar oculto"
        print("✅ Panel inicialmente oculto")

        # Abrir panel
        advanced_button.click()
        time.sleep(1)
        assert advanced_panel.value_of_css_property("display") == "block", "Panel debería estar visible"
        print("✅ Panel se abre correctamente")

        driver.save_screenshot("/tmp/explore_test_panel_open.png")
        print("📸 Panel abierto: /tmp/explore_test_panel_open.png")

        print("\n🧪 TEST 2: Filtrar por título")
        title_filter = driver.find_element(By.ID, "filter_title")
        title_filter.clear()
        title_filter.send_keys("Machine Learning")
        time.sleep(2)

        results = driver.find_elements(By.CSS_SELECTOR, "#results .card")
        assert len(results) > 0, "Debería haber resultados"
        print(f"✅ Filtro por título: {len(results)} resultado(s) encontrado(s)")

        driver.save_screenshot("/tmp/explore_test_title_filter.png")

        print("\n🧪 TEST 3: Filtrar por autor")
        # Limpiar filtro anterior
        title_filter.clear()
        time.sleep(1)

        author_filter = driver.find_element(By.ID, "filter_author")
        author_filter.send_keys("John Smith")
        time.sleep(2)

        results = driver.find_elements(By.CSS_SELECTOR, "#results .card")
        assert len(results) >= 2, f"Debería haber al menos 2 resultados de John Smith, encontrados: {len(results)}"
        print(f"✅ Filtro por autor: {len(results)} resultado(s) encontrado(s)")

        driver.save_screenshot("/tmp/explore_test_author_filter.png")

        print("\n🧪 TEST 4: Filtrar por tipo de publicación")
        # Limpiar filtros anteriores
        author_filter.clear()
        time.sleep(1)

        pub_type_filter = Select(driver.find_element(By.ID, "filter_publication_type"))
        pub_type_filter.select_by_value("hardware")
        time.sleep(2)

        results = driver.find_elements(By.CSS_SELECTOR, "#results .card")
        assert len(results) >= 1, "Debería haber al menos 1 resultado de hardware"
        print(f"✅ Filtro por tipo de publicación: {len(results)} resultado(s) encontrado(s)")

        driver.save_screenshot("/tmp/explore_test_pubtype_filter.png")

        print("\n🧪 TEST 5: Filtrar por rango de fechas")
        # Limpiar filtros anteriores
        pub_type_filter.select_by_value("any")
        time.sleep(1)

        date_from = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")

        date_from_field = driver.find_element(By.ID, "filter_date_from")
        date_to_field = driver.find_element(By.ID, "filter_date_to")

        date_from_field.send_keys(date_from)
        date_to_field.send_keys(date_to)
        time.sleep(2)

        results = driver.find_elements(By.CSS_SELECTOR, "#results .card")
        assert len(results) >= 2, f"Debería haber 2 resultados en el rango de fechas, encontrados: {len(results)}"
        print(f"✅ Filtro por rango de fechas: {len(results)} resultado(s) encontrado(s)")

        driver.save_screenshot("/tmp/explore_test_date_filter.png")

        print("\n🧪 TEST 6: Verificar botón de limpiar filtros")
        clear_button = driver.find_element(By.ID, "clear-filters")
        clear_button.click()
        time.sleep(1)

        # Verificar que los campos se limpiaron
        title_filter = driver.find_element(By.ID, "filter_title")
        author_filter = driver.find_element(By.ID, "filter_author")
        assert title_filter.get_attribute("value") == "", "Campo título debería estar vacío"
        assert author_filter.get_attribute("value") == "", "Campo autor debería estar vacío"
        print("✅ Botón limpiar filtros funciona correctamente")

        driver.save_screenshot("/tmp/explore_test_cleared.png")

        print("\n✅ TODOS LOS TESTS PASARON EXITOSAMENTE")

    finally:
        close_driver(driver)


# Permitir ejecutar el test directamente
if __name__ == "__main__":
    test_advanced_search_selenium()
