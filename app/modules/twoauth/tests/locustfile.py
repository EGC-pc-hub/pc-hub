from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token


class TwoAuthBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login_2fa_flow()

    @task
    def ensure_logged_out(self):
        self.client.get("/logout", name="logout")

    @task
    def login_2fa_flow(self):
        resp = self.client.get("/login", name="login:get")
        try:
            csrf_token = get_csrf_token(resp)
        except Exception:
            self.ensure_logged_out()
            resp = self.client.get("/login", name="login:get")
            try:
                csrf_token = get_csrf_token(resp)
            except Exception:
                return

        self.client.post(
            "/login",
            data={
                "email": "user1@example.com",
                "password": "1234",
                "csrf_token": csrf_token,
            },
            name="login:post",
        )

        self.client.get("/2auth", name="twoauth:verify:get")

    @task
    def signup_2fa_flow(self):
        resp = self.client.get("/signup", name="signup:get")
        try:
            csrf_token = get_csrf_token(resp)
        except Exception:
            return

        self.client.post(
            "/signup",
            data={
                "email": fake.email(),
                "password": fake.password(),
                "csrf_token": csrf_token,
            },
            name="signup:post",
        )

        self.client.get("/2auth", name="twoauth:verify:get")

    @task
    def resend_code(self):
        self.client.get("/2auth/resend", name="twoauth:resend:get")


class TwoAuthUser(HttpUser):
    tasks = [TwoAuthBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
