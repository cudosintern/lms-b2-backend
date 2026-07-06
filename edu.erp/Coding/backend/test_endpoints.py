from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

response = client.get("/api/v1/mentor-list/terms?curriculum_id=10")
print("TERMS RESPONSE:", response.status_code, response.json() if response.status_code == 200 else response.text)

response = client.get("/api/v1/mentor-list/list?curriculum_id=10")
print("LIST RESPONSE (No Term):", response.status_code, response.json() if response.status_code == 200 else response.text)

response = client.get("/api/v1/mentor-list/list?curriculum_id=10&term_id=1")
print("LIST RESPONSE (With Term):", response.status_code, response.json() if response.status_code == 200 else response.text)
