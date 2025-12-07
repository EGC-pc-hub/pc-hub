from locust import HttpUser, task
from datetime import datetime, timedelta
import random

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token


class ExploreUser(HttpUser):
    """Simulate users exploring and searching datasets with advanced filters"""
    
    host = get_host_for_locust_testing()
    wait_time = lambda self: random.uniform(2, 5)
    
    @task(3)
    def basic_search(self):
        """Perform a basic search query"""
        response = self.client.get("/explore")
        csrf_token = get_csrf_token(response)
        
        search_data = {
            "csrf_token": csrf_token,
            "query": fake.word(),
            "publication_type": "any",
            "sorting": "newest",
            "filter_title": "",
            "filter_author": "",
            "filter_tags": "",
            "filter_publication_type": "any",
            "filter_date_from": "",
            "filter_date_to": ""
        }
        
        response = self.client.post("/explore", json=search_data, name="/explore [basic search]")
        if response.status_code != 200:
            print(f"Basic search failed: {response.status_code}")
    
    @task(2)
    def search_by_title(self):
        """Search datasets by title"""
        response = self.client.get("/explore")
        csrf_token = get_csrf_token(response)
        
        search_data = {
            "csrf_token": csrf_token,
            "query": "",
            "publication_type": "any",
            "sorting": "newest",
            "filter_title": fake.word(),
            "filter_author": "",
            "filter_tags": "",
            "filter_publication_type": "any",
            "filter_date_from": "",
            "filter_date_to": ""
        }
        
        response = self.client.post("/explore", json=search_data, name="/explore [filter by title]")
        if response.status_code != 200:
            print(f"Title search failed: {response.status_code}")
    
    @task(2)
    def search_by_author(self):
        """Search datasets by author"""
        response = self.client.get("/explore")
        csrf_token = get_csrf_token(response)
        
        search_data = {
            "csrf_token": csrf_token,
            "query": "",
            "publication_type": "any",
            "sorting": "newest",
            "filter_title": "",
            "filter_author": fake.name(),
            "filter_tags": "",
            "filter_publication_type": "any",
            "filter_date_from": "",
            "filter_date_to": ""
        }
        
        response = self.client.post("/explore", json=search_data, name="/explore [filter by author]")
        if response.status_code != 200:
            print(f"Author search failed: {response.status_code}")
    
    @task(2)
    def search_by_tags(self):
        """Search datasets by tags"""
        response = self.client.get("/explore")
        csrf_token = get_csrf_token(response)
        
        search_data = {
            "csrf_token": csrf_token,
            "query": "",
            "publication_type": "any",
            "sorting": "newest",
            "filter_title": "",
            "filter_author": "",
            "filter_tags": fake.word(),
            "filter_publication_type": "any",
            "filter_date_from": "",
            "filter_date_to": ""
        }
        
        response = self.client.post("/explore", json=search_data, name="/explore [filter by tags]")
        if response.status_code != 200:
            print(f"Tags search failed: {response.status_code}")
    
    @task(1)
    def search_by_publication_type(self):
        """Search datasets by publication type"""
        response = self.client.get("/explore")
        csrf_token = get_csrf_token(response)
        
        pub_types = ["software", "hardware", "other", "none"]
        
        search_data = {
            "csrf_token": csrf_token,
            "query": "",
            "publication_type": "any",
            "sorting": "newest",
            "filter_title": "",
            "filter_author": "",
            "filter_tags": "",
            "filter_publication_type": random.choice(pub_types),
            "filter_date_from": "",
            "filter_date_to": ""
        }
        
        response = self.client.post("/explore", json=search_data, name="/explore [filter by publication type]")
        if response.status_code != 200:
            print(f"Publication type search failed: {response.status_code}")
    
    @task(1)
    def search_by_date_range(self):
        """Search datasets by date range"""
        response = self.client.get("/explore")
        csrf_token = get_csrf_token(response)
        
        date_from = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")
        
        search_data = {
            "csrf_token": csrf_token,
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
        
        response = self.client.post("/explore", json=search_data, name="/explore [filter by date range]")
        if response.status_code != 200:
            print(f"Date range search failed: {response.status_code}")
    
    @task(2)
    def combined_advanced_search(self):
        """Search with multiple advanced filters"""
        response = self.client.get("/explore")
        csrf_token = get_csrf_token(response)
        
        pub_types = ["software", "hardware", "other", "any"]
        
        search_data = {
            "csrf_token": csrf_token,
            "query": "",
            "publication_type": "any",
            "sorting": random.choice(["newest", "oldest"]),
            "filter_title": fake.word() if random.random() > 0.5 else "",
            "filter_author": fake.name() if random.random() > 0.5 else "",
            "filter_tags": fake.word() if random.random() > 0.5 else "",
            "filter_publication_type": random.choice(pub_types),
            "filter_date_from": "",
            "filter_date_to": ""
        }
        
        response = self.client.post("/explore", json=search_data, name="/explore [combined filters]")
        if response.status_code != 200:
            print(f"Combined search failed: {response.status_code}")
