from fastapi.testclient import TestClient
from app.main import app
from app.utils.auth_helper import get_current_user
import json

# Setup dependency override to simulate logged-in user_id=3 (cross-department mentor)
def mock_get_current_user():
    return {
        "token": "test_token",
        "username": "test_mentor_3",
        "first_name": "Rakesh",
        "last_name": "Patil",
        "user_id": 3,
        "org_id": 1,
        "user_type": "U"
    }

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

print("--- Testing /api/v1/mentor-list/curriculums ---")
response = client.get("/api/v1/mentor-list/curriculums?dept_id=1&pgm_id=1")
print("STATUS CODE:", response.status_code)
print("RESPONSE DATA:")
print(json.dumps(response.json(), indent=2))

print("\n--- Testing /api/v1/mentor-mentee-details/curriculums ---")
response = client.get("/api/v1/mentor-mentee-details/curriculums?dept_id=1&pgm_id=1")
print("STATUS CODE:", response.status_code)
print("RESPONSE DATA:")
print(json.dumps(response.json(), indent=2))

