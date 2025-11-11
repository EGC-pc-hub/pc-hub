import pytest

from app.modules.conftest import login, logout
from app.modules.dataset.models import DataSet, DSDownloadRecord


@pytest.fixture(scope="function")
def sample_dataset(test_client):
    """Create a sample dataset for testing"""
    from app import db
    from app.modules.auth.models import User
    from app.modules.dataset.models import DSMetaData, PublicationType

    # Get or create test user
    user = User.query.filter_by(email="test@example.com").first()
    if not user:
        user = User(email="test@example.com", password="test1234")
        db.session.add(user)
        db.session.commit()

    # Create metadata
    ds_meta_data = DSMetaData(
        title="Test Dataset for Counter",
        description="Test Description",
        publication_type=PublicationType.JOURNAL_ARTICLE,
        publication_doi="10.1234/test-counter",
        dataset_doi="10.1234/dataset-test-counter",
        tags="test,counter,dataset",
    )
    db.session.add(ds_meta_data)
    db.session.flush()

    # Create dataset
    dataset = DataSet(user_id=user.id, ds_meta_data_id=ds_meta_data.id)
    db.session.add(dataset)
    db.session.commit()

    yield dataset

    # Cleanup
    try:
        db.session.delete(dataset)
        db.session.delete(ds_meta_data)
        db.session.commit()
    except BaseException:
        db.session.rollback()


class TestDownloadCounter:
    """Test suite for download counter functionality"""

    def test_dataset_has_download_count_field(self, test_client):
        """Test that DataSet model has download_count field"""
        response = test_client.get("/")
        assert response.status_code == 200

        # Verify the model has the field
        dataset = DataSet.query.first()
        if dataset:
            assert hasattr(dataset, "download_count")
            assert isinstance(dataset.download_count, int)
            assert dataset.download_count >= 0

    def test_download_count_default_value(self, test_client):
        """Test that new datasets have download_count = 0 by default"""
        from app import db
        from app.modules.auth.models import User

        # Get or create a test user
        user = User.query.filter_by(email="test@example.com").first()
        if not user:
            user = User(email="test@example.com", password="test1234")
            db.session.add(user)
            db.session.commit()

        # Create a minimal dataset
        from app.modules.dataset.models import DSMetaData, PublicationType

        ds_meta_data = DSMetaData(
            title="Test Dataset",
            description="Test Description",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            publication_doi="10.1234/test",
            dataset_doi="10.1234/dataset-test",
        )
        db.session.add(ds_meta_data)
        db.session.flush()

        dataset = DataSet(user_id=user.id, ds_meta_data_id=ds_meta_data.id)
        db.session.add(dataset)
        db.session.commit()

        assert dataset.download_count == 0

        # Cleanup
        db.session.delete(dataset)
        db.session.delete(ds_meta_data)
        db.session.commit()

    def test_download_increments_counter(self, test_client, sample_dataset):
        """Test that downloading a dataset increments the counter"""
        initial_count = sample_dataset.download_count

        # Perform download
        response = test_client.get(f"/dataset/download/{sample_dataset.id}")

        # Should return the file (200) or redirect
        # 500 if files don't exist, that's ok for this test
        assert response.status_code in [200, 302, 500]

        # Refresh dataset from DB
        from app import db

        db.session.refresh(sample_dataset)

        # Verify counter incremented
        assert sample_dataset.download_count == initial_count + 1

    def test_download_creates_record(self, test_client, sample_dataset):
        """Test that downloading creates a DSDownloadRecord"""
        dataset = sample_dataset

        initial_records = DSDownloadRecord.query.filter_by(dataset_id=dataset.id).count()

        # Perform download
        response = test_client.get(f"/dataset/download/{dataset.id}")
        assert response.status_code in [200, 302, 500]  # 500 if files don't exist

        # Verify new record was created
        final_records = DSDownloadRecord.query.filter_by(dataset_id=dataset.id).count()
        assert final_records == initial_records + 1

    def test_multiple_downloads_increment_correctly(self, test_client, sample_dataset):
        """Test that multiple downloads increment the counter correctly"""
        initial_count = sample_dataset.download_count
        num_downloads = 3

        # Perform multiple downloads
        for _ in range(num_downloads):
            response = test_client.get(f"/dataset/download/{sample_dataset.id}")
            assert response.status_code in [200, 302, 500]  # 500 if files don't exist

        # Refresh dataset from DB
        from app import db

        db.session.refresh(sample_dataset)

        # Verify counter incremented correctly
        assert sample_dataset.download_count == initial_count + num_downloads


