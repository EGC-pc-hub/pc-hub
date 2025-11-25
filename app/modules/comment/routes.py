from flask import abort, jsonify, render_template, request
from flask_login import current_user, login_required

from app.modules.comment import comment_bp
from app.modules.comment.forms import CommentForm
from app.modules.comment.services import CommentService

comment_service = CommentService()


@comment_bp.route("/comment", methods=["GET"])
@login_required
def index():
    return render_template("comment/index.html")


@comment_bp.route("/comment/dataset/<int:dataset_id>", methods=["GET"])
@login_required
def index_by_dataset(dataset_id):

    return render_template("comment/index.html", dataset_id=dataset_id, filter_by="dataset")


@comment_bp.route("/comment/parent/<int:parent_id>", methods=["GET"])
def index_by_parent(parent_id):
    """Show a page for a parent comment: reply UI (if logged in) and list of replies.

    This view is accessible to anonymous users; reply/create actions still require login.
    """
    parent = comment_service.get_by_id(parent_id)
    if not parent:
        abort(404)

    # Determine owner of the dataset to control visibility of hidden replies
    dataset = getattr(parent, "dataset", None)
    is_owner = False
    if dataset and getattr(dataset, "user_id", None) is not None:
        is_owner = current_user.is_authenticated and (current_user.id == dataset.user_id)

    # If the parent comment is hidden and the visitor is not the dataset owner, deny access
    if not getattr(parent, "visible", True) and not is_owner:
        abort(403)

    # Get replies and apply visibility filter for anonymous/non-owner users
    replies = comment_service.get_comments_by_parent(parent_id) or []
    if not is_owner:
        replies = [r for r in replies if getattr(r, "visible", True)]

    return render_template(
        "comment/index.html",
        parent=parent,
        replies=replies,
        dataset=dataset,
        is_owner=is_owner,
        filter_by="parent",
    )


@comment_bp.route("/comment/dataset/<int:dataset_id>/create", methods=["POST"])
@login_required
def create_comment_for_dataset(dataset_id):
    """Crear un comentario para un dataset.

    Acepta JSON {"content": "..."} o formulario con campo `content`.
    Devuelve el comentario creado en JSON.
    """
    # Try JSON first
    content = None
    if request.is_json:
        data = request.get_json() or {}
        content = data.get("content")

    # Fallback to form (Flask-WTF)
    if content is None:
        form = CommentForm()
        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400
        content = form.content.data

    if not content or not content.strip():
        return jsonify({"message": "Content is required"}), 400

    try:
        comment = comment_service.create(
            user_id=current_user.id,
            dataset_id=dataset_id,
            parent_id=None,
            content=content.strip(),
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return (
        jsonify(
            {
                "success": True,
                "comment": {
                    "id": comment.id,
                    "user_id": comment.user_id,
                    "dataset_id": comment.dataset_id,
                    "parent_id": comment.parent_id,
                    "content": comment.content,
                },
            }
        ),
        201,
    )


@comment_bp.route("/comment/parent/<int:parent_id>/reply", methods=["POST"])
@login_required
def reply_to_comment(parent_id):
    """Responder a un comentario (crear comentario hijo).

    Acepta JSON {"content": "..."} o formulario con campo `content`.
    Asigna `dataset_id` automáticamente desde el comentario padre.
    """
    parent = comment_service.get_by_id(parent_id)
    if not parent:
        return jsonify({"message": "Parent comment not found"}), 404

    # Do not allow replying to a hidden parent comment
    if not getattr(parent, "visible", True):
        return jsonify({"message": "Cannot reply to a hidden comment"}), 403

    # Get content
    content = None
    if request.is_json:
        data = request.get_json() or {}
        content = data.get("content")

    if content is None:
        form = CommentForm()
        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400
        content = form.content.data

    if not content or not content.strip():
        return jsonify({"message": "Content is required"}), 400

    try:
        comment = comment_service.create(
            user_id=current_user.id,
            dataset_id=parent.dataset_id,
            parent_id=parent_id,
            content=content.strip(),
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return (
        jsonify(
            {
                "success": True,
                "comment": {
                    "id": comment.id,
                    "user_id": comment.user_id,
                    "dataset_id": comment.dataset_id,
                    "parent_id": comment.parent_id,
                    "content": comment.content,
                },
            }
        ),
        201,
    )
