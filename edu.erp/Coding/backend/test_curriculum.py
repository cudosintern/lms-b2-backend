from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

response = client.get("/api/v1/curriculum/list")
print("STATUS:", response.status_code)
if response.status_code == 200:
    data = response.json()
    print("DATA:")
    print(json.dumps(data, indent=2))
else:
    print("ERROR:", response.text)