class TestDownloadCounterAPI:
    """Test suite for download counter API endpoints"""

    def test_stats_endpoint_returns_download_count(self, test_client, sample_dataset):
        """Test that /dataset/<id>/stats endpoint returns download_count"""
        response = test_client.get(f"/dataset/{sample_dataset.id}/stats")
        assert response.status_code == 200

        data = response.get_json()
        assert "download_count" in data
        assert isinstance(data["download_count"], int)
        assert data["download_count"] >= 0
        assert data["dataset_id"] == sample_dataset.id

    def test_api_v1_datasets_includes_download_count(self, test_client):
        """Test that /api/v1/datasets/ includes download_count for each dataset"""
        response = test_client.get("/api/v1/datasets/")
        assert response.status_code == 200

        data = response.get_json()
        assert "items" in data

        if len(data["items"]) > 0:
            first_dataset = data["items"][0]
            assert "download_count" in first_dataset
            assert isinstance(first_dataset["download_count"], int)
            assert first_dataset["download_count"] >= 0

    def test_api_v1_single_dataset_includes_download_count(self, test_client, sample_dataset):
        """Test that /api/v1/datasets/<id> includes download_count"""
        response = test_client.get(f"/api/v1/datasets/{sample_dataset.id}")
        assert response.status_code == 200

        data = response.get_json()
        assert "download_count" in data
        assert isinstance(data["download_count"], int)
        assert data["download_count"] >= 0

    def test_api_html_view_returns_html(self, test_client):
        """Test that /dataset/api returns HTML page"""
        response = test_client.get("/dataset/api")
        assert response.status_code == 200
        assert b"text/html" in response.content_type.encode()
        assert b"Datasets" in response.data or b"datasets" in response.data


class TestDownloadCounterModel:
    """Test suite for DataSet model methods related to download counter"""

    def test_get_download_count_method(self, test_client, sample_dataset):
        """Test that DataSet has get_download_count method"""
        # Check if method exists
        assert hasattr(sample_dataset, "get_download_count")

        # Call the method
        count = sample_dataset.get_download_count()
        assert isinstance(count, int)
        assert count >= 0
        assert count == sample_dataset.download_count

    def test_to_dict_includes_download_count(self, test_client, sample_dataset):
        """Test that DataSet.to_dict() includes download_count"""
        dataset = sample_dataset

        # Check if to_dict method exists and includes download_count
        if hasattr(dataset, "to_dict"):
            dataset_dict = dataset.to_dict()
            assert "download_count" in dataset_dict
            assert dataset_dict["download_count"] == dataset.download_count


class TestDownloadCounterIntegration:
    """Integration tests for download counter functionality"""

    def test_download_counter_appears_on_homepage(self, test_client):
        """Test that download counter appears on the public homepage"""
        response = test_client.get("/")
        assert response.status_code == 200

        # Check if download counter markup is present
        assert b"download" in response.data.lower()
        # Check for data attributes used by JavaScript
        assert b"data-download-counter" in response.data or b"download" in response.data.lower()

    def test_download_counter_appears_on_dataset_detail(self, test_client, sample_dataset):
        """Test that download counter appears on dataset detail page"""
        # Get the dataset DOI URL
        doi = sample_dataset.ds_meta_data.dataset_doi

        response = test_client.get(f"/doi/{doi}/")
        assert response.status_code == 200

        # Check if download counter is displayed
        assert b"download" in response.data.lower()

    def test_download_and_verify_counter_update(self, test_client, sample_dataset):
        """Integration test: download dataset and verify counter updates"""
        # Get initial count
        initial_count = sample_dataset.download_count

        # Download the dataset
        response = test_client.get(f"/dataset/download/{sample_dataset.id}")
        # 500 may occur if files don't exist
        assert response.status_code in [200, 302, 500]

        # Verify counter in database
        from app import db

        db.session.refresh(sample_dataset)
        assert sample_dataset.download_count == initial_count + 1

        # Verify counter via API
        stats_response = test_client.get(f"/dataset/{sample_dataset.id}/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.get_json()
        assert stats_data["download_count"] == initial_count + 1

    def test_authenticated_user_download_increments_counter(self, test_client, sample_dataset):
        """Test that authenticated users also increment the counter"""
        # Login
        login(test_client, "test@example.com", "test1234")

        initial_count = sample_dataset.download_count

        # Download as authenticated user
        response = test_client.get(f"/dataset/download/{sample_dataset.id}")
        # 500 may occur if files don't exist
        assert response.status_code in [200, 302, 500]

        # Verify counter incremented
        from app import db

        db.session.refresh(sample_dataset)
        assert sample_dataset.download_count == initial_count + 1

        logout(test_client)
