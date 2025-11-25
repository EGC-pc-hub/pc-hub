import random

from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing

DATASET_ID = 1


class CommentBehavior(TaskSet):

    # Get comments for a dataset
    @task(1)
    def get_comments_by_dataset(self):
        url = f"/comment/dataset/{DATASET_ID}"
        response = self.client.get(url)
        if response.status_code != 200:
            print(f"GET {url} failed: {response.status_code}")

    # Post a comment to a dataset
    @task(2)
    def post_comment_to_dataset(self):
        url = f"/comment/dataset/{DATASET_ID}/create"
        content = "".join(random.choices("abcdefghijklmnopqrstuvwxyz ", k=50))

        response = self.client.post(url, json={"content": content})
        if response.status_code != 201:
            print(f"POST {url} failed: {response.status_code}, {response.text}")


class CommentUser(HttpUser):
    tasks = [CommentBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
