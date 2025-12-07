import pytest
from datetime import datetime, timedelta

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, DSMetrics, Author, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData, FMMetrics


@pytest.fixture(scope="function")
def test_datasets(test_client):
    """Create multiple test datasets with different attributes for advanced search testing"""
    
    # Get or create test user
    user = User.query.filter_by(email="test@example.com").first()
    if not user:
        user = User(email="test@example.com", password="test1234")
        db.session.add(user)
        db.session.commit()

    datasets = []
    
    # Dataset 1: Software, with specific author and tags
    ds_metrics_1 = DSMetrics(number_of_models="5", number_of_features="20")
    db.session.add(ds_metrics_1)
    db.session.flush()
    
    ds_meta_1 = DSMetaData(
        title="Machine Learning Framework",
        description="A comprehensive ML framework for data science",
        publication_type=PublicationType.SOFTWARE,
        publication_doi="10.1234/ml-framework",
        dataset_doi="10.1234/dataset-ml",
        tags="machine learning, AI, python",
        ds_metrics_id=ds_metrics_1.id
    )
    db.session.add(ds_meta_1)
    db.session.flush()
    
    author_1 = Author(name="John Smith", affiliation="MIT", orcid="0000-0001-1234-5678", ds_meta_data_id=ds_meta_1.id)
    db.session.add(author_1)
    
    dataset_1 = DataSet(user_id=user.id, ds_meta_data_id=ds_meta_1.id, created_at=datetime.now() - timedelta(days=10))
    db.session.add(dataset_1)
    db.session.flush()
    
    # Add feature model to dataset 1
    fm_metrics_1 = FMMetrics(solver="PySAT", not_solver=None)
    db.session.add(fm_metrics_1)
    db.session.flush()
    
    fm_meta_1 = FMMetaData(
        uvl_filename="model1.uvl",
        title="ML Model Config",
        description="Configuration model",
        publication_type=PublicationType.SOFTWARE,
        publication_doi="10.1234/ml-framework",
        tags="config",
        fm_metrics_id=fm_metrics_1.id
    )
    db.session.add(fm_meta_1)
    db.session.flush()
    
    fm_1 = FeatureModel(data_set_id=dataset_1.id, fm_meta_data_id=fm_meta_1.id)
    db.session.add(fm_1)
    datasets.append(dataset_1)
    
    # Dataset 2: Hardware, different author and tags, older date
    ds_metrics_2 = DSMetrics(number_of_models="3", number_of_features="15")
    db.session.add(ds_metrics_2)
    db.session.flush()
    
    ds_meta_2 = DSMetaData(
        title="IoT Sensor Network",
        description="Hardware specifications for IoT sensors",
        publication_type=PublicationType.HARDWARE,
        publication_doi="10.1234/iot-sensors",
        dataset_doi="10.1234/dataset-iot",
        tags="IoT, sensors, hardware",
        ds_metrics_id=ds_metrics_2.id
    )
    db.session.add(ds_meta_2)
    db.session.flush()
    
    author_2 = Author(name="Jane Doe", affiliation="Stanford", orcid="0000-0002-2345-6789", ds_meta_data_id=ds_meta_2.id)
    db.session.add(author_2)
    
    dataset_2 = DataSet(user_id=user.id, ds_meta_data_id=ds_meta_2.id, created_at=datetime.now() - timedelta(days=30))
    db.session.add(dataset_2)
    db.session.flush()
    
    # Add feature model to dataset 2
    fm_metrics_2 = FMMetrics(solver="PySAT", not_solver=None)
    db.session.add(fm_metrics_2)
    db.session.flush()
    
    fm_meta_2 = FMMetaData(
        uvl_filename="sensor_model.uvl",
        title="Sensor Configuration",
        description="Sensor network model",
        publication_type=PublicationType.HARDWARE,
        publication_doi="10.1234/iot-sensors",
        tags="network",
        fm_metrics_id=fm_metrics_2.id
    )
    db.session.add(fm_meta_2)
    db.session.flush()
    
    fm_2 = FeatureModel(data_set_id=dataset_2.id, fm_meta_data_id=fm_meta_2.id)
    db.session.add(fm_2)
    datasets.append(dataset_2)
    
    # Dataset 3: Software, shared author with dataset 1
    ds_metrics_3 = DSMetrics(number_of_models="8", number_of_features="30")
    db.session.add(ds_metrics_3)
    db.session.flush()
    
    ds_meta_3 = DSMetaData(
        title="Web Development Framework",
        description="Modern web framework for building applications",
        publication_type=PublicationType.SOFTWARE,
        publication_doi="10.1234/web-framework",
        dataset_doi="10.1234/dataset-web",
        tags="web, javascript, framework",
        ds_metrics_id=ds_metrics_3.id
    )
    db.session.add(ds_meta_3)
    db.session.flush()
    
    author_3 = Author(name="John Smith", affiliation="MIT", orcid="0000-0001-1234-5678", ds_meta_data_id=ds_meta_3.id)
    db.session.add(author_3)
    
    dataset_3 = DataSet(user_id=user.id, ds_meta_data_id=ds_meta_3.id, created_at=datetime.now() - timedelta(days=5))
    db.session.add(dataset_3)
    db.session.flush()
    
    # Add feature model to dataset 3
    fm_metrics_3 = FMMetrics(solver="PySAT", not_solver=None)
    db.session.add(fm_metrics_3)
    db.session.flush()
    
    fm_meta_3 = FMMetaData(
        uvl_filename="web_model.uvl",
        title="Web App Model",
        description="Web application configuration",
        publication_type=PublicationType.SOFTWARE,
        publication_doi="10.1234/web-framework",
        tags="config",
        fm_metrics_id=fm_metrics_3.id
    )
    db.session.add(fm_meta_3)
    db.session.flush()
    
    fm_3 = FeatureModel(data_set_id=dataset_3.id, fm_meta_data_id=fm_meta_3.id)
    db.session.add(fm_3)
    datasets.append(dataset_3)
        
    db.session.commit()
    
    yield datasets
    
    # Cleanup - cascade deletes will handle related records
    try:
        for dataset in datasets:
            # Refresh to ensure we have the latest state
            db.session.refresh(dataset)
            
            # Get related objects before deletion
            ds_meta_data = dataset.ds_meta_data
            ds_metrics = ds_meta_data.ds_metrics if ds_meta_data else None
            
            # Delete the dataset - this will cascade to feature models
            db.session.delete(dataset)
            
            # Delete metadata and metrics if they exist
            if ds_meta_data:
                db.session.delete(ds_meta_data)
            if ds_metrics:
                db.session.delete(ds_metrics)
                
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Cleanup error: {e}")


