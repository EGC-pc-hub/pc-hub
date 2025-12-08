import random

from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing

PARENT_ID = 1
DATASET_ID = 1


class CommentBehavior(TaskSet):
    @task(1)
    def get_replies_by_dataset(self):
        # catch_response is used to make locust able to mark requests as success despite being 4xx
        with self.client.get(f"/comment/parent/{PARENT_ID}", name="comment:by_dataset", catch_response=True) as resp:
            # Acceptable responses are 200 (OK), 403 (hidden parent comment), and 404 (parent comment not found)
            if resp.status_code in (200, 403, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(2)
    def post_comment_to_dataset(self):
        url = f"/comment/dataset/{DATASET_ID}/create"
        content = "".join(random.choices("abcdefghijklmnopqrstuvwxyz ", k=50))

        response = self.client.post(url, json={"content": content})
        # 200 given by login redirect , the post sends a 302 due to not being logged in
        assert response.status_code == 200


class CommentUser(HttpUser):
    tasks = [CommentBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
