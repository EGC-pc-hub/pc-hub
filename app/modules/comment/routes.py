from flask import render_template

from app.modules.comment import comment_bp


@comment_bp.route("/comment", methods=["GET"])
def index():
    return render_template("comment/index.html")
