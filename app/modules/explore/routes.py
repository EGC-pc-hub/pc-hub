from flask import jsonify, render_template, request

from app.modules.explore import explore_bp
from app.modules.explore.forms import ExploreForm
from app.modules.explore.services import ExploreService

@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    form = ExploreForm()
    service = ExploreService()

    if request.method == "POST":
        # Handle both regular and advanced search via AJAX
        data = request.get_json()

        if data:
            # Extract search parameters
            query = data.get("query", "")
            sorting = data.get("sorting", "newest")
            publication_type = data.get("publication_type", "any")
            tags = data.get("tags", [])

            # Check if it's an advanced search
            is_advanced = any(
                [
                    data.get("authors_filter") and data.get("authors_filter").strip(),
                    data.get("tags_filter") and data.get("tags_filter").strip(),
                    data.get("publication_types_advanced") and len(data.get("publication_types_advanced", [])) > 0,
                    data.get("date_from") and data.get("date_from").strip(),
                    data.get("date_to") and data.get("date_to").strip(),
                ]
            )

            # Force advanced search if we have authors_filter
            if data.get("authors_filter") and data.get("authors_filter").strip():
                is_advanced = True

            if is_advanced:
                # Advanced search
                from datetime import datetime

                # Parse dates if provided
                date_from = None
                date_to = None

                if data.get("date_from") and not data.get("any_date", False):
                    try:
                        date_from = datetime.strptime(data["date_from"], "%Y-%m-%d").date()
                    except ValueError:
                        pass

                if data.get("date_to") and not data.get("any_date", False):
                    try:
                        date_to = datetime.strptime(data["date_to"], "%Y-%m-%d").date()
                    except ValueError:
                        pass

                search_params = {
                    "query": query,
                    "authors": data.get("authors_filter", ""),
                    "tags": data.get("tags_filter", ""),
                    "publication_types": data.get("publication_types_advanced", []),
                    "date_from": date_from,
                    "date_to": date_to,
                    "sort_by": f"created_at_desc" if sorting == "newest" else f"created_at_asc",
                }
                datasets = service.advanced_search(**search_params)
            else:
                # Regular search
                datasets = service.filter(query, sorting, publication_type, tags)

            # Convert datasets to JSON format using to_dict method
            datasets_data = []
            for dataset in datasets:
                try:
                    # Use the model's to_dict() method which has the correct URL logic
                    dataset_dict = dataset.to_dict()
                    datasets_data.append(dataset_dict)
                except Exception as e:
                    print(f"ERROR processing dataset {dataset.id}: {e}")
                    # Add minimal data to avoid breaking the response
                    datasets_data.append(
                        {
                            "id": dataset.id,
                            "title": f"Dataset {dataset.id}",
                            "description": "Error loading data",
                            "url": (
                                dataset.get_uvlhub_doi()
                                if hasattr(dataset, "get_uvlhub_doi")
                                else f"/dataset/{dataset.id}"
                            ),
                            "created_at": "",
                            "publication_type": "Unknown",
                            "authors": [],
                            "tags": [],
                            "download_count": 0,
                            "total_size_in_human_format": "0 B",
                        }
                    )

            return jsonify(datasets_data)

    # GET request - render the template
    query = request.args.get("query", "")
    sorting = request.args.get("sorting", "newest")
    publication_type = request.args.get("publication_type", "any")
    tags = request.args.getlist("tags")

    return render_template(
        "explore/index.html", form=form, query=query, sorting=sorting, publication_type=publication_type, tags=tags
    )

# API ENDPOINTS PARA BÚSQUEDA AVANZADA
@explore_bp.route("/api/authors")
def get_author_suggestions():
    """API endpoint para autocompletar autores"""
    try:
        term = request.args.get("term", "").strip()
        if len(term) < 2:
            return jsonify([])

        service = ExploreService()
        authors = service.get_author_suggestions(term)

        return jsonify(
            [
                {
                    "id": author.id,
                    "name": author.name,
                    "orcid": author.orcid or "",
                    "affiliation": author.affiliation or "",
                }
                for author in authors
            ]
        )

    except Exception as e:
        print(f"Error in get_author_suggestions: {e}")
        return jsonify([]), 500

@explore_bp.route("/api/tags")
def get_available_tags():
    """API endpoint para obtener tags disponibles"""
    try:
        service = ExploreService()
        tags = service.get_available_tags()
        return jsonify(tags)

    except Exception as e:
        print(f"Error in get_available_tags: {e}")
        return jsonify([]), 500

@explore_bp.route("/api/publication-stats")
def get_publication_stats():
    """API endpoint para estadísticas de tipos de publicación"""
    try:
        service = ExploreService()
        stats = service.get_publication_type_stats()
        return jsonify(stats)

    except Exception as e:
        print(f"Error in get_publication_stats: {e}")
        return jsonify({}), 500
