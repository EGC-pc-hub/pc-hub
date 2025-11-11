import logging

from flask import render_template

from app.modules.dataset.services import DataSetService
from app.modules.featuremodel.services import FeatureModelService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    """
    WI101: Ruta principal que muestra la página de inicio con trending datasets.

    MODIFICACIONES REALIZADAS:
    ---------------------------
    Se añadió la llamada a dataset_service.trending_datasets_last_week() para
    obtener los datasets más descargados de la semana anterior.

    DATOS PASADOS AL TEMPLATE:
    ---------------------------
    - datasets: Últimos datasets sincronizados (existente)
    - trending_datasets: Top 3 datasets más descargados la semana pasada (NUEVO)
    - datasets_counter: Total de datasets sincronizados (existente)
    - feature_models_counter: Total de feature models (existente)
    - total_dataset_downloads: Total de descargas de datasets (existente)
    - total_feature_model_downloads: Total de descargas de feature models (existente)
    - total_dataset_views: Total de vistas de datasets (existente)
    - total_feature_model_views: Total de vistas de feature models (existente)

    INTEGRACIÓN CON EL WIDGET:
    ---------------------------
    La variable trending_datasets se pasa al template index.html, donde
    se renderiza en el widget de la sidebar derecha.
    """
    logger.info("Access index")
    dataset_service = DataSetService()
    feature_model_service = FeatureModelService()

    # Statistics: total datasets and feature models
    datasets_counter = dataset_service.count_synchronized_datasets()
    feature_models_counter = feature_model_service.count_feature_models()

    # Statistics: total downloads
    total_dataset_downloads = dataset_service.total_dataset_downloads()
    total_feature_model_downloads = feature_model_service.total_feature_model_downloads()

    # Statistics: total views
    total_dataset_views = dataset_service.total_dataset_views()
    total_feature_model_views = feature_model_service.total_feature_model_views()

    # WI101: Trending datasets - top downloads last week
    trending_datasets = dataset_service.trending_datasets_last_week()

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        trending_datasets=trending_datasets,
        datasets_counter=datasets_counter,
        feature_models_counter=feature_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_feature_model_downloads=total_feature_model_downloads,
        total_dataset_views=total_dataset_views,
        total_feature_model_views=total_feature_model_views,
    )
