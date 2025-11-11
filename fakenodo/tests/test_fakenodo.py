import io

import pytest

from fakenodo import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_create_and_publish_versions(client):
    # Create deposition
    resp = client.post(
        "/api/deposit/depositions",
        json={
            "metadata": {
                "title": "My dataset",
                "upload_type": "dataset",
                "description": "desc",
                "creators": [{"name": "Alice"}],
            }
        },
    )
    assert resp.status_code == 201
    dep = resp.get_json()
    dep_id = dep["id"]
    assert dep["doi"] is None

    # First publish (no files yet) -> generates DOI v1
    resp = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    assert resp.status_code == 202
    dep = resp.get_json()
    doi_v1 = dep["doi"]
    assert ".v1" in doi_v1

    # Update only metadata
    resp = client.put(
        f"/api/deposit/depositions/{dep_id}",
        json={"metadata": {"title": "My dataset v2", "upload_type": "dataset"}},
    )
    assert resp.status_code == 200

    # Publish again without file changes -> same DOI
    resp = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    assert resp.status_code == 202
    dep = resp.get_json()
    assert dep["doi"] == doi_v1

    # Upload a file using in-memory BytesIO
    resp = client.post(
        f"/api/deposit/depositions/{dep_id}/files",
        data={
            "name": "test.txt",
            "file": (io.BytesIO(b"hello"), "test.txt"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201

    # Publish after file change -> new DOI v2
    resp = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    assert resp.status_code == 202
    dep = resp.get_json()
    doi_v2 = dep["doi"]
    assert doi_v2 != doi_v1
    assert ".v2" in doi_v2

    # List versions by concept rec id
    concept_id = dep["conceptrecid"]
    resp = client.get(f"/api/records/{concept_id}/versions")
    assert resp.status_code == 200
    versions = resp.get_json()["hits"]["hits"]
    assert len(versions) == 2
    assert any(v["doi"] == doi_v1 for v in versions)
    assert any(v["doi"] == doi_v2 for v in versions)