class TestAdvancedSearchFilters:
    """Test suite for advanced search functionality"""
    
    def test_filter_by_title(self, test_client, test_datasets):
        """Test filtering datasets by title"""
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "Machine Learning",
                "filter_author": "",
                "filter_tags": "",
                "filter_publication_type": "any",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["title"] == "Machine Learning Framework"
    
    def test_filter_by_author(self, test_client, test_datasets):
        """Test filtering datasets by author name"""
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "",
                "filter_author": "John Smith",
                "filter_tags": "",
                "filter_publication_type": "any",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        authors = [author["name"] for dataset in data for author in dataset["authors"]]
        assert "John Smith" in authors
    
    def test_filter_by_tags(self, test_client, test_datasets):
        """Test filtering datasets by tags"""
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "",
                "filter_author": "",
                "filter_tags": "IoT",
                "filter_publication_type": "any",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert "IoT" in data[0]["tags"]
    
    def test_filter_by_publication_type(self, test_client, test_datasets):
        """Test filtering datasets by publication type"""
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "",
                "filter_author": "",
                "filter_tags": "",
                "filter_publication_type": "hardware",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert "Hardware" in data[0]["publication_type"]
    
    def test_filter_by_date_range(self, test_client, test_datasets):
        """Test filtering datasets by date range"""
        date_from = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")
        
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "",
                "filter_author": "",
                "filter_tags": "",
                "filter_publication_type": "any",
                "filter_date_from": date_from,
                "filter_date_to": date_to
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        # Should return datasets 1 and 3 (created 10 and 5 days ago)
        assert len(data) == 2
    
    def test_filter_by_date_from_only(self, test_client, test_datasets):
        """Test filtering datasets with only date_from"""
        date_from = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "",
                "filter_author": "",
                "filter_tags": "",
                "filter_publication_type": "any",
                "filter_date_from": date_from,
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        # Should return datasets 1 and 3
        assert len(data) == 2
    
    def test_combined_filters(self, test_client, test_datasets):
        """Test combining multiple advanced filters"""
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "",
                "filter_author": "John Smith",
                "filter_tags": "",
                "filter_publication_type": "software",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        for dataset in data:
            assert "Software" in dataset["publication_type"]
            authors = [author["name"] for author in dataset["authors"]]
            assert "John Smith" in authors
    
    def test_advanced_search_with_sorting_newest(self, test_client, test_datasets):
        """Test advanced search respects sorting order (newest first)"""
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "",
                "filter_author": "John Smith",
                "filter_tags": "",
                "filter_publication_type": "any",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        # First should be "Web Development Framework" (5 days ago)
        assert data[0]["title"] == "Web Development Framework"
    
    def test_advanced_search_with_sorting_oldest(self, test_client, test_datasets):
        """Test advanced search respects sorting order (oldest first)"""
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "oldest",
                "filter_title": "",
                "filter_author": "John Smith",
                "filter_tags": "",
                "filter_publication_type": "any",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        # First should be "Machine Learning Framework" (10 days ago)
        assert data[0]["title"] == "Machine Learning Framework"
    
    def test_regular_search_still_works(self, test_client, test_datasets):
        """Test that regular search (without advanced filters) still works"""
        response = test_client.post(
            "/explore",
            json={
                "query": "framework",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "",
                "filter_author": "",
                "filter_tags": "",
                "filter_publication_type": "any",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2  # Should find both "Machine Learning Framework" and "Web Development Framework"
    
    def test_no_results_advanced_search(self, test_client, test_datasets):
        """Test advanced search with filters that match no datasets"""
        response = test_client.post(
            "/explore",
            json={
                "query": "",
                "publication_type": "any",
                "sorting": "newest",
                "filter_title": "Nonexistent Dataset",
                "filter_author": "",
                "filter_tags": "",
                "filter_publication_type": "any",
                "filter_date_from": "",
                "filter_date_to": ""
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 0


class TestExplorePageRendering:
    """Test suite for explore page rendering"""
    
    def test_explore_page_loads(self, test_client):
        """Test that explore page loads successfully"""
        response = test_client.get("/explore")
        assert response.status_code == 200
        assert b"Explore" in response.data
    
    def test_advanced_search_button_exists(self, test_client):
        """Test that advanced search button is present"""
        response = test_client.get("/explore")
        assert response.status_code == 200
        assert b"Advanced Search" in response.data
    
    def test_advanced_search_fields_exist(self, test_client):
        """Test that all advanced search fields are present"""
        response = test_client.get("/explore")
        assert response.status_code == 200
        assert b"filter_title" in response.data
        assert b"filter_author" in response.data
        assert b"filter_tags" in response.data
        assert b"filter_publication_type" in response.data
        assert b"filter_date_from" in response.data
        assert b"filter_date_to" in response.data
