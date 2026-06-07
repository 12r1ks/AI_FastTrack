import uuid
import random
from locust import HttpUser, task, between

QUESTIONS = [
    "What are the parking rates?",
    "Where are your parking locations?",
    "Do you have availability in central tomorrow at 9am?",
    "What types of parking spots are there?",
    "How much is parking for 3 hours?",
]


class ChatUser(HttpUser):
    """Simulates a user chatting with the assistant."""
    wait_time = between(1, 4)

    def on_start(self):
        # each virtual user is its own conversation (its own thread_id)
        self.session_id = str(uuid.uuid4())

    @task(3)
    def chat(self):
        self.client.post(
            "/chat",
            json={"session_id": self.session_id, "message": random.choice(QUESTIONS)},
            name="POST /chat",
        )

    @task(1)
    def poll(self):
        self.client.get(
            f"/chat/poll?session_id={self.session_id}",
            name="GET /chat/poll",
        )


class AdminUser(HttpUser):
    """Simulates an admin watching the pending-approval queue."""
    wait_time = between(2, 5)

    @task
    def pending(self):
        self.client.get("/admin/pending", name="GET /admin/pending")
