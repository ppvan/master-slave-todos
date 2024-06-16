from locust import task, FastHttpUser

class HelloWorldUser(FastHttpUser):
    @task(6)
    def read_todos(self):
        self.client.get("/todos/")

    @task(4)
    def create_todos(self):
        payload = {
            "name": "Test 123",
            "description": "Description 22882",
        }

        res = self.client.post("/todos/", json=payload)
        todo = res.json()
        id = todo["id"]


        self.client.get(f"/todos/{id}")