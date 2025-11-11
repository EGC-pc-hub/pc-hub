import hashlib
import os
from copy import deepcopy
from typing import Dict, Tuple

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("fakenodo_api", __name__)


def _state():
    """Devuelve el estado en memoria del servicio.

    Estructura de datos:
    {
      "next_id": int,                       # Siguiente ID a asignar para un depósito
      "depositions": {
         <id>: {
            "id": int,
            "conceptrecid": int,           # Identificador de la familia de versiones (constante por depósito)
            "metadata": dict,              # Metadatos del borrador/depósito
            "files": { nombre: checksum }, # Ficheros del borrador con su checksum
            "published_versions": [        # Historial de publicaciones (snapshot de ficheros)
                { "version": int, "doi": str, "files_snapshot": { nombre: checksum } }
            ],
            "state": "draft"|"published",
            "doi": str|None               # DOI de la última publicación (si existe)
         }
      }
    }
    """
    return current_app.config["FAKENODO_STATE"]


def _compute_checksum(file_bytes: bytes) -> str:
    # Calcula un hash simple (MD5) del contenido del archivo para detectar cambios

    return hashlib.md5(file_bytes).hexdigest()


def _files_equal(a: Dict[str, str], b: Dict[str, str]) -> bool:
    # Compara snapshots de ficheros (nombre -> checksum)
    # Si son iguales, consideramos que no hay cambios de ficheros y, por tanto,
    # publicar de nuevo NO debería generar nueva versión/DOI.
    return a == b


def _ensure_dep(deposition_id: int) -> Tuple[dict, int]:
    # Obtiene un depósito existente o devuelve 404 si no existe
    dep = _state()["depositions"].get(deposition_id)
    if not dep:
        return None, 404
    return dep, 200


@bp.get("/deposit/depositions")
def list_depositions():
    # Lista todos los depósitos almacenados en memoria
    deps = list(_state()["depositions"].values())
    return jsonify(deps), 200


@bp.post("/deposit/depositions")
def create_deposition():
    # Crea un nuevo depósito en estado borrador (draft)

    payload = request.get_json(silent=True) or {}
    metadata = payload.get("metadata", {})

    # ID autoincremental para el nuevo depósito
    new_id = _state()["next_id"]
    _state()["next_id"] += 1

    deposition = {
        "id": new_id,
        "conceptrecid": new_id,
        "metadata": metadata,
        "files": {},
        "published_versions": [],
        "state": "draft",
        "doi": None,
    }
    _state()["depositions"][new_id] = deposition
    return jsonify(deposition), 201


@bp.get("/deposit/depositions/<int:deposition_id>")
def get_deposition(deposition_id: int):
    # Obtiene un depósito por ID (404 si no existe)
    dep, code = _ensure_dep(deposition_id)
    if code != 200:
        return jsonify({"message": "Not found"}), code
    return jsonify(dep), 200


@bp.put("/deposit/depositions/<int:deposition_id>")
def update_deposition(deposition_id: int):
    # Actualiza SOLO los metadatos del depósito para no crear nuevo DOI al publicar.

    dep, code = _ensure_dep(deposition_id)
    if code != 200:
        return jsonify({"message": "Not found"}), code
    payload = request.get_json(silent=True) or {}
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        dep["metadata"] = metadata
    return jsonify(dep), 200


@bp.delete("/deposit/depositions/<int:deposition_id>")
def delete_deposition(deposition_id: int):
    # Elimina un depósito por ID (idempotente: 404 si no existe)
    dep, code = _ensure_dep(deposition_id)
    if code != 200:
        return jsonify({"message": "Not found"}), code
    del _state()["depositions"][deposition_id]
    return "", 204


@bp.post("/deposit/depositions/<int:deposition_id>/files")
def upload_file(deposition_id: int):
    # Sube o actualiza un fichero en el borrador del depósito

    dep, code = _ensure_dep(deposition_id)
    if code != 200:
        return jsonify({"message": "Not found"}), code

    # El nombre puede venir en 'name' o usar file.filename
    name = request.form.get("name")
    file = request.files.get("file")

    # Camino normal: viene un fichero real en multipart/form-data
    if file:
        file_bytes = file.read()
        checksum = _compute_checksum(file_bytes)
        filename = name or getattr(file, "filename", None) or "uploaded"
        dep["files"][filename] = checksum
    else:
        # Fallback de robustez: aceptar una ruta local enviada como texto
        # (útil cuando algunas herramientas no adjuntan correctamente el "file" en multipart).
        # Se aceptan claves: filepath | src | file (texto)
        filepath = request.form.get("filepath") or request.form.get("src") or request.form.get("file")
        if not filepath:
            return jsonify({"message": "No file provided"}), 400
        try:
            with open(filepath, "rb") as fh:
                file_bytes = fh.read()
            checksum = _compute_checksum(file_bytes)
            filename = name or os.path.basename(filepath) or "uploaded"
            dep["files"][filename] = checksum
        except Exception as exc:
            return (
                jsonify(
                    {
                        "message": "No file provided",
                        "detail": str(exc),
                    }
                ),
                400,
            )

    return (
        jsonify(
            {
                "filename": filename,
                "checksum": checksum,
                "deposition_id": deposition_id,
            }
        ),
        201,
    )


@bp.post("/deposit/depositions/<int:deposition_id>/actions/publish")
def publish_deposition(deposition_id: int):
    # Publica el depósito
    dep, code = _ensure_dep(deposition_id)
    if code != 200:
        return jsonify({"message": "Not found"}), code

    current_files = deepcopy(dep["files"])
    versions = dep["published_versions"]

    if not versions:
        # Primera publicación -> genera DOI v1
        version_num = 1
        doi = f"10.9999/fakenodo.{dep['conceptrecid']}.v{version_num}"
        versions.append({"version": version_num, "doi": doi, "files_snapshot": current_files})
        dep["doi"] = doi
        dep["state"] = "published"
        return jsonify(dep), 202

    last = versions[-1]
    if _files_equal(last["files_snapshot"], current_files):
        # Sin cambios de ficheros -> mantener DOI/versión
        dep["doi"] = last["doi"]
        dep["state"] = "published"
        return jsonify(dep), 202

    # Con cambios de ficheros -> nueva versión y nuevo DOI
    version_num = last["version"] + 1
    doi = f"10.9999/fakenodo.{dep['conceptrecid']}.v{version_num}"
    versions.append({"version": version_num, "doi": doi, "files_snapshot": current_files})
    dep["doi"] = doi
    dep["state"] = "published"
    return jsonify(dep), 202


@bp.get("/records/<int:conceptrecid>/versions")
def list_versions(conceptrecid: int):
    # Lista las versiones publicadas para una familia (conceptrecid)
    # En este fake, conceptrecid coincide con el id del depósito base

    for dep in _state()["depositions"].values():
        if dep["conceptrecid"] == conceptrecid:
            hits = [
                {"version": v["version"], "doi": v["doi"], "metadata": dep.get("metadata", {})}
                for v in dep["published_versions"]
            ]
            return jsonify({"hits": {"hits": hits, "total": len(hits)}}), 200
    return jsonify({"hits": {"hits": [], "total": 0}}), 200
