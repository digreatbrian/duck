from locust import HttpUser, task, between
import random

class DuckFrameworkUser(HttpUser):
    # Wait time between task executions (in seconds)
    wait_time = between(1, 3)

    @task(1)
    def load_homepage(self):
        # Simple GET request to the homepage
        self.client.get("/")

    @task(2)
    def load_api(self):
        # Simulate a request to a specific API endpoint
        self.client.get("/api/some_endpoint")

    @task(3)
    def test_large_payload(self):
        # Simulate a request that might return a large payload
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "key": "value" * 1000  # Large request payload for testing
        }
        self.client.post("/api/large_payload", json=data, headers=headers)

    @task(4)
    def simulate_post_request(self):
        # Simulate a POST request with a form submission or JSON data
        payload = {
            "username": "testuser",
            "password": "password123"
        }
        self.client.post("/api/login", json=payload)

    @task(5)
    def simulate_404(self):
        # Simulate a request to a non-existent endpoint to test 404 responses
        self.client.get("/nonexistentendpoint", name="404 Response")

    def on_start(self):
        # This method will run before any task is executed, useful for setting up a user
        print("User started")
        self.client.get("/")  # You can simulate an initial GET request or login