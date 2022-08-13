from locust import HttpUser, task
from random import randint
import os
import json


class TrackLocationLoadTest(HttpUser):
    @task
    def track_location(self):
        api_keys = json.loads(os.getenv("UBER_SERVER_API_KEYS", []))
        if not api_keys:
            raise ValueError("No API KEYS provided")

        for key in api_keys[:2]:
            self.client.get(
                f"/v1/VIP/{randint(-1, 35)}", headers={"Authorization": f"Bearer {key}"}
            )
