import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile

from flask import (
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask import session
from flask_login import current_user, login_required
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import DSDownloadRecord
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
    GitHubRepoService,
    GitHubContentService,
)
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each feature model (one feature model = one request to Zenodo)
                for feature_model in dataset.feature_models:
                    zenodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".uvl"):
        return jsonify({"message": "No valid file"}), 400

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){extension}")):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return (
        jsonify(
            {
                "message": "UVL uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())  # Generate a new unique identifier if it does not exist
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Check if the download record already exists for this cookie
    existing_record = DSDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie,
    ).first()

    if not existing_record:
        # Record the download in your database
        DSDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    return render_template("dataset/view_dataset.html", dataset=dataset)


@dataset_bp.route("/dataset/<int:dataset_id>/backup/authorised-user", methods=["GET"])
@login_required
def backup_dataset_can(dataset_id):
    # Comprueba si el usuario actual está autorizado para hacer backup del dataset,
    # es decir, si el dataset pertenece al usuario actual
    dataset = dataset_service.get_or_404(dataset_id)
    if current_user.id != dataset.user_id:
        return jsonify({"error": "Not authorized to back up this dataset."}), 403
    return jsonify({"can_backup": True}), 200


@dataset_bp.route("/dataset/<int:dataset_id>/backup/github", methods=["POST"])
@login_required
def backup_dataset_to_github(dataset_id):
    # Crea el repo y sube los archivos en caso de que ya se esté autenticado con GitHub
    dataset = dataset_service.get_or_404(dataset_id)
    # Vuelve a comprobar si el usuario actual está autorizado para hacer backup del dataset por si acaso
    if current_user.id != dataset.user_id:
        return jsonify({"error": "Not authorized"}), 403

    try:
        token = session.get("github_token")
        # En este punto debería estar ya autenticado con GitHub
        # Lo comprobamos de nuevo por si acaso
        if not token:
            return jsonify({"error": "Not authenticated with GitHub"}), 401

        title = dataset.ds_meta_data.title or f"dataset-{dataset.id}"
        from app.modules.dataset.services import repo_name_formatting

        # Creamos el repo con el nombre formateado
        repo_name = repo_name_formatting(title)
        repo_service = GitHubRepoService(token=token)
        repo_info = repo_service.create_repo(
            name=repo_name, private=True, description=f"Backup for dataset {dataset.id}"
        )

        full_name = repo_info.get("full_name")
        html_url = repo_info.get("html_url")
        default_branch = repo_info.get("default_branch", "main")

        content_service = GitHubContentService(token=token, repo_full_name=full_name, branch=default_branch)
        result = content_service.upload_dataset(dataset, prefix="")

        return (
            jsonify(
                {
                    "message": "Backup completed",
                    "repo": full_name,
                    "url": html_url,
                    "uploaded": result.get("uploaded", 0),
                }
            ),
            200,
        )
    except Exception as exc:
        logger.exception(f"GitHub backup failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@dataset_bp.route("/dataset/<int:dataset_id>/backup/github-ui", methods=["GET"])
@login_required
def backup_dataset_github_ui(dataset_id):
    # Crear el repo y subir los archivos en el caso de que se abra el popup de GitHub
    dataset = dataset_service.get_or_404(dataset_id)
    if current_user.id != dataset.user_id:
        return abort(403)

    token = session.get("github_token")
    if not token:
        next_url = url_for(
            "dataset.backup_dataset_github_ui",
            dataset_id=dataset_id,
            return_url=request.args.get("return", request.path),
            popup=request.args.get("popup"),
        )
        return redirect(url_for("auth.github_login", next=next_url))

    try:
        title = dataset.ds_meta_data.title or f"dataset-{dataset.id}"
        from app.modules.dataset.services import repo_name_formatting

        repo_name = repo_name_formatting(title)
        repo_service = GitHubRepoService(token=token)
        repo_info = repo_service.create_repo(
            name=repo_name, private=True, description=f"Backup for dataset {dataset.id}"
        )
        full_name = repo_info.get("full_name")
        html_url = repo_info.get("html_url")
        default_branch = repo_info.get("default_branch", "main")

        content_service = GitHubContentService(token=token, repo_full_name=full_name, branch=default_branch)
        result = content_service.upload_dataset(dataset)

        return_url = request.args.get("return") or request.args.get("return_url")
        if return_url:
            # Si se abrió en popup, notificar al opener y cerrar
            if request.args.get("popup") == "1":
                payload = {
                    "type": "github-backup-done",
                    "repo": full_name or "",
                    "url": html_url or "",
                    "uploaded": (result or {}).get("uploaded", 0),
                }
                html = f"""
                <!DOCTYPE html>
                <html lang='en'>
                <head><meta charset='utf-8'><title>Backup completed</title></head>
                <body>
                <p>Backup completed. You can close this window.</p>
                <script>
                (function() {{
                    var data = {json.dumps(payload)};
                    try {{
                        if (window.opener && window.opener.location
                            && window.opener.location.origin === window.location.origin) {{
                            window.opener.postMessage(data, window.location.origin);
                        }}
                    }} catch (e) {{}}
                    window.close();
                }})();
                </script>
                </body>
                </html>
                """
                return html
            # Si no, añade los parámetros UX a la URL de retorno y redirige
            split = urlsplit(return_url)
            q = dict(parse_qsl(split.query))
            q.update(
                {
                    "backup": "done",
                    "repo": full_name or "",
                    "url": html_url or "",
                    "uploaded": str((result or {}).get("uploaded", 0)),
                }
            )
            new_return = urlunsplit((split.scheme, split.netloc, split.path, urlencode(q), split.fragment))
            return redirect(new_return)
        # Si no hay URL de retorno, mostrar un mensaje simple
        return f"Backup completed: <a href='{html_url}' target='_blank'>{html_url}</a>"
    except Exception as exc:
        logger.exception(f"GitHub UI backup failed: {exc}")
        return f"Error: {exc}", 400
