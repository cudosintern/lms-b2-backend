from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

# Test fetching departments
response = client.get("/api/v1/mentor-list/departments")
print("DEPARTMENTS:", response.status_code)
print(json.dumps(response.json(), indent=2))

# Test fetching programs for dept_id=71 (Computer Science)
response = client.get("/api/v1/mentor-list/programs?dept_id=71")
print("\nPROGRAMS for dept 71:", response.status_code)
print(json.dumps(response.json(), indent=2))

# Test fetching programs for dept_id=73 (Electronics Engineering)
response = client.get("/api/v1/mentor-list/programs?dept_id=73")
print("\nPROGRAMS for dept 73:", response.status_code)
print(json.dumps(response.json(), indent=2))

# Test fetching curriculums for dept_id=1, pgm_id=1
response = client.get("/api/v1/mentor-list/curriculums?dept_id=1&pgm_id=1")
print("\nCURRICULUMS for dept 1, pgm 1:", response.status_code)
print(json.dumps(response.json(), indent=2))

# Test fetching curriculums for dept_id=73, pgm_id=16
response = client.get("/api/v1/mentor-list/curriculums?dept_id=73&pgm_id=16")
print("\nCURRICULUMS for dept 73, pgm 16:", response.status_code)
print(json.dumps(response.json(), indent=2))
