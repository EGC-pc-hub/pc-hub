import json
import logging

from flask import jsonify

from app.modules.flamapy import flamapy_bp
from app.modules.hubfile.services import HubfileService

logger = logging.getLogger(__name__)


@flamapy_bp.route("/flamapy/check_json/<int:file_id>", methods=["GET"])
def check_json(file_id):
    try:
        hubfile = HubfileService().get_by_id(file_id)

        # Try to load and validate JSON format
        with open(hubfile.get_path(), "r") as f:
            json.load(f)

        # If JSON is successfully parsed, it's valid
        return jsonify({"message": "Valid Model"}), 200

    except json.JSONDecodeError as e:
        return jsonify({"errors": [f"Invalid JSON format: {str(e)}"]}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flamapy_bp.route("/flamapy/valid/<int:file_id>", methods=["GET"])
def valid(file_id):
    return jsonify({"success": True, "file_id": file_id})


@flamapy_bp.route("/flamapy/to_glencoe/<int:file_id>", methods=["GET"])
def to_glencoe(file_id):
    # Placeholder: Implement conversion from JSON to Glencoe format if needed
    return jsonify({"error": "Conversion not yet implemented for JSON format"}), 501


@flamapy_bp.route("/flamapy/to_splot/<int:file_id>", methods=["GET"])
def to_splot(file_id):
    # Placeholder: Implement conversion from JSON to SPLOT format if needed
    return jsonify({"error": "Conversion not yet implemented for JSON format"}), 501


@flamapy_bp.route("/flamapy/to_cnf/<int:file_id>", methods=["GET"])
def to_cnf(file_id):
    # Placeholder: Implement conversion from JSON to CNF format if needed
    return jsonify({"error": "Conversion not yet implemented for JSON format"}), 501
