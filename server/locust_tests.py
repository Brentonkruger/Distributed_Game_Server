from locust import HttpLocust, TaskSet, task

class SimpleLocustTest(TaskSet):

    @task
    def get_something(self):
        self.client.get("/GetReplicaList")

class LocustTests(HttpLocust):
    task_set = SimpleLocustTest