import os

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    # Almacenamiento simple en memoria para depósitos de datos.
    # Estructura:
    # depositions = {
    #   id: {
    #       'id': int,
    #       'conceptrecid': int,
    #       'metadata': dict,
    #       'files': {filename: checksum(str)},
    #       'published_versions': [
    #           {
    #               'version': int,
    #               'doi': str,
    #               'files_snapshot': {filename: checksum}
    #           }
    #       ]
    #   }
    # }
    app.config.setdefault("FAKENODO_STATE", {"next_id": 1, "depositions": {}})

    from .routes import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/")
    def index():
        return {"service": "fakenodo", "status": "ok"}

    return app
